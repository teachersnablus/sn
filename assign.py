import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
import time

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام مديرية جنوب نابلس 2026", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] {
        font-size: 19px !important;
        direction: rtl;
        text-align: right;
    }
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { 
        text-align: right; 
        border: 1px solid #ddd; 
        padding: 25px; 
        border-radius: 12px; 
    }
    input, select, textarea { 
        font-size: 19px !important;
        direction: rtl !important; 
        text-align: right !important; 
    }
    .school-title { 
        color: #ffffff; 
        background-color: #1E3A8A; 
        padding: 25px; 
        border-radius: 10px; 
        text-align: center; 
        font-size: 28px !important; 
        font-weight: bold; 
        margin-bottom: 30px; 
    }
    .search-row-label {
        font-size: 22px !important;
        font-weight: bold;
        color: #ffffff; 
        background-color: #1E3A8A; 
        padding: 10px 15px;
        border-radius: 8px;
        white-space: nowrap;
        text-align: center;
    }
    .stButton button { font-size: 19px !important; }
    .stTabs [data-baseweb="tab"] { font-size: 21px !important; }
    </style>
    """, unsafe_allow_html=True)

SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_final_v31.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS main_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, 
              phone TEXT, address TEXT, relative_exam TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT, type TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS correction_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, 
              subject TEXT, branch TEXT, address TEXT, 
              has_relative TEXT, relative_details TEXT, phone TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS system_settings (form_name TEXT PRIMARY KEY, is_open INTEGER)''')
for form in ['ثانوية', 'توظيف', 'تصحيح']:
    c.execute("INSERT OR IGNORE INTO system_settings VALUES (?, 1)", (form,))
conn.commit()

# --- دالة تصدير الإكسل ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        worksheet.right_to_left()
        cell_format = workbook.add_format({'font_size': 14, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 22, cell_format)
    return output.getvalue()

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
if 'auth' not in st.session_state: st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

# --- دالة التحقق من الأرقام ---
def validate_inputs(id_val, phone_val):
    if len(id_val) != 9 or not id_val.isdigit():
        st.error("❌ خطأ: رقم الهوية يجب أن يتكون من 9 أرقام بالضبط.")
        return False
    if len(phone_val) != 10 or not phone_val.isdigit():
        st.error("❌ خطأ: رقم الجوال يجب أن يتكون من 10 أرقام بالضبط.")
        return False
    return True

# --- 3. تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    with tab1:
        u_in = st.text_input("رقم المدرسة").strip()
        p_in = st.text_input("كلمة المرور", type="password").strip()
        if st.button("دخول المدارس"):
            try:
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                match = df_acc[(df_acc['school_user'].astype(str) == u_in) & (df_acc['password'].astype(str) == p_in)]
                if not match.empty:
                    st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u_in, 'school_display_name': str(match.iloc[0]['school_full_name'])})
                    st.rerun()
                else: st.error("❌ بيانات الحساب خاطئة")
            except: st.error("❌ فشل الاتصال")
    with tab2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول المسؤول"):
                st.session_state.update({'auth': True, 'user_type': "admin"})
                st.rerun()
    st.stop()

# --- 4. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    menu = st.sidebar.radio("القائمة الرئيسية:", ["إضافة", "التقارير"])
    st.sidebar.markdown("<br>"*22, unsafe_allow_html=True)
    col_out1, col_out2, col_out3 = st.sidebar.columns([0.5, 2, 0.5])
    with col_out2:
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.clear(); st.rerun()

    if menu == "إضافة":
        col_lbl, col_inp = st.columns([1.2, 3])
        with col_lbl: st.markdown("<div class='search-row-label'>🔍 بحث برقم الهوية</div>", unsafe_allow_html=True)
        with col_inp: search_id = st.text_input("", placeholder="أدخل رقم الهوية...", key=f"search_{st.session_state.reset_key}", label_visibility="collapsed").strip()
        
        found_row, is_main = None, False
        if search_id:
            df_m = pd.read_sql(f"SELECT * FROM main_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
            if not df_m.empty: found_row, is_main = df_m.iloc[0], True; st.success(f"✅ الموظف: {found_row['name']}")
            else:
                df_c = pd.read_sql(f"SELECT * FROM correction_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
                if not df_c.empty: found_row, is_main = df_c.iloc[0], False; st.success(f"✅ كشف التصحيح: {found_row['name']}")
                else: st.info("ℹ️ الرقم متاح للتسجيل.")

        if found_row is not None:
            if st.button("🗑️ حذف السجل"):
                c.execute("DELETE FROM main_table WHERE id_num=?", (search_id,)); c.execute("DELETE FROM correction_table WHERE id_num=?", (search_id,))
                conn.commit(); st.session_state.reset_key += 1; st.success("✅ تم الحذف"); time.sleep(1); st.rerun()

        st.divider()
        t_sec, t_job, t_cor = st.tabs(["📝 الثانوية العامة", "📋 امتحان التوظيف", "✍️ التصحيح"])
        
        # --- شاشة الثانوية العامة ---
        with t_sec:
            if get_form_status('ثانوية'):
                with st.form(key=f"sec_form_{st.session_state.reset_key}"):
                    c1, c2 = st.columns(2)
                    id_num = c2.text_input("رقم الهوية (9 أرقام) *", value=search_id)
                    name = c1.text_input("الاسم رباعي *", value=found_row['name'] if (found_row is not None and is_main and found_row['type']=="الثانوية العامة") else "")
                    phone = c1.text_input("رقم الجوال (10 أرقام) *", value=found_row['phone'] if (found_row is not None and is_main and found_row['type']=="الثانوية العامة") else "")
                    address = st.text_input("مكان السكن *", value=found_row['address'] if (found_row is not None and is_main and found_row['type']=="الثانوية العامة") else "")
                    job_list = ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"]
                    job = c2.selectbox("الوظيفة *", job_list, index=job_list.index(found_row['job_title']) if (found_row is not None and is_main and found_row['job_title'] in job_list) else 0)
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية", value=found_row['school2'] if (found_row is not None and is_main) else "")
                    rel_name = st.text_input("اسم القريب المباشر", value=found_row['relative_exam'] if (found_row is not None and is_main and found_row['type']=="الثانوية العامة") else "")
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], horizontal=True)
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True)
                    if st.form_submit_button("💾 حفظ بيانات الثانوية"):
                        if not (name and id_num and phone and address and job): 
                            st.error("⚠️ يرجى تعبئة جميع الحقول الإجبارية")
                        elif validate_inputs(id_num, phone):
                            c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, address, rel_name, job, desire, note, "الثانوية العامة"))
                            conn.commit(); st.success("✅ تم الحفظ"); st.session_state.reset_key += 1; time.sleep(1); st.rerun()

        # --- شاشة امتحان التوظيف ---
        with t_job:
            if get_form_status('توظيف'):
                with st.form(key=f"job_form_{st.session_state.reset_key}"):
                    c1, c2 = st.columns(2)
                    id_num = c2.text_input("رقم الهوية (9 أرقام) *", value=search_id)
                    name = c1.text_input("الاسم رباعي *", value=found_row['name'] if (found_row is not None and is_main and found_row['type']=="امتحان التوظيف") else "")
                    phone = c1.text_input("رقم الجوال (10 أرقام) *", value=found_row['phone'] if (found_row is not None and is_main and found_row['type']=="امتحان التوظيف") else "")
                    address = st.text_input("مكان السكن *", value=found_row['address'] if (found_row is not None and is_main and found_row['type']=="امتحان التوظيف") else "")
                    job_list = ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"]
                    job = c2.selectbox("الوظيفة *", job_list, index=job_list.index(found_row['job_title']) if (found_row is not None and is_main and found_row['job_title'] in job_list) else 0)
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية", value=found_row['school2'] if (found_row is not None and is_main) else "")
                    rel_exam = st.text_input("امتحان القريب المباشر", value=found_row['relative_exam'] if (found_row is not None and is_main and found_row['type']=="امتحان التوظيف") else "")
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], horizontal=True, key="d_job")
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True, key="n_job")
                    if st.form_submit_button("💾 حفظ بيانات التوظيف"):
                        if not (name and id_num and phone and address and job): 
                            st.error("⚠️ يرجى تعبئة جميع الحقول الإجبارية")
                        elif validate_inputs(id_num, phone):
                            c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, address, rel_exam, job, desire, note, "امتحان التوظيف"))
                            conn.commit(); st.success("✅ تم الحفظ"); st.session_state.reset_key += 1; time.sleep(1); st.rerun()

        # --- شاشة التصحيح ---
        with t_cor:
            if get_form_status('تصحيح'):
                with st.form(key=f"c_form_{st.session_state.reset_key}"):
                    c1, c2 = st.columns(2)
                    c_id = c2.text_input("رقم الهوية (9 أرقام) *", value=search_id)
                    c_name = c1.text_input("الاسم الرباعي *", value=found_row['name'] if (found_row is not None and not is_main) else "")
                    c_phone = c1.text_input("الجوال (10 أرقام) *", value=found_row['phone'] if (found_row is not None and not is_main) else "")
                    c_address = c2.text_input("مكان السكن *", value=found_row['address'] if (found_row is not None and not is_main) else "")
                    branch_list = ["", "علمي", "أدبي", "تجاري", "صناعي", "فندقي", "زراعي", "اقتصاد منزلي"]
                    c_branch = c1.selectbox("الفرع *", branch_list, index=branch_list.index(found_row['branch']) if (found_row is not None and not is_main and found_row['branch'] in branch_list) else 0)
                    
                    sub_list = [
                        "", "اللغة العربية", "اللغة الإنجليزية", "الرياضيات", "التربية الإسلامية", 
                        "الفيزياء", "الكيمياء", "الأحياء", "تكنولوجيا المعلومات", "التاريخ", "الجغرافيا", 
                        "فرع (الريادة و الأعمال) - مباحث التخصص", "فرع (الاقتصاد المنزلي) - مباحث التخصص", 
                        "الثقافة العلمية", "الفروع المهنية (الصناعي ) - مباحث التخصص", "الفروع المهنية (الزراعي) - مباحث التخصص"
                    ]
                    c_subj = c2.selectbox("المبحث *", sub_list, index=sub_list.index(found_row['subject']) if (found_row is not None and not is_main and found_row['subject'] in sub_list) else 0)
                    
                    st.divider()
                    has_rel = st.radio("هل له قريب مباشر يتقدم للامتحان؟", ["لا يوجد", "يوجد"], horizontal=True)
                    rel_details = st.text_input("اسم القريب (إن وجد)", value=found_row['relative_details'] if (found_row is not None and not is_main) else "")
                    st.selectbox("علاقة القرابة", ["", "ابن/ابنة", "أخ/أخت", "زوج/زوجة", "حفيد/حفيدة"]) 
                    if st.form_submit_button("💾 حفظ بيانات التصحيح"):
                        if not (c_name and c_id and c_phone and c_address and c_subj and c_branch): 
                            st.error("⚠️ يرجى اختيار المبحث والفرع وتعبئة الحقول")
                        elif validate_inputs(c_id, c_phone):
                            c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?)", (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subj, c_branch, c_address, has_rel, rel_details, c_phone))
                            conn.commit(); st.success("✅ تم الحفظ"); st.session_state.reset_key += 1; time.sleep(1); st.rerun()

    elif menu == "التقارير":
        st.subheader("📊 سجلات المدرسة الموثقة")
        df1 = pd.read_sql(f"SELECT * FROM main_table WHERE school_user='{st.session_state['school_user']}'", conn)
        df2 = pd.read_sql(f"SELECT * FROM correction_table WHERE school_user='{st.session_state['school_user']}'", conn)
        if not df1.empty: st.info("🔹 كشف المراقبة والتوظيف"); st.dataframe(df1.drop(columns=['school_user','school_full_name']), use_container_width=True)
        if not df2.empty: st.divider(); st.success("🔹 كشف التصحيح"); st.dataframe(df2[['id_num','name','address','branch','subject']], use_container_width=True)

# --- 5. واجهة الإدارة ---
elif st.session_state['user_type'] == "admin":
    adm_menu = st.sidebar.radio("لوحة التحكم:", ["إدارة البيانات", "صلاحيات النماذج"])
    st.sidebar.markdown("<br>"*22, unsafe_allow_html=True)
    with st.sidebar:
        if st.button("🚪 تسجيل الخروج"): st.session_state.clear(); st.rerun()

    st.title("🛠️ لوحة تحكم الإدارة المركزية")
    if adm_menu == "صلاحيات النماذج":
        cols = st.columns(3)
        for i, f in enumerate(['ثانوية', 'توظيف', 'تصحيح']):
            with cols[i]:
                curr = get_form_status(f); st.write(f"نموذج {f}: {'✅ مفتوح' if curr else '❌ مغلق'}")
                if st.button(f"تغيير حالة {f}", key=f"at_{f}"): c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (0 if curr else 1, f)); conn.commit(); st.rerun()
    else:
        t1, t2, t3 = st.tabs(["الثانوية العامة", "امتحان التوظيف", "التصحيح"])
        def view_admin(t_name, d_type, k_s, is_c=False):
            df = pd.read_sql("SELECT * FROM correction_table", conn) if is_c else pd.read_sql(f"SELECT * FROM main_table WHERE type='{d_type}'", conn)
            sel = st.selectbox(f"اختر مدرسة ({t_name}):", ["الكل"] + sorted(df['school_full_name'].unique().tolist()), key=f"s_{k_s}")
            f_df = df if sel == "الكل" else df[df['school_full_name'] == sel]
            st.dataframe(f_df)
            st.download_button(label=f"📥 تحميل ({t_name})", data=to_excel(f_df), file_name=f'admin_{k_s}.xlsx')
        with t1: view_admin("الثانوية العامة", "الثانوية العامة", "tw")
        with t2: view_admin("امتحان التوظيف", "امتحان التوظيف", "em")
        with t3: view_admin("تصحيح", "", "cr", True)

import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
import time

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام مديرية جنوب نابلس 2026", layout="wide")

st.markdown("""
    <style>
    /* تكبير الخط لكل النظام */
    html, body, [class*="st-"] {
        font-size: 18px !important;
        direction: rtl;
        text-align: right;
    }
    
    .stApp { direction: rtl; text-align: right; }
    
    /* تنسيق النماذج */
    div[data-testid="stForm"] { 
        text-align: right; 
        border: 1px solid #ddd; 
        padding: 25px; 
        border-radius: 12px; 
    }
    
    input, select, textarea { 
        font-size: 18px !important;
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
    
    /* تنسيق سطر البحث الجديد */
    .search-row-label {
        font-size: 20px !important;
        font-weight: bold;
        color: #1E3A8A;
        white-space: nowrap;
        padding-top: 10px;
    }
    
    /* تكبير خطوط الأزرار والقوائم */
    .stButton button {
        font-size: 18px !important;
        padding: 10px 20px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_final_v22.db", check_same_thread=False)
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

# --- دالة تصدير الإكسل المنسق ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        worksheet.right_to_left()
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)
        cell_format = workbook.add_format({'font_size': 14, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 22, cell_format)
        for row_num in range(1, len(df) + 1):
            for col_num in range(len(df.columns)):
                worksheet.write(row_num, col_num, df.iloc[row_num-1, col_num], cell_format)
    return output.getvalue()

if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

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
            except: st.error("❌ فشل الاتصال بالحسابات")
    with tab2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول المسؤول"):
                st.session_state.update({'auth': True, 'user_type': "admin"})
                st.rerun()
    st.stop()

# --- 4. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    
    # القائمة الجانبية
    menu = st.sidebar.radio("القائمة الرئيسية:", ["إضافة", "الالتقارير"])

    # نقل زر تسجيل الخروج للأسفل في الوسط
    st.sidebar.markdown("<br>"*15, unsafe_allow_html=True)
    col_out1, col_out2, col_out3 = st.sidebar.columns([1, 2, 1])
    with col_out2:
        if st.button("🚪 خروج"):
            st.session_state.clear()
            st.rerun()

    if menu == "إضافة":
        # تصميم سطر البحث (العنوان بجانب المستطيل)
        col_lbl, col_inp = st.columns([1, 3])
        with col_lbl:
            st.markdown("<div class='search-row-label'>🔍 بحث برقم الهوية:</div>", unsafe_allow_html=True)
        with col_inp:
            search_id = st.text_input("", placeholder="أدخل 9 خانات للبحث أو التعديل...", key=f"search_{st.session_state.reset_key}", label_visibility="collapsed").strip()
        
        found_row, is_main = None, False
        if search_id:
            df_m = pd.read_sql(f"SELECT * FROM main_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
            if not df_m.empty: found_row, is_main = df_m.iloc[0], True; st.success(f"✅ تم العثور على الموظف: {found_row['name']}")
            else:
                df_c = pd.read_sql(f"SELECT * FROM correction_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
                if not df_c.empty: found_row, is_main = df_c.iloc[0], False; st.success(f"✅ تم العثور في كشف التصحيح: {found_row['name']}")
                else: st.warning("ℹ️ الرقم غير مسجل. يمكنك البدء بإدخال بيانات جديدة.")

        if found_row is not None:
            if st.button("🗑️ حذف هذا السجل"):
                c.execute("DELETE FROM main_table WHERE id_num=?", (search_id,)); c.execute("DELETE FROM correction_table WHERE id_num=?", (search_id,))
                conn.commit(); st.session_state.reset_key += 1; st.success("✅ تم الحذف"); time.sleep(1); st.rerun()

        st.divider()
        t_m, t_c = st.tabs(["📝 مراقبة وتوظيف", "✍️ تصحيح"])
        with t_m:
            if get_form_status('ثانوية') or get_form_status('توظيف'):
                mode_list = ["الثانوية العامة", "امتحان التوظيف"]
                default_mode = found_row['type'] if (found_row is not None and is_main) else mode_list[0]
                mode = st.radio("نوع النموذج:", mode_list, index=mode_list.index(default_mode) if default_mode in mode_list else 0)
                with st.form(key=f"m_form_{st.session_state.reset_key}"):
                    c1, c2 = st.columns(2)
                    id_num = c2.text_input("رقم الهوية (9 خانات) *", value=search_id)
                    name = c1.text_input("الاسم رباعي *", value=found_row['name'] if (found_row is not None and is_main) else "")
                    phone = c1.text_input("رقم الجوال (10 خانات) *", value=found_row['phone'] if (found_row is not None and is_main) else "")
                    address = st.text_input("مكان السكن (إجباري) *", value=found_row['address'] if (found_row is not None and is_main) else "")
                    job_list = ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"]
                    job = c2.selectbox("الوظيفة *", job_list, index=job_list.index(found_row['job_title']) if (found_row is not None and is_main and found_row['job_title'] in job_list) else 0)
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية (اختياري)", value=found_row['school2'] if (found_row is not None and is_main) else "")
                    rel_ex = st.text_input("امتحان القريب المباشر (اختياري)", value=found_row['relative_exam'] if (found_row is not None and is_main) else "")
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], index=0 if (found_row is None or not is_main or found_row['desire'] == "يرغب") else 1, horizontal=True)
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], index=0 if (found_row is None or not is_main or found_row['principal_note'] == "يصلح") else 1, horizontal=True)
                    if st.form_submit_button("💾 حفظ البيانات"):
                        if not (name and id_num and phone and address and job): st.error("⚠️ يرجى تعبئة الحقول الإجبارية")
                        else:
                            c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, address, rel_ex, job, desire, note, mode))
                            conn.commit(); st.success("✅ تم الحفظ بنجاح"); st.session_state.reset_key += 1; time.sleep(1.2); st.rerun()

        with t_c:
            if get_form_status('تصحيح'):
                with st.form(key=f"c_form_{st.session_state.reset_key}"):
                    c1, c2 = st.columns(2)
                    c_id = c2.text_input("رقم الهوية (9 خانات) *", value=search_id)
                    c_name = c1.text_input("الاسم الرباعي *", value=found_row['name'] if (found_row is not None and not is_main) else "")
                    c_phone = c1.text_input("الجوال (10 خانات) *", value=found_row['phone'] if (found_row is not None and not is_main) else "")
                    c_address = c2.text_input("مكان السكن (إجباري) *", value=found_row['address'] if (found_row is not None and not is_main) else "")
                    branch_list = ["", "علمي", "أدبي", "تجاري", "صناعي", "فندقي", "زراعي"]
                    c_branch = c1.selectbox("الفرع *", branch_list, index=branch_list.index(found_row['branch']) if (found_row is not None and not is_main and found_row['branch'] in branch_list) else 0)
                    sub_list = ["", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "أخرى"]
                    c_subj = c2.selectbox("المبحث *", sub_list, index=sub_list.index(found_row['subject']) if (found_row is not None and not is_main and found_row['subject'] in sub_list) else 0)
                    st.divider()
                    has_rel = st.radio("هل له قريب مباشر يتقدم للامتحان؟", ["لا يوجد", "يوجد"], index=0 if (found_row is None or not is_main or found_row['has_relative'] == "لا يوجد") else 1, horizontal=True)
                    rel_details = st.text_input("اسم القريب المباشر رباعياً (إن وجد)", value=found_row['relative_details'] if (found_row is not None and not is_main) else "")
                    st.selectbox("علاقة القرابة", ["", "ابن/ابنة", "أخ/أخت", "زوج/زوجة", "حفيد/حفيدة"]) 
                    if st.form_submit_button("💾 حفظ طلب التصحيح"):
                        if not (c_name and c_id and c_phone and c_address and c_subj and c_branch): st.error("⚠️ يرجى تعبئة الحقول الأساسية")
                        else:
                            c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?)", (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subj, c_branch, c_address, has_rel, rel_details, c_phone))
                            conn.commit(); st.success("✅ تم حفظ الطلب بنجاح"); st.session_state.reset_key += 1; time.sleep(1.2); st.rerun()

    elif menu == "التقارير":
        st.subheader("📊 سجلات المدرسة")
        df1 = pd.read_sql(f"SELECT * FROM main_table WHERE school_user='{st.session_state['school_user']}'", conn)
        df2 = pd.read_sql(f"SELECT * FROM correction_table WHERE school_user='{st.session_state['school_user']}'", conn)
        if not df1.empty:
            st.info("🔹 كشف المراقبة والتوظيف")
            df1_view = df1.rename(columns={'id_num':'الهوية','name':'الاسم','phone':'الجوال','address':'السكن','job_title':'الوظيفة','type':'النوع'})
            st.dataframe(df1_view.drop(columns=['school_user','school_full_name']), use_container_width=True)
            st.download_button(label="📥 تحميل كشف المراقبة (Excel)", data=to_excel(df1_view.drop(columns=['school_user','school_full_name'])), file_name='monitoring.xlsx')
        if not df2.empty:
            st.divider(); st.success("🔹 كشف التصحيح")
            df2_view = df2.rename(columns={'id_num':'الهوية','name':'الاسم','address':'السكن','subject':'المبحث', 'branch':'الفرع'})
            st.dataframe(df2_view[['الهوية','الاسم','السكن','الفرع','المبحث']], use_container_width=True)
            st.download_button(label="📥 تحميل كشف التصحيح (Excel)", data=to_excel(df2_view[['الهوية','الاسم','السكن','الفرع','المبحث']]), file_name='correction.xlsx')

# --- 5. واجهة الإدارة ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ لوحة تحكم الإدارة")
    st.sidebar.markdown("<br>"*15, unsafe_allow_html=True)
    if st.sidebar.button("🚪 خروج"): st.session_state.clear(); st.rerun()
    
    adm_menu = st.sidebar.selectbox("القائمة:", ["إدارة البيانات", "صلاحيات النماذج"])
    if adm_menu == "صلاحيات النماذج":
        cols = st.columns(3)
        for i, f in enumerate(['ثانوية', 'توظيف', 'تصحيح']):
            with cols[i]:
                curr = get_form_status(f); st.write(f"نموذج {f}: {'✅ مفتوح' if curr else '❌ مغلق'}")
                if st.button(f"تغيير {f}", key=f"at_{f}"): c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (0 if curr else 1, f)); conn.commit(); st.rerun()
    else:
        t1, t2, t3 = st.tabs(["المراقبة", "التوظيف", "التصحيح"])
        def view_admin(t_name, d_type, k_s, is_c=False):
            df = pd.read_sql("SELECT * FROM correction_table", conn) if is_c else pd.read_sql(f"SELECT * FROM main_table WHERE type='{d_type}'", conn)
            sel = st.selectbox(f"مدرسة ({t_name}):", ["الكل"] + sorted(df['school_full_name'].unique().tolist()), key=f"s_{k_s}")
            f_df = df if sel == "الكل" else df[df['school_full_name'] == sel]
            st.dataframe(f_df)
            st.download_button(label=f"📥 تحميل ({t_name})", data=to_excel(f_df), file_name=f'admin_{k_s}.xlsx')
            target = st.selectbox(f"حذف هوية ({t_name}):", [""] + f_df['id_num'].tolist(), key=f"d_{k_s}")
            if st.button(f"تأكيد الحذف {target}", key=f"b_{k_s}"):
                if target: c.execute(f"DELETE FROM {'correction_table' if is_c else 'main_table'} WHERE id_num=?", (target,)); conn.commit(); st.rerun()
        with t1: view_admin("ثانوية عامة", "الثانوية العامة", "tw")
        with t2: view_admin("توظيف", "امتحان التوظيف", "em")
        with t3: view_admin("تصحيح", "", "cr", True)

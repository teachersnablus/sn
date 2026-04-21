import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
import time

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام قسم الإمتحانات مديرية جنوب نابلس", layout="wide")

# إعداد الحالة الابتدائية لتجنب أخطاء Streamlit
if 'main_search_input' not in st.session_state:
    st.session_state['main_search_input'] = ""
if 'reset_key' not in st.session_state:
    st.session_state.reset_key = 0
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': "", 'menu_choice': "إضافة"})

st.markdown("""
    <style>
        .custom-header {
            position: fixed; top: 0; left: 0; width: 100%; background-color: #1a1c23; color: white;
            text-align: center; padding: 15px 0; z-index: 9999; border-bottom: 2px solid #00ffcc;
            line-height: 1.5; direction: rtl; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        }
        [data-testid="stSidebar"] { display: none; }
        .stApp { margin-top: 80px; direction: rtl; text-align: right; }
        header {visibility: hidden;}
        html, body, [class*="st-"] { font-size: 19px !important; direction: rtl; text-align: right; }
        div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 25px; border-radius: 12px; }
        .school-title { color: #ffffff; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; font-size: 26px !important; font-weight: bold; margin-top: 20px; margin-bottom: 20px; }
        .search-row-label { font-size: 20px !important; font-weight: bold; color: #ffffff; background-color: #1E3A8A; padding: 10px 15px; border-radius: 8px; text-align: center; }
        .note-box { background-color: #fff3cd; border: 2px solid #ffc107; color: #856404; padding: 12px 20px; border-radius: 8px; font-weight: bold; text-align: center; margin-bottom: 15px; }
    </style>
    <div class="custom-header">
        <div style="font-weight: bold; font-size: 1.2rem;">إعداد وتصميم : عوض نعمان ريده</div>
        <div style="font-size: 1rem; color: #00ffcc;">قسم الامتحانات - مديرية التربية والتعليم جنوب نابلس</div>
    </div>
    """, unsafe_allow_html=True)

COLUMN_NAMES_MAP = {
    'الرقم': 'الرقم', 'id_num': 'رقم الهوية', 'name': 'الاسم رباعي',
    'school_user': 'رقم المدرسة', 'school_full_name': 'اسم المدرسة',
    'school2': 'المدرسة الثانية', 'phone': 'رقم الجوال', 'address': 'مكان السكن',
    'relative_exam': 'اسم القريب المباشر', 'job_title': 'الوظيفة',
    'desire': 'الرغبة', 'principal_note': 'رأي المدير', 'type': 'نوع النظام',
    'gender': 'الجنس', 'subject': 'المبحث', 'branch': 'الفرع',
    'has_relative': 'هل يوجد قريب؟', 'relative_details': 'تفاصيل القريب'
}

SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

@st.cache_data(ttl=600)
def load_accounts():
    try: return pd.read_csv(SCHOOLS_ACCOUNTS_URL)
    except: return pd.DataFrame(columns=['school_user', 'password', 'school_full_name'])

RESIDENCE_AREAS = ["", "نابلس", "رام الله", "سلفيت", "طولكرم", "عورتا", "أودلا", "بيتا", "عقربا", "مجدل بني فاضل", "دوما", "قريوت", "جالود", "تلفيت", "قصرة", "جوريش", "قبلان", "يتما", "اللبن", "الساوية", "جماعين", "زيتا", "عوريف", "عصيرة القبلية", "بورين", "مادما","عينابوس","حوارة", "يانون", "أوصرين"]
GENDER_OPTIONS = ["", "ذكر", "أنثى"]
jobs_list = ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"]

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_final_v31.db", check_same_thread=False)
c = conn.cursor()

def auto_fix_db_schema():
    c.execute('''CREATE TABLE IF NOT EXISTS system_settings (form_name TEXT PRIMARY KEY, is_open INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS main_table (id INTEGER PRIMARY KEY AUTOINCREMENT, id_num TEXT, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, phone TEXT, address TEXT, relative_exam TEXT, job_title TEXT, desire TEXT, principal_note TEXT, type TEXT, gender TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS correction_table (id INTEGER PRIMARY KEY AUTOINCREMENT, id_num TEXT, name TEXT, school_user TEXT, school_full_name TEXT, subject TEXT, branch TEXT, address TEXT, has_relative TEXT, relative_details TEXT, phone TEXT)''')
    conn.commit()

auto_fix_db_schema()

def get_val(row, idx, default=""):
    try: return row[idx] if row and row[idx] is not None else default
    except: return default

def to_excel_formatted(df, report_title="تقرير", school_name=""):
    output = BytesIO()
    df_excel = df.copy()
    cols_to_drop = [col for col in ['id', 'school_user', 'school_full_name'] if col in df_excel.columns]
    if cols_to_drop: df_excel = df_excel.drop(columns=cols_to_drop)
    df_excel.insert(0, 'الرقم', range(1, len(df_excel) + 1))
    df_excel = df_excel.rename(columns={k: v for k, v in COLUMN_NAMES_MAP.items() if k in df_excel.columns})
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        cell_format = workbook.add_format({'font_size': 13, 'font_name': 'Arial', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'font_size': 13, 'bold': True, 'border': 1, 'bg_color': '#D7E4BC', 'align': 'center'})
        worksheet.right_to_left()
        for i, col in enumerate(df_excel.columns):
            worksheet.set_column(i, i, 20, cell_format)
            worksheet.write(0, i, col, header_format)
    return output.getvalue()

def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

def validate_inputs(id_num, phone):
    if len(id_num) != 9 or not id_num.isdigit():
        st.error("❌ رقم الهوية يجب أن يتكون من 9 أرقام.")
        return False
    if len(phone) != 10 or not phone.isdigit():
        st.error("❌ رقم الجوال يجب أن يتكون من 10 أرقام.")
        return False
    return True

# --- تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة تجميع المراقبة والتصحيح - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول القسم"])
    with tab1:
        with st.form("l1"):
            u = st.text_input("رقم المدرسة")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                df_acc = load_accounts()
                match = df_acc[(df_acc['school_user'].astype(str) == u) & (df_acc['password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u, 'school_display_name': str(match.iloc[0]['school_full_name'])})
                    st.rerun()
                else: st.error("بيانات خاطئة")
    with tab2:
        with st.form("l2"):
            adm_p = st.text_input("كلمة مرور القسم", type="password")
            if st.form_submit_button("دخول"):
                if adm_p == "ADMIN2026":
                    st.session_state.update({'auth': True, 'user_type': "admin", 'menu_choice': "إدارة البيانات"})
                    st.rerun()
    st.stop()

# --- شاشة المدارس ---
if st.session_state['user_type'] == "school":
    nav1, nav2, nav3, nav4 = st.columns([1, 1, 2, 1])
    with nav1: 
        if st.button("➕ إضافة/تعديل", use_container_width=True): st.session_state.menu_choice = "إضافة"
    with nav2: 
        if st.button("📊 التقارير", use_container_width=True): st.session_state.menu_choice = "التقارير"
    with nav4: 
        if st.button("🚪 خروج", use_container_width=True): st.session_state.clear(); st.rerun()

    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)

    if st.session_state.menu_choice == "إضافة":
        col_lbl, col_inp = st.columns([1.2, 3])
        with col_lbl: st.markdown("<div class='search-row-label'>🔍 بحث برقم الهوية</div>", unsafe_allow_html=True)
        
        # استخدام الحقل بربطه مع الـ session_state مباشرة
        search_id = st.text_input("", placeholder="أدخل رقم الهوية للبحث...", key="main_search_input", label_visibility="collapsed").strip()
        
        found_data = {"main_sec": None, "main_job": None, "cor": None}
        if len(search_id) == 9:
            c.execute("SELECT * FROM main_table WHERE id_num=? AND school_user=? AND type=?", (search_id, st.session_state['school_user'], "الثانوية العامة"))
            found_data["main_sec"] = c.fetchone()
            c.execute("SELECT * FROM main_table WHERE id_num=? AND school_user=? AND type=?", (search_id, st.session_state['school_user'], "امتحان التوظيف"))
            found_data["main_job"] = c.fetchone()
            c.execute("SELECT * FROM correction_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user']))
            found_data["cor"] = c.fetchone()

        st.divider()
        t_sec, t_job, t_cor = st.tabs(["📝 الثانوية العامة", "📋 امتحان التوظيف", "✍️ التصحيح"])

        # ==================== تبويب الثانوية العامة ====================
        with t_sec:
            if get_form_status('ثانوية'):
                m_row = found_data["main_sec"]
                with st.form(key=f"sec_form_{st.session_state.reset_key}"):
                    st.markdown('<div class="note-box">📋 بيانات معلمي الثانوية العامة (المراقبة)</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    # رقم الهوية مفتوح للتعديل ويأخذ قيمته من البحث
                    id_num_form = c2.text_input("رقم الهوية *", value=search_id if search_id else "")
                    name = c1.text_input("الاسم رباعي *", value=get_val(m_row, 2))
                    phone = c1.text_input("الجوال *", value=get_val(m_row, 6))
                    
                    addr_idx = RESIDENCE_AREAS.index(m_row[7]) if m_row and m_row[7] in RESIDENCE_AREAS else 0
                    address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=addr_idx)
                    
                    job_idx = jobs_list.index(m_row[9]) if m_row and m_row[9] in jobs_list else 0
                    job = c1.selectbox("الوظيفة *", jobs_list, index=job_idx)
                    
                    gender_idx = GENDER_OPTIONS.index(m_row[13]) if m_row and m_row[13] in GENDER_OPTIONS else 0
                    gender = c2.selectbox("الجنس *", GENDER_OPTIONS, index=gender_idx)
                    
                    school2 = st.text_input("المدرسة الثانية", value=get_val(m_row, 5))
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], index=0 if get_val(m_row, 10) == "يرغب" else 1, horizontal=True)
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], index=0 if get_val(m_row, 11) == "يصلح" else 1, horizontal=True)
                    
                    if st.form_submit_button("💾 حفظ / تحديث"):
                        if not (name and id_num_form and phone and address and job and gender): st.error("أكمل البيانات")
                        elif validate_inputs(id_num_form, phone):
                            if m_row:
                                c.execute("UPDATE main_table SET id_num=?, name=?, phone=?, address=?, job_title=?, school2=?, desire=?, principal_note=?, gender=? WHERE id_num=? AND school_user=? AND type='الثانوية العامة'", (id_num_form, name, phone, address, job, school2, desire, note, gender, search_id, st.session_state['school_user']))
                            else:
                                c.execute("INSERT INTO main_table (id_num, name, school_user, school_full_name, school2, phone, address, job_title, desire, principal_note, type, gender) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (id_num_form, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, address, job, desire, note, "الثانوية العامة", gender))
                            conn.commit()
                            st.success("تم الحفظ بنجاح")
                            # تفريغ البيانات
                            st.session_state['main_search_input'] = ""
                            st.session_state.reset_key += 1
                            time.sleep(0.5)
                            st.rerun()

        # ==================== تبويب امتحان التوظيف ====================
        with t_job:
            if get_form_status('توظيف'):
                j_row = found_data["main_job"]
                with st.form(key=f"job_form_{st.session_state.reset_key}"):
                    st.markdown('<div class="note-box">📋 بيانات المراقبة لامتحان التوظيف</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    id_num_form = c2.text_input("رقم الهوية *", value=search_id if search_id else "")
                    name = c1.text_input("الاسم رباعي *", value=get_val(j_row, 2))
                    phone = c1.text_input("الجوال *", value=get_val(j_row, 6))
                    
                    addr_idx = RESIDENCE_AREAS.index(j_row[7]) if j_row and j_row[7] in RESIDENCE_AREAS else 0
                    address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=addr_idx)
                    
                    job_idx = jobs_list.index(j_row[9]) if j_row and j_row[9] in jobs_list else 0
                    job = c1.selectbox("الوظيفة *", jobs_list, index=job_idx)
                    
                    gender_idx = GENDER_OPTIONS.index(j_row[13]) if j_row and j_row[13] in GENDER_OPTIONS else 0
                    gender = c2.selectbox("الجنس *", GENDER_OPTIONS, index=gender_idx)
                    
                    rel_val = get_val(j_row, 8)
                    has_rel = st.radio("هل له قريب مباشر؟", ["لا يوجد", "يوجد"], index=1 if rel_val else 0, horizontal=True)
                    rel_exam = st.text_input("اسم القريب المباشر", value=rel_val)
                    
                    if st.form_submit_button("💾 حفظ / تحديث"):
                        if not (name and id_num_form and phone and address and job and gender): st.error("أكمل البيانات")
                        elif validate_inputs(id_num_form, phone):
                            if j_row:
                                c.execute("UPDATE main_table SET id_num=?, name=?, phone=?, address=?, job_title=?, relative_exam=?, gender=? WHERE id_num=? AND school_user=? AND type='امتحان التوظيف'", (id_num_form, name, phone, address, job, rel_exam, gender, search_id, st.session_state['school_user']))
                            else:
                                c.execute("INSERT INTO main_table (id_num, name, school_user, school_full_name, phone, address, relative_exam, job_title, type, gender) VALUES (?,?,?,?,?,?,?,?,?,?)", (id_num_form, name, st.session_state['school_user'], st.session_state['school_display_name'], phone, address, rel_exam, job, "امتحان التوظيف", gender))
                            conn.commit()
                            st.success("تم الحفظ بنجاح")
                            st.session_state['main_search_input'] = ""
                            st.session_state.reset_key += 1
                            time.sleep(0.5)
                            st.rerun()

        # ==================== تبويب التصحيح ====================
        with t_cor:
            if get_form_status('تصحيح'):
                c_row = found_data["cor"]
                with st.form(key=f"cor_form_{st.session_state.reset_key}"):
                    st.markdown('<div class="note-box">✍️ بيانات المعلمين المرشحين للتصحيح</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    id_num_form = c2.text_input("رقم الهوية *", value=search_id if search_id else "")
                    name = c1.text_input("الاسم رباعي *", value=get_val(c_row, 2))
                    phone = c1.text_input("الجوال *", value=get_val(c_row, 10))
                    
                    addr_idx = RESIDENCE_AREAS.index(c_row[7]) if c_row and c_row[7] in RESIDENCE_AREAS else 0
                    address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=addr_idx)
                    
                    branches = ["", "علمي", "أدبي", "تجاري", "صناعي", "فندقي", "زراعي", "اقتصاد منزلي"]
                    br_idx = branches.index(c_row[6]) if c_row and c_row[6] in branches else 0
                    branch = c1.selectbox("الفرع *", branches, index=br_idx)
                    
                    subjects = ["", "اللغة العربية", "اللغة الإنجليزية", "الرياضيات", "التربية الإسلامية", "الفيزياء", "الكيمياء", "الأحياء", "تكنولوجيا المعلومات", "التاريخ", "الجغرافيا","الثقافة العلمية", "فرع (الريادة و الأعمال)", "فرع (الاقتصاد المنزلي)", "الفروع المهنية"]
                    sub_idx = subjects.index(c_row[5]) if c_row and c_row[5] in subjects else 0
                    subj = c2.selectbox("المبحث *", subjects, index=sub_idx)
                    
                    rel_det = get_val(c_row, 9)
                    has_rel = st.radio("هل يوجد قريب؟", ["لا يوجد", "يوجد"], index=1 if rel_det else 0, horizontal=True)
                    rel_name = st.text_input("اسم القريب", value=rel_det)

                    if st.form_submit_button("💾 حفظ / تحديث"):
                        if not (name and id_num_form and phone and address and subj and branch): st.error("أكمل البيانات")
                        elif validate_inputs(id_num_form, phone):
                            if c_row:
                                c.execute("UPDATE correction_table SET id_num=?, name=?, subject=?, branch=?, address=?, has_relative=?, relative_details=?, phone=? WHERE id_num=? AND school_user=?", (id_num_form, name, subj, branch, address, has_rel, rel_name, phone, search_id, st.session_state['school_user']))
                            else:
                                c.execute("INSERT INTO correction_table (id_num, name, school_user, school_full_name, subject, branch, address, has_relative, relative_details, phone) VALUES (?,?,?,?,?,?,?,?,?,?)", (id_num_form, name, st.session_state['school_user'], st.session_state['school_display_name'], subj, branch, address, has_rel, rel_name, phone))
                            conn.commit()
                            st.success("تم الحفظ بنجاح")
                            st.session_state['main_search_input'] = ""
                            st.session_state.reset_key += 1
                            time.sleep(0.5)
                            st.rerun()

    elif st.session_state.menu_choice == "التقارير":
        st.subheader("📊 سجلات المدرسة الموثقة")
        df1 = pd.read_sql_query("SELECT * FROM main_table WHERE school_user=?", conn, params=(st.session_state['school_user'],))
        df2 = pd.read_sql_query("SELECT * FROM correction_table WHERE school_user=?", conn, params=(st.session_state['school_user'],))
        
        if not df1.empty:
            st.info("🔹 كشف المراقبة والتوظيف")
            st.dataframe(df1.drop(columns=['id', 'school_user']).rename(columns=COLUMN_NAMES_MAP), use_container_width=True)
            st.download_button("📥 تحميل المراقبة", data=to_excel_formatted(df1, "", st.session_state['school_display_name']), file_name="مراقبة.xlsx")
        
        if not df2.empty:
            st.success("🔹 كشف التصحيح")
            st.dataframe(df2.drop(columns=['id', 'school_user']).rename(columns=COLUMN_NAMES_MAP), use_container_width=True)
            st.download_button("📥 تحميل التصحيح", data=to_excel_formatted(df2, "", st.session_state['school_display_name']), file_name="تصحيح.xlsx")

# --- شاشة الإدارة ---
elif st.session_state['user_type'] == "admin":
    adm_nav1, adm_nav2, adm_nav4 = st.columns([1, 1, 1])
    with adm_nav1: 
        if st.button("📂 إدارة البيانات"): st.session_state.menu_choice = "إدارة البيانات"
    with adm_nav2: 
        if st.button("⚙️ الصلاحيات"): st.session_state.menu_choice = "صلاحيات النماذج"
    with adm_nav4: 
        if st.button("🚪 خروج"): st.session_state.clear(); st.rerun()

    if st.session_state.menu_choice == "صلاحيات النماذج":
        for f in ['ثانوية', 'توظيف', 'تصحيح']:
            curr = get_form_status(f)
            if st.button(f"نموذج {f}: {'✅ مفتوح (اضغط للإغلاق)' if curr else '❌ مغلق (اضغط للفتح)'}"):
                c.execute("INSERT OR REPLACE INTO system_settings VALUES (?, ?)", (f, 0 if curr else 1))
                conn.commit(); st.rerun()
    else:
        st.title("📂 عرض بيانات جميع المدارس")
        t1, t2, t3 = st.tabs(["الثانوية العامة", "امتحان التوظيف", "التصحيح"])
        
        def admin_view(query, params, title):
            df = pd.read_sql_query(query, conn, params=params)
            if not df.empty:
                st.dataframe(df.rename(columns=COLUMN_NAMES_MAP), use_container_width=True)
                st.download_button(f"تحميل {title}", data=to_excel_formatted(df), file_name=f"{title}.xlsx")
            else: st.info("لا توجد بيانات")

        with t1: admin_view("SELECT * FROM main_table WHERE type='الثانوية العامة'", (), "ثانوية_عامة")
        with t2: admin_view("SELECT * FROM main_table WHERE type='امتحان التوظيف'", (), "توظيف")
        with t3: admin_view("SELECT * FROM correction_table", (), "تصحيح")

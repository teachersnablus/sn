import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
import time

# قاموس ترجمة الأعمدة
COLUMN_NAMES_MAP = {
    'الرقم': 'الرقم', 'id_num': 'رقم الهوية', 'name': 'الاسم رباعي',
    'school_user': 'رقم المدرسة', 'school_full_name': 'اسم المدرسة',
    'school2': 'المدرسة الثانية', 'phone': 'رقم الجوال', 'address': 'مكان السكن',
    'relative_exam': 'اسم القريب المباشر', 'job_title': 'الوظيفة',
    'desire': 'الرغبة', 'principal_note': 'رأي المدير', 'type': 'نوع النظام',
    'gender': 'الجنس', 'subject': 'المبحث', 'branch': 'الفرع',
    'has_relative': 'هل يوجد قريب؟', 'relative_details': 'تفاصيل القريب'
}

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام قسم الإمتحانات مديرية جنوب نابلس", layout="wide")

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

SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

@st.cache_data(ttl=600)
def load_accounts():
    try:
        return pd.read_csv(SCHOOLS_ACCOUNTS_URL)
    except:
        return pd.DataFrame(columns=['school_user', 'password', 'school_full_name'])

RESIDENCE_AREAS = [
    "", "نابلس", "رام الله", "سلفيت", "طولكرم", "عورتا", "أودلا", "بيتا", "عقربا", 
    "مجدل بني فاضل", "دوما", "قريوت", "جالود", "تلفيت", "قصرة", "جوريش", "قبلان", 
    "يتما", "اللبن", "الساوية", "جماعين", "زيتا", "عوريف", "عصيرة القبلية", "بورين", 
    "مادما","عينابوس","حوارة", "يانون", "أوصرين"
]
GENDER_OPTIONS = ["", "ذكر", "أنثى"]

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_final_v31.db", check_same_thread=False)
c = conn.cursor()

def auto_fix_db_schema():
    c.execute("PRAGMA table_info(system_settings)")
    if [col[1] for col in c.fetchall()] != ['form_name', 'is_open']:
        c.execute("DROP TABLE IF EXISTS system_settings")
        c.execute('''CREATE TABLE system_settings (form_name TEXT PRIMARY KEY, is_open INTEGER)''')
    for tbl, create_sql in [
        ('main_table', 'id INTEGER PRIMARY KEY AUTOINCREMENT, id_num TEXT, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, phone TEXT, address TEXT, relative_exam TEXT, job_title TEXT, desire TEXT, principal_note TEXT, type TEXT, gender TEXT'),
        ('correction_table', 'id INTEGER PRIMARY KEY AUTOINCREMENT, id_num TEXT, name TEXT, school_user TEXT, school_full_name TEXT, subject TEXT, branch TEXT, address TEXT, has_relative TEXT, relative_details TEXT, phone TEXT')
    ]:
        c.execute(f"PRAGMA table_info({tbl})")
        existing = [col[1] for col in c.fetchall()]
        expected = [part.split()[0] for part in create_sql.split(', ')]
        if existing != expected:
            c.execute(f"DROP TABLE IF EXISTS {tbl}")
        c.execute(f"CREATE TABLE IF NOT EXISTS {tbl} ({create_sql})")

auto_fix_db_schema()

for form in ['ثانوية', 'توظيف', 'تصحيح']:
    c.execute("INSERT OR IGNORE INTO system_settings VALUES (?, 1)", (form,))
conn.commit()

# ✅ دالة تصدير إكسل منسقة باحترافية
def to_excel_formatted(df, report_title="تقرير", school_name=""):
    output = BytesIO()
    df_excel = df.copy()
    
    # إزالة الأعمدة الداخلية
    cols_to_drop = [col for col in ['id', 'school_user', 'school_full_name'] if col in df_excel.columns]
    if cols_to_drop: df_excel = df_excel.drop(columns=cols_to_drop)
    
    # إضافة الترقيم
    df_excel.insert(0, 'الرقم', range(1, len(df_excel) + 1))
    
    # ترجمة الأعمدة
    df_excel = df_excel.rename(columns={k: v for k, v in COLUMN_NAMES_MAP.items() if k in df_excel.columns})
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # ✅ تنسيق الخلايا (خط 13، سطر واحد، حدود كاملة)
        cell_format = workbook.add_format({
            'font_size': 13, 'font_name': 'Arial', 'border': 1,
            'align': 'center', 'valign': 'vcenter', 'text_wrap': False
        })
        header_format = workbook.add_format({
            'font_size': 13, 'font_name': 'Arial', 'bold': True, 'border': 1,
            'bg_color': '#D7E4BC', 'align': 'center', 'valign': 'vcenter', 'text_wrap': False
        })
        # ✅ تنسيق التوقيع والخاتم (خط 14 كما طلبت)
        sig_format = workbook.add_format({
            'font_size': 14, 'font_name': 'Arial', 'align': 'right', 'valign': 'vcenter', 'border': 0
        })
        
        # ✅ إعدادات الطباعة والصفحة
        worksheet.right_to_left()
        worksheet.set_landscape()               # وضع أفقي
        worksheet.fit_to_pages(1, 0)            # احتواء العرض في صفحة واحدة
        worksheet.set_margins(left=0.3, right=0.3, top=0.4, bottom=0.4)
        
        # ✅ ضبط عرض الأعمدة ديناميكياً
        for i, col in enumerate(df_excel.columns):
            try: max_len = max(df_excel[col].dropna().astype(str).str.len().max(), len(str(col)) + 2)
            except: max_len = 12
            worksheet.set_column(i, i, min(max_len * 1.4, 45), cell_format)
            
        # ✅ كتابة الرؤوس والبيانات
        for col_num, value in enumerate(df_excel.columns.values):
            worksheet.write(0, col_num, value, header_format)
        for row_num, row in enumerate(df_excel.values, start=1):
            for col_num, value in enumerate(row):
                worksheet.write(row_num, col_num, str(value) if pd.notna(value) else "", cell_format)
                
        # ✅ التوقيع والخاتم (باستخدام write لتجنب خطأ التداخل)
        last_row = len(df_excel) + 3
        worksheet.merge_range(f'A{last_row}:F{last_row}', 'توقيع مدير المدرسة: ........................', sig_format)
        worksheet.merge_range(f'G{last_row}:L{last_row}', f'خاتم المدرسة: {school_name}', sig_format)
        
    return output.getvalue()

if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
if 'auth' not in st.session_state: 
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': "", 'menu_choice': "إضافة"})
if 'has_rel_job' not in st.session_state: st.session_state.has_rel_job = "لا يوجد"
if 'has_rel_cor' not in st.session_state: st.session_state.has_rel_cor = "لا يوجد"

def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

def validate_inputs(id_num, phone):
    if len(id_num) != 9 or not id_num.isdigit():
        st.error("❌ خطأ: رقم الهوية يجب أن يتكون من 9 أرقام بالضبط.")
        return False
    if len(phone) != 10 or not phone.isdigit():
        st.error("❌ خطأ: رقم الجوال يجب أن يتكون من 10 أرقام بالضبط.")
        return False
    return True

# --- 3. تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة تجميع المراقبة والتصحيح مديرية التربية والتعليم - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول القسم"])
    with tab1:
        with st.form(key="school_login_form"):
            u_in = st.text_input("رقم المدرسة", key="school_user_input").strip()
            p_in = st.text_input("كلمة المرور", type="password", key="school_pass_input").strip()
            if st.form_submit_button("دخول المدارس"):
                df_acc = load_accounts()
                if df_acc is not None and not df_acc.empty:
                    match = df_acc[(df_acc['school_user'].astype(str) == u_in) & (df_acc['password'].astype(str) == p_in)]
                    if not match.empty:
                        st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u_in, 'school_display_name': str(match.iloc[0]['school_full_name'])})
                        st.rerun()
                    else: st.error("❌ بيانات الحساب خاطئة")
                else: st.error("❌ فشل الاتصال")
    with tab2:
        with st.form(key="admin_login_form"):
            adm_pass = st.text_input("كلمة مرور القسم", type="password", key="admin_pass_input")
            if st.form_submit_button("دخول القسم"):
                if adm_pass == "ADMIN2026":
                    st.session_state.update({'auth': True, 'user_type': "admin", 'menu_choice': "إدارة البيانات"})
                    st.rerun()
                else: st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- شاشة المدارس المحدثة بخاصية التعديل ---
if st.session_state['user_type'] == "school":
    nav1, nav2, nav3, nav4 = st.columns([1, 1, 2, 1])
    with nav1:
        if st.button("➕ إضافة/تعديل بيانات", use_container_width=True): st.session_state.menu_choice = "إضافة"
    with nav2:
        if st.button("📊 التقارير", use_container_width=True): st.session_state.menu_choice = "التقارير"
    with nav4:
        if st.button("🚪 تسجيل الخروج", use_container_width=True): st.session_state.clear(); st.rerun()

    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)

    if st.session_state.menu_choice == "إضافة":
        col_lbl, col_inp = st.columns([1.2, 3])
        with col_lbl: st.markdown("<div class='search-row-label'>🔍 بحث برقم الهوية للتعديل</div>", unsafe_allow_html=True)
        with col_inp: search_id = st.text_input("", placeholder="أدخل رقم الهوية...", key=f"search_box", label_visibility="collapsed").strip()
        
        found_data = {"main": None, "correction": None}
        
        if search_id and len(search_id) == 9 and search_id.isdigit():
            # البحث في الجدول الرئيسي (ثانوية/توظيف)
            res_m = c.execute("SELECT * FROM main_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user'])).fetchone()
            # البحث في جدول التصحيح
            res_c = c.execute("SELECT * FROM correction_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user'])).fetchone()
            
            if res_m or res_c:
                st.success("✅ تم العثور على سجل مسبق لهذا الرقم. يمكنك التعديل أدناه أو الحذف.")
                if res_m: found_data["main"] = res_m
                if res_c: found_data["correction"] = res_c
                
                if st.button("🗑️ حذف السجل نهائياً"):
                    c.execute("DELETE FROM main_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user']))
                    c.execute("DELETE FROM correction_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user']))
                    conn.commit(); st.success("✅ تم الحذف"); time.sleep(1); st.rerun()
            else:
                st.info("ℹ️ الرقم متاح للتسجيل كجديد.")

        st.divider()
        t_sec, t_job, t_cor = st.tabs(["📝 الثانوية العامة", "📋 امتحان التوظيف", "✍️ التصحيح"])
        
        # دالة مساعدة لجلب القيمة الافتراضية عند التعديل
        def get_val(data_row, index, default=""):
            return data_row[index] if data_row else default

        # ==================== تبويب الثانوية العامة ====================
        with t_sec:
            if get_form_status('ثانوية'):
                # التحقق إذا كان السجل الموجود هو "ثانوية عامة"
                m_row = found_data["main"] if (found_data["main"] and found_data["main"][12] == "الثانوية العامة") else None
                with st.form(key=f"sec_form"):
                    st.markdown('<div class="note-box">📋 بيانات الثانوية العامة</div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    id_num = c2.text_input("رقم الهوية *", value=search_id if search_id else "", key="sec_id")
                    name = c1.text_input("الاسم رباعي *", value=get_val(m_row, 2))
                    phone = c1.text_input("رقم الجوال *", value=get_val(m_row, 6))
                    
                    addr_idx = RESIDENCE_AREAS.index(m_row[7]) if m_row and m_row[7] in RESIDENCE_AREAS else 0
                    address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=addr_idx)
                    
                    jobs_list = ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"]
                    job_idx = jobs_list.index(m_row[9]) if m_row and m_row[9] in jobs_list else 0
                    job = c1.selectbox("الوظيفة *", jobs_list, index=job_idx)
                    
                    gen_idx = GENDER_OPTIONS.index(m_row[13]) if m_row and m_row[13] in GENDER_OPTIONS else 0
                    gender = c2.selectbox("الجنس *", GENDER_OPTIONS, index=gen_idx)
                    
                    school2 = st.text_input("المدرسة الثانية", value=get_val(m_row, 5))
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], index=0 if get_val(m_row, 10) == "يرغب" else 1, horizontal=True)
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], index=0 if get_val(m_row, 11) == "يصلح" else 1, horizontal=True)
                    
                    btn_label = "💾 تحديث البيانات" if m_row else "💾 حفظ جديد"
                    if st.form_submit_button(btn_label):
                        if not (name and id_num and phone and address and job and gender): st.error("⚠️ حقول ناقصة")
                        elif validate_inputs(id_num, phone):
                            if m_row: # تحديث
                                c.execute("""UPDATE main_table SET name=?, phone=?, address=?, job_title=?, school2=?, desire=?, principal_note=?, gender=? 
                                             WHERE id_num=? AND school_user=? AND type='الثانوية العامة'""",
                                          (name, phone, address, job, school2, desire, note, gender, id_num, st.session_state['school_user']))
                            else: # إدخال جديد
                                c.execute("""INSERT INTO main_table (id_num, name, school_user, school_full_name, school2, phone, address, job_title, desire, principal_note, type, gender) 
                                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, address, job, desire, note, "الثانوية العامة", gender))
                            conn.commit(); st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()

        # ==================== تبويب امتحان التوظيف ====================
        with t_job:
            if get_form_status('توظيف'):
                j_row = found_data["main"] if (found_data["main"] and found_data["main"][12] == "امتحان التوظيف") else None
                with st.form(key="job_form"):
                    c1, c2 = st.columns(2)
                    id_num = c2.text_input("رقم الهوية *", value=search_id if search_id else "")
                    name = c1.text_input("الاسم رباعي *", value=get_val(j_row, 2))
                    phone = c1.text_input("رقم الجوال *", value=get_val(j_row, 6))
                    address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=RESIDENCE_AREAS.index(j_row[7]) if j_row and j_row[7] in RESIDENCE_AREAS else 0)
                    job = c1.selectbox("الوظيفة *", ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"], index=["", "معلم", "مدير مدرسة", "سكرتير", "آذن"].index(j_row[9]) if j_row else 0)
                    gender = c2.selectbox("الجنس *", GENDER_OPTIONS, index=GENDER_OPTIONS.index(j_row[13]) if j_row else 0)
                    
                    has_rel = st.radio("هل له قريب؟", ["لا يوجد", "يوجد"], index=1 if get_val(j_row, 8) else 0, horizontal=True)
                    rel_exam = st.text_input("اسم القريب", value=get_val(j_row, 8)) if has_rel == "يوجد" else ""
                    
                    if st.form_submit_button("💾 حفظ/تحديث التوظيف"):
                        if validate_inputs(id_num, phone):
                            if j_row:
                                c.execute("UPDATE main_table SET name=?, phone=?, address=?, job_title=?, relative_exam=?, gender=? WHERE id_num=? AND school_user=? AND type='امتحان التوظيف'",
                                          (name, phone, address, job, rel_exam, gender, id_num, st.session_state['school_user']))
                            else:
                                c.execute("INSERT INTO main_table (id_num, name, school_user, school_full_name, phone, address, job_title, relative_exam, type, gender) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                          (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], phone, address, job, rel_exam, "امتحان التوظيف", gender))
                            conn.commit(); st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()

        # ==================== تبويب التصحيح ====================
        with t_cor:
            if get_form_status('تصحيح'):
                c_row = found_data["correction"]
                with st.form(key="cor_form"):
                    c1, c2 = st.columns(2)
                    c_id = c2.text_input("رقم الهوية *", value=search_id if search_id else "")
                    c_name = c1.text_input("الاسم الرباعي *", value=get_val(c_row, 2))
                    c_phone = c1.text_input("الجوال *", value=get_val(c_row, 10))
                    
                    branches = ["", "علمي", "أدبي", "تجاري", "صناعي", "فندقي", "زراعي", "اقتصاد منزلي"]
                    c_branch = c1.selectbox("الفرع *", branches, index=branches.index(c_row[6]) if c_row else 0)
                    
                    subjects = ["", "اللغة العربية", "اللغة الإنجليزية", "الرياضيات", "التربية الإسلامية", "الفيزياء", "الكيمياء", "الأحياء", "تكنولوجيا المعلومات", "التاريخ", "الجغرافيا","الثقافة العلمية"]
                    c_subj = c2.selectbox("المبحث *", subjects, index=subjects.index(c_row[5]) if c_row else 0)
                    
                    if st.form_submit_button("💾 حفظ/تحديث التصحيح"):
                        if validate_inputs(c_id, c_phone):
                            if c_row:
                                c.execute("UPDATE correction_table SET name=?, phone=?, subject=?, branch=? WHERE id_num=? AND school_user=?",
                                          (c_name, c_phone, c_subj, c_branch, c_id, st.session_state['school_user']))
                            else:
                                c.execute("INSERT INTO correction_table (id_num, name, school_user, school_full_name, subject, branch, phone) VALUES (?,?,?,?,?,?,?)",
                                          (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subj, c_branch, c_phone))
                            conn.commit(); st.success("✅ تم الحفظ"); time.sleep(1); st.rerun()

    elif st.session_state.menu_choice == "التقارير":
        st.subheader("📊 سجلات المدرسة الموثقة")
        report_type = st.selectbox("اختر النظام لعرض التقرير:", ["الكل", "الثانوية العامة", "امتحان التوظيف", "التصحيح"], key=f"report_filter_{st.session_state.reset_key}")
        
        if report_type in ["الكل", "الثانوية العامة", "امتحان التوظيف"]:
            df1 = pd.read_sql_query("SELECT * FROM main_table WHERE school_user=?", conn, params=(st.session_state['school_user'],))
            if report_type == "الثانوية العامة": df1 = df1[df1['type'] == "الثانوية العامة"]
            elif report_type == "امتحان التوظيف": df1 = df1[df1['type'] == "امتحان التوظيف"]
            if not df1.empty: 
                st.info("🔹 كشف المراقبة والتوظيف")
                d1 = df1.drop(columns=['id', 'school_user', 'school_full_name']).copy()
                d1.insert(0, 'الرقم', range(1, len(d1) + 1))
                st.dataframe(d1.rename(columns=COLUMN_NAMES_MAP), use_container_width=True, hide_index=True)
                
                # ✅ زر تحميل إكسل منسق للتوظيف/الثانوية
                st.download_button(
                    label="📥 تحميل كشف المراقبة/التوظيف (إكسل منسق)",
                    data=to_excel_formatted(df1, "كشف المراقبة والتوظيف", st.session_state['school_display_name']),
                    file_name=f"{st.session_state['school_display_name']}_مراقبة_توظيف.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_main_{st.session_state.reset_key}"
                )
        
        if report_type in ["الكل", "التصحيح"]:
            df2 = pd.read_sql_query("SELECT * FROM correction_table WHERE school_user=?", conn, params=(st.session_state['school_user'],))
            if not df2.empty: 
                if report_type != "الكل": st.divider()
                st.success("🔹 كشف التصحيح")
                d2 = df2.drop(columns=['id', 'school_user', 'school_full_name']).copy()
                d2.insert(0, 'الرقم', range(1, len(d2) + 1))
                st.dataframe(d2.rename(columns=COLUMN_NAMES_MAP), use_container_width=True, hide_index=True)
                
                # ✅ زر تحميل إكسل منسق للتصحيح
                st.download_button(
                    label="📥 تحميل كشف التصحيح (إكسل منسق)",
                    data=to_excel_formatted(df2, "كشف التصحيح", st.session_state['school_display_name']),
                    file_name=f"{st.session_state['school_display_name']}_تصحيح.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_cor_{st.session_state.reset_key}"
                )

# --- شاشة الإدارة ---
elif st.session_state['user_type'] == "admin":
    adm_nav1, adm_nav2, adm_nav3, adm_nav4 = st.columns([1, 1, 2, 1])
    with adm_nav1:
        if st.button("📂 إدارة البيانات", use_container_width=True): st.session_state.menu_choice = "إدارة البيانات"
    with adm_nav2:
        if st.button("⚙️ صلاحيات النماذج", use_container_width=True): st.session_state.menu_choice = "صلاحيات النماذج"
    with adm_nav4:
        if st.button("🚪 تسجيل الخروج", use_container_width=True): st.session_state.clear(); st.rerun()

    st.title("🛠️ لوحة تحكم الإدارة المركزية")
    
    if st.session_state.menu_choice == "صلاحيات النماذج":
        cols = st.columns(3)
        for i, f in enumerate(['ثانوية', 'توظيف', 'تصحيح']):
            with cols[i]:
                curr = get_form_status(f); st.write(f"نموذج {f}: {'✅ مفتوح' if curr else '❌ مغلق'}")
                if st.button(f"تغيير حالة {f}", key=f"at_{f}_{st.session_state.reset_key}"): 
                    c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (0 if curr else 1, f)); conn.commit(); st.rerun()
    else:
        t1, t2, t3 = st.tabs(["الثانوية العامة", "امتحان التوظيف", "التصحيح"])
        def view_admin(t_name, d_type, k_s, is_c=False):
            df = pd.read_sql_query("SELECT * FROM correction_table", conn) if is_c else pd.read_sql_query("SELECT * FROM main_table WHERE type=?", conn, params=(d_type,))
            if not is_c and not df.empty:
                dup_filter = st.checkbox(f"✅ عرض المكررين فقط ({t_name})", key=f"dup_{k_s}_{st.session_state.reset_key}", help="عرض الأرقام المسجلة في أكثر من مدرسة")
                if dup_filter:
                    dup_ids = df.groupby('id_num').filter(lambda x: x['school_full_name'].nunique() > 1)['id_num'].unique()
                    df = df[df['id_num'].isin(dup_ids)]
            sel = st.selectbox(f"اختر مدرسة ({t_name}):", ["الكل"] + sorted(df['school_full_name'].dropna().unique().tolist()) if not df.empty else ["الكل"], key=f"s_{k_s}_{st.session_state.reset_key}")
            f_df = df if sel == "الكل" else df[df['school_full_name'] == sel]
            if not f_df.empty:
                admin_disp = f_df.drop(columns=['id']).copy()
                admin_disp.insert(0, 'الرقم', range(1, len(admin_disp) + 1))
                st.dataframe(admin_disp.rename(columns=COLUMN_NAMES_MAP), use_container_width=True, hide_index=True)
                
                st.write("🗑️ **لحذف سجل محدد يدوياً:**")
                col_del1, col_del2, col_del3 = st.columns([3, 3, 1])
                with col_del1: del_id = st.text_input("رقم الهوية:", key=f"del_id_{k_s}_{st.session_state.reset_key}")
                with col_del2: del_school = st.selectbox("المدرسة:", ["الكل"] + list(f_df['school_full_name'].dropna().unique()), key=f"del_sch_{k_s}_{st.session_state.reset_key}")
                with col_del3:
                    if st.button("حذف", key=f"btn_del_{k_s}_{st.session_state.reset_key}"):
                        if del_id:
                            try:
                                if del_school == "الكل": c.execute("DELETE FROM correction_table WHERE id_num=?" if is_c else "DELETE FROM main_table WHERE id_num=?", (del_id,))
                                else: c.execute("DELETE FROM correction_table WHERE id_num=? AND school_full_name=?" if is_c else "DELETE FROM main_table WHERE id_num=? AND school_full_name=?", (del_id, del_school))
                                conn.commit(); st.success("✅ تم حذف السجل"); time.sleep(1); st.rerun()
                            except Exception as e: st.error(f"❌ خطأ: {str(e)}")
                st.download_button(label=f"📥 تحميل ({t_name})", data=to_excel_formatted(f_df, t_name, ""), file_name=f'admin_{k_s}.xlsx')
            else: st.info("لا توجد بيانات لعرضها")
        
        with t1: view_admin("الثانوية العامة", "الثانوية العامة", "tw")
        with t2: view_admin("امتحان التوظيف", "امتحان التوظيف", "em")
        with t3: view_admin("تصحيح", "", "cr", True)

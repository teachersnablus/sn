import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
import time

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام قسم الإمتحانات مديرية جنوب نابلس", layout="wide")

st.markdown("""
    <style>
        /* تثبيت الترويسة العلوي */
        .custom-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #1a1c23;
            color: white;
            text-align: center;
            padding: 15px 0;
            z-index: 9999;
            border-bottom: 2px solid #00ffcc;
            line-height: 1.5;
            direction: rtl;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        }
        
        /* إخفاء القائمة الجانبية بالكامل */
        [data-testid="stSidebar"] {
            display: none;
        }

        /* إزاحة محتوى التطبيق لأسفل */
        .stApp {
            margin-top: 80px;
        }

        header {visibility: hidden;}

        /* تنسيقات الخط والاتجاه */
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
        
        .school-title { 
            color: #ffffff; 
            background-color: #1E3A8A; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center; 
            font-size: 26px !important; 
            font-weight: bold; 
            margin-top: 20px;
            margin-bottom: 20px; 
        }
        .search-row-label {
            font-size: 20px !important;
            font-weight: bold;
            color: #ffffff; 
            background-color: #1E3A8A; 
            padding: 10px 15px;
            border-radius: 8px;
            text-align: center;
        }
        .note-box {
            background-color: #fff3cd;
            border: 2px solid #ffc107;
            color: #856404;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 15px;
        }
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

# --- قائمة المناطق السكنية ---
RESIDENCE_AREAS = [
    "", "نابلس", "رام الله", "سلفيت", "طولكرم", "عورتا", "أودلا", "بيتا", "عقربا", 
    "مجدل بني فاضل", "دوما", "قريوت", "جالود", "تلفيت", "قصرة", "جوريش", "قبلان", 
    "يتما", "اللبن", "الساوية", "جماعين", "زيتا", "عوريف", "عصيرة القبلية", "بورين", 
    "مادما","عينابوس","حوارة", "يانون", "أوصرين"
]

# --- خيارات الجنس ---
GENDER_OPTIONS = ["", "ذكر", "أنثى"]

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_final_v31.db", check_same_thread=False)
c = conn.cursor()

# ✅ هيكل الجداول الجديد: PRIMARY KEY = id (تلقائي) للسماح بتسجيلات متعددة لنفس الهوية
c.execute('''CREATE TABLE IF NOT EXISTS main_table 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              id_num TEXT, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, 
              phone TEXT, address TEXT, relative_exam TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT, type TEXT, gender TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS correction_table 
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              id_num TEXT, name TEXT, school_user TEXT, school_full_name TEXT, 
              subject TEXT, branch TEXT, address TEXT, 
              has_relative TEXT, relative_details TEXT, phone TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS system_settings (form_name TEXT PRIMARY KEY, is_open INTEGER)''')
for form in ['ثانوية', 'توظيف', 'تصحيح']:
    c.execute("INSERT OR IGNORE INTO system_settings VALUES (?, 1)", (form,))
conn.commit()

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

# --- تهيئة session state ---
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
if 'auth' not in st.session_state: 
    st.session_state.update({
        'auth': False, 'school_display_name': "", 'school_user': "", 
        'user_type': "", 'menu_choice': "إضافة"
    })

# --- تهيئة متغيرات القريب المباشر في الجلسة (للتوظيف والتصحيح فقط) ---
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

def get_index_safe(options_list, value):
    if value in options_list:
        return options_list.index(value)
    return 0

# --- 3. تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة تجميع المراقبة والتصحيح مديرية التربية والتعليم - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول القسم"])
    
    with tab1:
        with st.form(key="school_login_form"):
            u_in = st.text_input("رقم المدرسة", key="school_user_input").strip()
            p_in = st.text_input("كلمة المرور", type="password", key="school_pass_input").strip()
            login_submitted = st.form_submit_button("دخول المدارس")
            
            if login_submitted:
                df_acc = load_accounts()
                if df_acc is not None and not df_acc.empty:
                    match = df_acc[(df_acc['school_user'].astype(str) == u_in) & (df_acc['password'].astype(str) == p_in)]
                    if not match.empty:
                        st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u_in, 'school_display_name': str(match.iloc[0]['school_full_name'])})
                        st.rerun()
                    else: st.error("❌ بيانات الحساب خاطئة")
                else: st.error("❌ فشل الاتصال - يرجى المحاولة مرة أخرى")
                
    with tab2:
        with st.form(key="admin_login_form"):
            adm_pass = st.text_input("كلمة مرور القسم", type="password", key="admin_pass_input")
            admin_submitted = st.form_submit_button("دخول القسم")
            
            if admin_submitted:
                if adm_pass == "ADMIN2026":
                    # ✅ إصلاح 1: إغلاق علامة التنصيص بشكل صحيح
                    st.session_state.update({'auth': True, 'user_type': "admin", 'menu_choice': "إدارة البيانات"})
                    st.rerun()
                else: st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- شاشة المدارس ---
if st.session_state['user_type'] == "school":
    # أزرار التنقل العلوية
    nav1, nav2, nav3, nav4 = st.columns([1, 1, 2, 1])
    with nav1:
        if st.button("➕ إضافة بيانات", use_container_width=True):
            st.session_state.menu_choice = "إضافة"
    with nav2:
        if st.button("📊 التقارير", use_container_width=True):
            st.session_state.menu_choice = "التقارير"
    with nav4:
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)

    if st.session_state.menu_choice == "إضافة":
        col_lbl, col_inp = st.columns([1.2, 3])
        with col_lbl: st.markdown("<div class='search-row-label'>🔍 بحث برقم الهوية للتعديل</div>", unsafe_allow_html=True)
        with col_inp: search_id = st.text_input("", placeholder="أدخل رقم الهوية...", key=f"search_{st.session_state.reset_key}", label_visibility="collapsed").strip()
        
        found_rows = pd.DataFrame()
        
        if search_id and len(search_id) == 9 and search_id.isdigit():
            df_m = pd.read_sql_query("SELECT *, 'main' as tbl FROM main_table WHERE id_num=? AND school_user=?", conn, params=(search_id, st.session_state['school_user']))
            df_c = pd.read_sql_query("SELECT *, 'correction' as tbl FROM correction_table WHERE id_num=? AND school_user=?", conn, params=(search_id, st.session_state['school_user']))
            
            if not df_m.empty or not df_c.empty:
                found_rows = pd.concat([df_m, df_c], ignore_index=True)
                st.success(f"✅ تم العثور على {len(found_rows)} سجل(سجلات) للموظف")
            else:
                st.info("ℹ️ الرقم متاح للتسجيل.")

        if isinstance(found_rows, pd.DataFrame) and not found_rows.empty:
            if st.button("🗑️ حذف جميع السجلات لهذا الرقم من مدرستك"):
                c.execute("DELETE FROM main_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user']))
                c.execute("DELETE FROM correction_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user']))
                conn.commit()
                st.session_state.reset_key += 1
                st.success("✅ تم الحذف")
                time.sleep(1)
                st.rerun()

        st.divider()
        t_sec, t_job, t_cor = st.tabs(["📝 الثانوية العامة", "📋 امتحان التوظيف", "✍️ التصحيح"])
        
        # ==================== تبويب الثانوية العامة ====================
        with t_sec:
            if get_form_status('ثانوية'):
                with st.form(key=f"sec_form_{st.session_state.reset_key}"):
                    # ✅ الملاحظة تظهر في أعلى النموذج فوق رقم الهوية
                    st.markdown('<div class="note-box">📋 ملاحظة هامة: تعبأ بيانات المعلم الذي ليس له قريب مباشر فقط</div>', unsafe_allow_html=True)
                    
                    c1, c2 = st.columns(2)
                    id_num = c2.text_input("رقم الهوية (9 أرقام) *", value=search_id if search_id else "", key=f"sec_id_{st.session_state.reset_key}")
                    name = c1.text_input("الاسم رباعي *", value="", key=f"sec_name_{st.session_state.reset_key}")
                    phone = c1.text_input("رقم الجوال (10 أرقام) *", value="", key=f"sec_phone_{st.session_state.reset_key}")
                    address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=0, key=f"sec_addr_{st.session_state.reset_key}")
                    job_list = ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"]
                    job = c1.selectbox("الوظيفة *", job_list, index=0, key=f"sec_job_{st.session_state.reset_key}")
                    gender = c2.selectbox("الجنس *", GENDER_OPTIONS, index=0, key=f"sec_gender_{st.session_state.reset_key}")
                    
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية (إن وجدت)", value="", key=f"sec_school2_{st.session_state.reset_key}")
                    
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], horizontal=True, key=f"desire_sec_{st.session_state.reset_key}")
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True, key=f"note_sec_{st.session_state.reset_key}")
                    
                    if st.form_submit_button("💾 حفظ بيانات الثانوية"):
                        if not (name and id_num and phone and address and job and gender): 
                            st.error("⚠️ يرجى تعبئة جميع الحقول الإجبارية")
                        elif validate_inputs(id_num, phone):
                            try:
                                # ✅ في الثانوية: relative_exam يُحفظ فارغ دائماً (لا نأخذ بيانات من له قريب)
                                c.execute("""INSERT INTO main_table 
                                            (id_num, name, school_user, school_full_name, school2, phone, address, relative_exam, job_title, desire, principal_note, type, gender) 
                                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                                        (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], 
                                         school2, phone, address, "", job, desire, note, "الثانوية العامة", gender))
                                conn.commit()
                                st.success("✅ تم الحفظ بنجاح")
                                st.session_state.reset_key += 1
                                time.sleep(1)
                                st.rerun()
                            except sqlite3.IntegrityError as e:
                                st.error(f"❌ خطأ في قاعدة البيانات: {str(e)}")
                            except Exception as e:
                                st.error(f"❌ خطأ غير متوقع: {str(e)}")

        # ==================== تبويب امتحان التوظيف ====================
        with t_job:
            if get_form_status('توظيف'):
                # ✅ إصلاح 2: نقل خيار القريب خارج الـ form ليظهر الحقل فوراً
                st.session_state.has_rel_job = st.radio(
                    "هل له قريب مباشر يتقدم للامتحان؟", 
                    ["لا يوجد", "يوجد"], 
                    horizontal=True, 
                    key=f"rel_job_{st.session_state.reset_key}",
                    index=0 if st.session_state.has_rel_job == "لا يوجد" else 1
                )
                
                with st.form(key=f"job_form_{st.session_state.reset_key}"):
                    c1, c2 = st.columns(2)
                    id_num = c2.text_input("رقم الهوية (9 أرقام) *", value=search_id if search_id else "", key=f"job_id_{st.session_state.reset_key}")
                    name = c1.text_input("الاسم رباعي *", value="", key=f"job_name_{st.session_state.reset_key}")
                    phone = c1.text_input("رقم الجوال (10 أرقام) *", value="", key=f"job_phone_{st.session_state.reset_key}")
                    address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=0, key=f"job_addr_{st.session_state.reset_key}")
                    job_list = ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"]
                    job = c1.selectbox("الوظيفة *", job_list, index=0, key=f"job_title_sel_{st.session_state.reset_key}")
                    gender = c2.selectbox("الجنس *", GENDER_OPTIONS, index=0, key=f"job_gender_{st.session_state.reset_key}")
                    
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية (إن وجدت)", value="", key=f"job_school2_{st.session_state.reset_key}")
                    
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], horizontal=True, key=f"d_job_{st.session_state.reset_key}")
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True, key=f"n_job_{st.session_state.reset_key}")
                    
                    # ✅ إظهار حقل القريب بناءً على قيمة الجلسة (يظهر فوراً لأن الشرط خارج الـ form)
                    if st.session_state.has_rel_job == "يوجد":
                        rel_exam = st.text_input("اسم القريب المباشر *", value="", key=f"rel_exam_job_{st.session_state.reset_key}")
                    else:
                        rel_exam = ""
                    
                    if st.form_submit_button("💾 حفظ بيانات التوظيف"):
                        if not (name and id_num and phone and address and job and gender): 
                            st.error("⚠️ يرجى تعبئة جميع الحقول الإجبارية")
                        elif st.session_state.has_rel_job == "يوجد" and not rel_exam:
                            st.error("⚠️ يرجى إدخال اسم القريب المباشر")
                        elif validate_inputs(id_num, phone):
                            try:
                                rel_exam_safe = rel_exam if rel_exam else ""
                                c.execute("""INSERT INTO main_table 
                                            (id_num, name, school_user, school_full_name, school2, phone, address, relative_exam, job_title, desire, principal_note, type, gender) 
                                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                        (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'],
                                         school2, phone, address, rel_exam_safe, job, desire, note, "امتحان التوظيف", gender))
                                conn.commit()
                                st.success("✅ تم الحفظ بنجاح")
                                st.session_state.reset_key += 1
                                time.sleep(1)
                                st.rerun()
                            except sqlite3.IntegrityError as e:
                                st.error(f"❌ خطأ في قاعدة البيانات: {str(e)}")
                            except Exception as e:
                                st.error(f"❌ خطأ غير متوقع: {str(e)}")

        # ==================== تبويب التصحيح ====================
        with t_cor:
            if get_form_status('تصحيح'):
                # ✅ خيار القريب خارج الـ form ليظهر الحقل فوراً
                st.session_state.has_rel_cor = st.radio(
                    "هل له قريب مباشر يتقدم للامتحان؟", 
                    ["لا يوجد", "يوجد"], 
                    horizontal=True, 
                    key=f"rel_cor_{st.session_state.reset_key}",
                    index=0 if st.session_state.has_rel_cor == "لا يوجد" else 1
                )
                
                with st.form(key=f"c_form_{st.session_state.reset_key}"):
                    c1, c2 = st.columns(2)
                    c_id = c2.text_input("رقم الهوية (9 أرقام) *", value=search_id if search_id else "", key=f"cor_id_{st.session_state.reset_key}")
                    c_name = c1.text_input("الاسم الرباعي *", value="", key=f"cor_name_{st.session_state.reset_key}")
                    c_phone = c1.text_input("الجوال (10 أرقام) *", value="", key=f"cor_phone_{st.session_state.reset_key}")
                    c_address = c2.selectbox("مكان السكن *", RESIDENCE_AREAS, index=0, key=f"cor_addr_{st.session_state.reset_key}")
                    branch_list = ["", "علمي", "أدبي", "تجاري", "صناعي", "فندقي", "زراعي", "اقتصاد منزلي"]
                    c_branch = c1.selectbox("الفرع *", branch_list, index=0, key=f"cor_branch_{st.session_state.reset_key}")
                    sub_list = ["", "اللغة العربية", "اللغة الإنجليزية", "الرياضيات", "التربية الإسلامية", "الفيزياء", "الكيمياء", "الأحياء", "تكنولوجيا المعلومات", "التاريخ", "الجغرافيا","الثقافة العلمية", "فرع (الريادة و الأعمال) - مباحث التخصص", "فرع (الاقتصاد المنزلي) - مباحث التخصص",  "الفروع المهنية (الصناعي ) - مباحث التخصص", "الفروع المهنية (الزراعي) - مباحث التخصص"]
                    c_subj = c2.selectbox("المبحث *", sub_list, index=0, key=f"cor_subj_{st.session_state.reset_key}")
                    st.divider()
                    
                    # ✅ إظهار حقل القريب في التصحيح بناءً على قيمة الجلسة
                    if st.session_state.has_rel_cor == "يوجد":
                        rel_details = st.text_input("اسم القريب *", value="", key=f"rel_det_cor_{st.session_state.reset_key}")
                    else:
                        rel_details = ""
                    
                    if st.form_submit_button("💾 حفظ بيانات التصحيح"):
                        if not (c_name and c_id and c_phone and c_address and c_subj and c_branch): 
                            st.error("⚠️ يرجى اختيار المبحث والفرع وتعبئة الحقول")
                        elif st.session_state.has_rel_cor == "يوجد" and not rel_details:
                            st.error("⚠️ يرجى إدخال اسم القريب المباشر")
                        elif validate_inputs(c_id, c_phone):
                            try:
                                rel_details_safe = rel_details if rel_details else ""
                                c.execute("""INSERT INTO correction_table 
                                            (id_num, name, school_user, school_full_name, subject, branch, address, has_relative, relative_details, phone) 
                                            VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                                        (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], 
                                         c_subj, c_branch, c_address, st.session_state.has_rel_cor, rel_details_safe, c_phone))
                                conn.commit()
                                st.success("✅ تم الحفظ بنجاح")
                                st.session_state.reset_key += 1
                                time.sleep(1)
                                st.rerun()
                            except sqlite3.IntegrityError as e:
                                st.error(f"❌ خطأ في قاعدة البيانات: {str(e)}")
                            except Exception as e:
                                st.error(f"❌ خطأ غير متوقع: {str(e)}")

    elif st.session_state.menu_choice == "التقارير":
        st.subheader("📊 سجلات المدرسة الموثقة")
        
        # ✅ التعديل 4: إضافة فلتر لاختيار النظام المطلوب عرض تقريره
        report_type = st.selectbox("اختر النظام لعرض التقرير:", ["الكل", "الثانوية العامة", "امتحان التوظيف", "التصحيح"], key=f"report_filter_{st.session_state.reset_key}")
        
        if report_type in ["الكل", "الثانوية العامة", "امتحان التوظيف"]:
            df1 = pd.read_sql_query("SELECT * FROM main_table WHERE school_user=?", conn, params=(st.session_state['school_user'],))
            if report_type == "الثانوية العامة":
                df1 = df1[df1['type'] == "الثانوية العامة"]
            elif report_type == "امتحان التوظيف":
                df1 = df1[df1['type'] == "امتحان التوظيف"]
            
            if not df1.empty: 
                st.info("🔹 كشف المراقبة والتوظيف")
                st.dataframe(df1.drop(columns=['school_user','school_full_name']), use_container_width=True)
        
        if report_type in ["الكل", "التصحيح"]:
            df2 = pd.read_sql_query("SELECT * FROM correction_table WHERE school_user=?", conn, params=(st.session_state['school_user'],))
            if not df2.empty: 
                if report_type != "الكل": st.divider()
                st.success("🔹 كشف التصحيح")
                st.dataframe(df2[['id_num','name','address','branch','subject']], use_container_width=True)

# --- شاشة الإدارة ---
elif st.session_state['user_type'] == "admin":
    # أزرار التنقل العلوية للقسم
    adm_nav1, adm_nav2, adm_nav3, adm_nav4 = st.columns([1, 1, 2, 1])
    with adm_nav1:
        if st.button("📂 إدارة البيانات", use_container_width=True):
            st.session_state.menu_choice = "إدارة البيانات"
    with adm_nav2:
        if st.button("⚙️ صلاحيات النماذج", use_container_width=True):
            st.session_state.menu_choice = "صلاحيات النماذج"
    with adm_nav4:
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.title("🛠️ لوحة تحكم الإدارة المركزية")
    
    if st.session_state.menu_choice == "صلاحيات النماذج":
        cols = st.columns(3)
        for i, f in enumerate(['ثانوية', 'توظيف', 'تصحيح']):
            with cols[i]:
                curr = get_form_status(f)
                st.write(f"نموذج {f}: {'✅ مفتوح' if curr else '❌ مغلق'}")
                if st.button(f"تغيير حالة {f}", key=f"at_{f}_{st.session_state.reset_key}"): 
                    c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (0 if curr else 1, f))
                    conn.commit()
                    st.rerun()
    else:
        t1, t2, t3 = st.tabs(["الثانوية العامة", "امتحان التوظيف", "التصحيح"])
        
        def view_admin(t_name, d_type, k_s, is_c=False):
            df = pd.read_sql_query("SELECT * FROM correction_table", conn) if is_c else pd.read_sql_query("SELECT * FROM main_table WHERE type=?", conn, params=(d_type,))
            
            # ✅ التعديل 1: إضافة فلتر للمكررين (نفس id_num في مدارس مختلفة)
            if not is_c and not df.empty:
                dup_filter = st.checkbox(f"✅ عرض المكررين فقط ({t_name})", key=f"dup_{k_s}_{st.session_state.reset_key}", help="عرض الأرقام المسجلة في أكثر من مدرسة")
                if dup_filter:
                    dup_ids = df.groupby('id_num').filter(lambda x: x['school_full_name'].nunique() > 1)['id_num'].unique()
                    df = df[df['id_num'].isin(dup_ids)]
            
            sel = st.selectbox(f"اختر مدرسة ({t_name}):", ["الكل"] + sorted(df['school_full_name'].dropna().unique().tolist()) if not df.empty else ["الكل"], key=f"s_{k_s}_{st.session_state.reset_key}")
            f_df = df if sel == "الكل" else df[df['school_full_name'] == sel]
            
            # ✅ التعديل 1: إضافة واجهة للحذف اليدوي لسجل محدد
            if not f_df.empty:
                st.dataframe(f_df, use_container_width=True)
                st.write("🗑️ **لحذف سجل محدد يدوياً:**")
                col_del1, col_del2, col_del3 = st.columns([3, 3, 1])
                with col_del1:
                    del_id = st.text_input("رقم الهوية:", key=f"del_id_{k_s}_{st.session_state.reset_key}")
                with col_del2:
                    del_school = st.selectbox("المدرسة:", ["الكل"] + list(f_df['school_full_name'].dropna().unique()), key=f"del_sch_{k_s}_{st.session_state.reset_key}")
                with col_del3:
                    if st.button("حذف", key=f"btn_del_{k_s}_{st.session_state.reset_key}"):
                        if del_id:
                            try:
                                if del_school == "الكل":
                                    c.execute("DELETE FROM correction_table WHERE id_num=?" if is_c else "DELETE FROM main_table WHERE id_num=?", (del_id,))
                                else:
                                    c.execute("DELETE FROM correction_table WHERE id_num=? AND school_full_name=?" if is_c else "DELETE FROM main_table WHERE id_num=? AND school_full_name=?", (del_id, del_school))
                                conn.commit()
                                st.success("✅ تم حذف السجل")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ خطأ: {str(e)}")
            else:
                st.info("لا توجد بيانات لعرضها")
            
            st.download_button(label=f"📥 تحميل ({t_name})", data=to_excel(f_df), file_name=f'admin_{k_s}.xlsx')
        
        with t1: view_admin("الثانوية العامة", "الثانوية العامة", "tw")
        with t2: view_admin("امتحان التوظيف", "امتحان التوظيف", "em")
        with t3: view_admin("تصحيح", "", "cr", True)

import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام مديرية جنوب نابلس 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    input, select, textarea { direction: rtl !important; text-align: right !important; }
    .school-title { color: #ffffff; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 25px; }
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# رابط ملف الحسابات
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_pro_2026.db", check_same_thread=False)
c = conn.cursor()

# الجداول الأساسية
c.execute('''CREATE TABLE IF NOT EXISTS main_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, 
              phone TEXT, city TEXT, village TEXT, relative_exam TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT, type TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS correction_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, 
              subject TEXT, branch TEXT, city TEXT, village TEXT, 
              has_relative TEXT, relative_details TEXT, phone TEXT)''')

# جدول التحكم في الصلاحيات (فتح/إغلاق النماذج)
c.execute('''CREATE TABLE IF NOT EXISTS system_settings (form_name TEXT PRIMARY KEY, is_open INTEGER)''')
# تعبئة القيم الافتراضية إذا كانت فارغة
for form in ['ثانوية', 'توظيف', 'تصحيح']:
    c.execute("INSERT OR IGNORE INTO system_settings VALUES (?, 1)", (form,))
conn.commit()

# --- 3. وظائف مساعدة ---
def get_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else False

# --- 4. تهيئة الجلسة ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

# --- 5. واجهة تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم (رقم المدرسة)").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("دخول"):
            try:
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                df_acc.columns = df_acc.columns.str.strip()
                match = df_acc[(df_acc['school_user'].astype(str) == u_input) & (df_acc['password'].astype(str) == p_input)]
                if not match.empty:
                    st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u_input, 'school_display_name': str(match.iloc[0].get('school_full_name', u_input))})
                    st.rerun()
                else: st.error("❌ بيانات خاطئة")
            except: st.error("❌ خطأ في الاتصال")
    
    with tab2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول المسؤول"):
                st.session_state.auth, st.session_state.user_type = True, "admin"
                st.rerun()
    st.stop()

# --- 6. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    if st.sidebar.button("تسجيل الخروج"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    menu = st.sidebar.radio("القائمة:", ["تعبئة نماذج جديدة", "استعراض وتعديل بياناتنا"])

    if menu == "تعبئة نماذج جديدة":
        # فحص الحالة من قاعدة البيانات
        can_tawjihi = get_status('ثانوية')
        can_employment = get_status('توظيف')
        can_correct = get_status('تصحيح')

        available_forms = []
        if can_tawjihi: available_forms.append("الثانوية العامة")
        if can_employment: available_forms.append("امتحان التوظيف")
        
        tab_m, tab_c = st.tabs(["📋 مراقبة وتوظيف", "✍️ تصحيح الثانوية العامة"])

        with tab_m:
            if not available_forms:
                st.warning("⚠️ عذراً، نماذج المراقبة والتوظيف مغلقة حالياً من قبل الإدارة.")
            else:
                mode = st.radio("نوع النموذج:", available_forms, horizontal=True)
                with st.form("form_main", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("الاسم رباعي")
                        id_num = st.text_input("رقم الهوية")
                        phone = st.text_input("رقم الجوال")
                    with col2:
                        city = st.text_input("المدينة")
                        village = st.text_input("القرية")
                        job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
                    
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية")
                    rel_exam = st.text_input("امتحان القريب المباشر")
                    
                    desire, note = "", ""
                    if mode == "الثانوية العامة":
                        e1, e2 = st.columns(2)
                        with e1: desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], horizontal=True)
                        with e2: note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True)
                    else: desire = "توظيف"

                    if st.form_submit_button("💾 حفظ"):
                        if name and id_num:
                            c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                      (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, city, village, rel_exam, job, desire, note, mode))
                            conn.commit()
                            st.success("✅ تم الحفظ")
                        else: st.error("⚠️ أكمل البيانات")

        with tab_c:
            if can_correct:
                with st.form("form_correct", clear_on_submit=True):
                    # (نفس حقول التصحيح السابقة)
                    f1, f2 = st.columns(2)
                    with f1:
                        c_name = st.text_input("الاسم الرباعي ")
                        c_id = st.text_input("رقم الهوية ")
                        c_subject = st.selectbox("المبحث", ["اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم الحياتية", "الكيمياء", "الفيزياء", "الثقافة العلمية", "تكنولوجيا المعلومات", "التاريخ", "الجغرافيا", "التربية الدينية", "مباحث التخصص الأخرى"])
                    with f2:
                        c_city = st.text_input("المدينة ")
                        c_village = st.text_input("القرية ")
                        c_branch = st.selectbox("الفرع", ["الأدبي", "العلمي", "الريادة", "الزراعي", "الصناعي", "الاقتصاد المنزلي"])
                    
                    c_phone = st.text_input("الجوال")
                    has_rel = st.radio("قريب مباشر؟", ["لا", "نعم"], horizontal=True)
                    rel_info = st.text_input("التفاصيل (الاسم والعلاقة) في حال نعم")

                    if st.form_submit_button("💾 حفظ طلب التصحيح"):
                        if c_name and c_id:
                            c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                      (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subject, c_branch, c_city, c_village, has_rel, rel_info, c_phone))
                            conn.commit()
                            st.success("✅ تم الحفظ")
            else:
                st.warning("⚠️ نموذج التصحيح مغلق حالياً.")

    elif menu == "استعراض وتعديل بياناتنا":
        st.subheader("🔍 مراجعة البيانات المرسلة من قبل مدرستكم")
        
        # استعراض المراقبة والتوظيف للمدرسة الحالية فقط
        df_m = pd.read_sql(f"SELECT * FROM main_table WHERE school_user='{st.session_state['school_user']}'", conn)
        if not df_m.empty:
            st.write("📊 المراقبة والتوظيف:")
            st.dataframe(df_m)
            id_to_del = st.selectbox("اختر رقم الهوية للحذف (مراقبة/توظيف):", [""] + df_m['id_num'].tolist())
            if st.button("❌ حذف السجل المختار"):
                c.execute(f"DELETE FROM main_table WHERE id_num='{id_to_del}'")
                conn.commit()
                st.rerun()
        
        # استعراض التصحيح للمدرسة الحالية
        df_c = pd.read_sql(f"SELECT * FROM correction_table WHERE school_user='{st.session_state['school_user']}'", conn)
        if not df_c.empty:
            st.divider()
            st.write("✍️ سجلات التصحيح:")
            st.dataframe(df_c)

# --- 7. لوحة الإدارة ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ التحكم المركزي - جنوب نابلس")
    if st.sidebar.button("تسجيل الخروج"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    adm_menu = st.sidebar.selectbox("الانتقال إلى:", ["لوحة التحكم والصلاحيات", "عرض وتعديل البيانات"])

    if adm_menu == "لوحة التحكم والصلاحيات":
        st.header("🔓 فتح وإغلاق استقبال الطلبات")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("الثانوية العامة")
            st.write("الحالة:", "مفتوح ✅" if get_status('ثانوية') else "مغلق ❌")
            if st.button("تغيير حالة الثانوية"):
                new_st = 0 if get_status('ثانوية') else 1
                c.execute("UPDATE system_settings SET is_open=? WHERE form_name='ثانوية'", (new_st,))
                conn.commit()
                st.rerun()

        with col2:
            st.info("امتحان التوظيف")
            st.write("الحالة:", "مفتوح ✅" if get_status('توظيف') else "مغلق ❌")
            if st.button("تغيير حالة التوظيف"):
                new_st = 0 if get_status('توظيف') else 1
                c.execute("UPDATE system_settings SET is_open=? WHERE form_name='توظيف'", (new_st,))
                conn.commit()
                st.rerun()

        with col3:
            st.info("التصحيح")
            st.write("الحالة:", "مفتوح ✅" if get_status('تصحيح') else "مغلق ❌")
            if st.button("تغيير حالة التصحيح"):
                new_st = 0 if get_status('تصحيح') else 1
                c.execute("UPDATE system_settings SET is_open=? WHERE form_name='تصحيح'", (new_st,))
                conn.commit()
                st.rerun()

    else:
        tab1, tab2, tab3 = st.tabs(["المراقبة", "التوظيف", "التصحيح"])
        
        with tab1:
            df = pd.read_sql("SELECT * FROM main_table WHERE type='الثانوية العامة'", conn)
            st.dataframe(df)
            id_del = st.text_input("أدخل رقم الهوية للحذف نهائياً (مراقبة):")
            if st.button("حذف السجل"):
                c.execute(f"DELETE FROM main_table WHERE id_num='{id_del}'")
                conn.commit()
                st.success("تم الحذف")
                st.rerun()

        with tab2:
            df = pd.read_sql("SELECT * FROM main_table WHERE type='امتحان التوظيف'", conn)
            st.dataframe(df)

        with tab3:
            df = pd.read_sql("SELECT * FROM correction_table", conn)
            st.dataframe(df)

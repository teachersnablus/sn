import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام جنوب نابلس 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    input, select, textarea { direction: rtl !important; text-align: right !important; }
    .school-title { color: #ffffff; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# رابط جوجل شيت الحسابات
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_2026.db", check_same_thread=False)
c = conn.cursor()

# جدول المراقبة والتوظيف
c.execute('''CREATE TABLE IF NOT EXISTS main_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, 
              phone TEXT, city TEXT, village TEXT, relative_exam TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT, type TEXT)''')

# جدول التصحيح الجديد
c.execute('''CREATE TABLE IF NOT EXISTS correction_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, 
              subject TEXT, branch TEXT, city TEXT, village TEXT, 
              has_relative TEXT, relative_details TEXT, phone TEXT)''')
conn.commit()

# --- 3. تهيئة الجلسة ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

# --- 4. تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم (رقم المدرسة)").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل الدخول للمدرسة"):
            try:
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                df_acc.columns = df_acc.columns.str.strip()
                match = df_acc[(df_acc['school_user'].astype(str) == u_input) & (df_acc['password'].astype(str) == p_input)]
                if not match.empty:
                    st.session_state.update({
                        'auth': True, 'user_type': "school", 'school_user': u_input,
                        'school_display_name': str(match.iloc[0].get('school_full_name', u_input)).strip()
                    })
                    st.rerun()
                else: st.error("❌ خطأ في بيانات الدخول")
            except Exception as e: st.error(f"❌ خطأ اتصال: {e}")
    
    with tab2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول المسؤول"):
                st.session_state.auth, st.session_state.user_type = True, "admin"
                st.rerun()
    st.stop()

# --- 5. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    if st.sidebar.button("تسجيل الخروج"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    main_tab, correct_tab = st.tabs(["📝 مراقبة وتوظيف", "✍️ تصحيح الثانوية العامة"])

    # --- نموذج المراقبة والتوظيف ---
    with main_tab:
        mode = st.radio("النموذج:", ["الثانوية العامة", "امتحان التوظيف"], horizontal=True)
        with st.form("main_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم رباعي")
                id_num = st.text_input("رقم الهوية")
                phone = st.text_input("رقم الجوال")
            with col2:
                city = st.text_input("المدينة")
                village = st.text_input("القرية (إن وجد)")
                job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
            
            c1, c2 = st.columns(2)
            with c1: school2 = st.text_input("المدرسة الثانية")
            with c2: rel_exam = st.text_input("امتحان القريب المباشر (إن وجد)")
            
            if mode == "الثانوية العامة":
                e1, e2 = st.columns(2)
                with e1: desire = st.radio("يرغب بالمراقبة؟", ["يرغب", "لا يرغب"], horizontal=True)
                with e2: note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True)
            else: desire, note = "توظيف", ""

            if st.form_submit_button("💾 حفظ بيانات المراقبة/التوظيف"):
                if name and id_num:
                    c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, city, village, rel_exam, job, desire, note, mode))
                    conn.commit()
                    st.success(f"✅ تم الحفظ بنجاح")
                else: st.error("⚠️ يرجى تعبئة الاسم والهوية")

    # --- نموذج التصحيح الجديد ---
    with correct_tab:
        st.subheader("نموذج تصحيح الثانوية العامة")
        with st.form("correct_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                c_name = st.text_input("الاسم الرباعي")
                c_id = st.text_input("رقم الهوية ")
                c_subject = st.selectbox("المبحث الذي يدرسه المعلم", ["اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم الحياتية", "الكيمياء", "الفيزياء", "الثقافة العلمية", "تكنولوجيا المعلومات", "التاريخ", "الجغرافيا", "التربية الدينية", "فرع الريادة والأعمال مباحث التخصص", "فرع الاقتصاد المنزلي مباحث التخصص", "الفروع المهنية الصناعي مباحث التخصص", "الفروع المهنية الزراعي مباحث التخصص"])
            with f_col2:
                c_city = st.text_input("مكان السكن: المدينة")
                c_village = st.text_input("مكان السكن: القرية")
                c_branch = st.selectbox("الفرع", ["الأدبي", "العلمي", "الريادة والأعمال", "الزراعي", "الصناعي", "الاقتصاد المنزلي"])
            
            st.divider()
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                has_rel = st.radio("هل له قريب مباشر في الثانوية العامة؟", ["لا", "نعم"], horizontal=True)
                c_phone = st.text_input("رقم الجوال ")
            with r_col2:
                rel_type = st.multiselect("العلاقة (في حال نعم)", ["ابن", "ابنة", "أخ", "أخت", "زوج", "زوجة", "خطيب", "خطيبة"])
                rel_name = st.text_input("اسم القريب المباشر")
            
            if st.form_submit_button("💾 حفظ بيانات التصحيح"):
                if c_name and c_id:
                    rel_info = f"{rel_name} ({', '.join(rel_type)})" if has_rel == "نعم" else "لا يوجد"
                    c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subject, c_branch, c_city, c_village, has_rel, rel_info, c_phone))
                    conn.commit()
                    st.success("✅ تم حفظ بيانات التصحيح")
                else: st.error("⚠️ يرجى تعبئة الاسم والهوية")

# --- 6. لوحة الإدارة (3 شاشات) ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ لوحة الإدارة المركزية - جنوب نابلس")
    if st.sidebar.button("تسجيل الخروج"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    adm_tab1, adm_tab2, adm_tab3 = st.tabs(["📊 بيانات الثانوية (مراقبة)", "📝 بيانات التوظيف", "✍️ بيانات التصحيح"])
    
    with adm_tab1:
        df1 = pd.read_sql("SELECT * FROM main_table WHERE type='الثانوية العامة'", conn)
        st.dataframe(df1, use_container_width=True)
        # زر التحميل... (موجود في الكود الكامل)

    with adm_tab2:
        df2 = pd.read_sql("SELECT * FROM main_table WHERE type='امتحان التوظيف'", conn)
        st.dataframe(df2, use_container_width=True)

    with adm_tab3:
        df3 = pd.read_sql("SELECT * FROM correction_table", conn)
        st.dataframe(df3, use_container_width=True)

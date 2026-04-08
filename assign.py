import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والتنسيق (RTL) ---
st.set_page_config(page_title="نظام جمع البيانات 2026", layout="wide")

# تنسيق CSS لجعل الواجهة تدعم العربية والاتجاه من اليمين لليسار
st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; }
    .st-emotion-cache-1kyxreq { justify-content: flex-end; }
    input, select, textarea { direction: rtl !important; text-align: right !important; }
    /* تنسيق خاص لجعل الحقول تظهر بوضوح */
    .stCheckbox, .stRadio { margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# رابط جوجل شيت (CSV)
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. إعداد قاعدة البيانات ---
conn = sqlite3.connect("exams_data_2026.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tawjihi_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school1 TEXT, school2 TEXT, phone TEXT, 
              city TEXT, village TEXT, relative_name TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT)''')
conn.commit()

# --- 3. إدارة تسجيل الدخول ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
    st.session_state['user_type'] = ""
    st.session_state['school_id'] = ""

if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل الدخول"):
            try:
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                match = df_acc[(df_acc['school_user'].astype(str).str.strip() == u_input) & 
                               (df_acc['password'].astype(str).str.strip() == p_input)]
                if not match.empty:
                    st.session_state['auth'] = True
                    st.session_state['user_type'] = "school"
                    st.session_state['school_id'] = u_input
                    st.rerun()
                else: st.error("❌ خطأ في البيانات")
            except: st.error("❌ فشل الاتصال بقاعدة البيانات")
    
    with tab2:
        admin_pass = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول الإدارة"):
            if admin_pass == "ADMIN2026":
                st.session_state['auth'] = True
                st.session_state['user_type'] = "admin"
                st.rerun()
    st.stop()

# --- 4. واجهة المدارس (تعبئة البيانات) ---
if st.session_state.user_type == "school":
    st.sidebar.success(f"المدرسة: {st.session_state.school_id}")
    if st.sidebar.button("خروج"):
        st.session_state.auth = False
        st.rerun()

    st.header(f"📝 نموذج مدرسة: {st.session_state.school_id}")
    
    # --- الخانات الديناميكية (خارج الـ Form لتعمل فوراً) ---
    st.subheader("إعدادات إضافية")
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        sec_sch_check = st.checkbox("✅ المعلم يعمل في مدرسة ثانية")
    with col_opt2:
        rel_check = st.radio("👪 هل له قريب مباشر في الامتحان؟", ["لا يوجد", "يوجد"], horizontal=True)

    st.divider()

    # --- نموذج إدخال البيانات الرئيسي ---
    with st.form("main_entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("اسم المعلم رباعي")
            id_num = st.text_input("رقم الهوية")
            phone = st.text_input("رقم الجوال")
        with c2:
            city = st.text_input("المدينة")
            village = st.text_input("القرية / السكن")
            job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])

        # تظهر الخانات هنا بناءً على الاختيار المسبق بالخارج
        school2 = ""
        if sec_sch_check:
            school2 = st.text_input("🔍 اكتب اسم المدرسة الثانية هنا")
        
        rel_n = ""
        if rel_check == "يوجد":
            rel_n = st.text_input("🔍 اكتب اسم القريب المباشر هنا")

        st.divider()
        desire = st.radio("هل يرغب بالمراقبة؟", ["يرغب", "لا يرغب"], horizontal=True)
        note = st.radio("رأي المدير (هل يصلح للعمل؟):", ["يصلح", "لا يصلح"], horizontal=True)

        if st.form_submit_button("حفظ وإرسال البيانات"):
            if name and id_num:
                c.execute("INSERT OR REPLACE INTO tawjihi_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          (id_num, name, st.session_state.school_id, school2, phone, city, village, rel_n, job, desire, note))
                conn.commit()
                st.success(f"✅ تم حفظ بيانات المعلم {name} بنجاح")
            else:
                st.error("⚠️ يرجى تعبئة الاسم ورقم الهوية")

# --- 5. واجهة المدير (تصدير البيانات) ---
elif st.session_state.user_type == "admin":
    st.title("🛠️ لوحة تحكم الإدارة")
    if st.sidebar.button("خروج"):
        st.session_state.auth = False
        st.rerun()

    df = pd.read_sql("SELECT * FROM tawjihi_table", conn)
    st.write("### إجمالي البيانات المسجلة")
    st.dataframe(df, use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 تحميل ملف Excel", data=buffer.getvalue(), file_name="Schools_Data_2026.xlsx")

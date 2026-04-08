import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والتنسيق من اليمين لليسار (RTL) ---
st.set_page_config(page_title="نظام جمع البيانات 2026", layout="wide")

# إضافة تنسيق CSS لجعل الواجهة تدعم اللغة العربية بالكامل
st.markdown("""
    <style>
    .stApp {
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stForm"] {
        text-align: right;
    }
    .st-emotion-cache-1kyxreq {
        justify-content: flex-end;
    }
    /* محاذاة القوائم المنسدلة والنصوص */
    input, select, textarea {
        direction: rtl !format;
        text-align: right !important;
    }
    </style>
    """, unsafe_allow_html=True)

# رابط جوجل شيت (CSV) الخاص بك
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. إعداد قاعدة البيانات المحلية ---
conn = sqlite3.connect("exams_data_2026.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS tawjihi_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school1 TEXT, school2 TEXT, phone TEXT, 
              city TEXT, village TEXT, relative_name TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS hiring_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school TEXT, phone TEXT, 
              job_title TEXT, relative_exams TEXT)''')
conn.commit()

# --- 3. دالة جلب حسابات المدارس ---
@st.cache_data(ttl=600)
def fetch_accounts(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except:
        return None

# --- 4. إدارة الجلسة (Login System) ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
    st.session_state['user_type'] = ""
    st.session_state['school_id'] = ""

if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - نابلس")
    
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم (المدرسة)").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل الدخول"):
            df_acc = fetch_accounts(SCHOOLS_ACCOUNTS_URL)
            if df_acc is not None:
                match = df_acc[(df_acc['school_user'].astype(str).str.strip() == u_input) & 
                               (df_acc['password'].astype(str).str.strip() == p_input)]
                if not match.empty:
                    st.session_state['auth'] = True
                    st.session_state['user_type'] = "school"
                    st.session_state['school_id'] = u_input
                    st.rerun()
                else: st.error("❌ بيانات الدخول غير صحيحة")
            else: st.error("❌ فشل الاتصال بقاعدة بيانات المدارس")

    with tab2:
        admin_pass = st.text_input("كلمة مرور الإدارة المركزية", type="password")
        if st.button("دخول الإدارة"):
            if admin_pass == "ADMIN2026":
                st.session_state['auth'] = True
                st.session_state['user_type'] = "admin"
                st.rerun()
            else: st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 5. واجهة المدارس (RTL) ---
if st.session_state.user_type == "school":
    st.sidebar.success(f"المدرسة: {st.session_state.school_id}")
    if st.sidebar.button("خروج"):
        st.session_state.auth = False
        st.rerun()

    mode = st.radio("اختر نوع النموذج:", ["الثانوية العامة", "امتحان التوظيف"], horizontal=True)
    st.divider()

    if mode == "الثانوية العامة":
        st.subheader("📝 بيانات المعلم - الثانوية العامة")
        with st.form("t_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("اسم المعلم رباعي")
                id_num = st.text_input("رقم الهوية")
                phone = st.text_input("رقم الجوال")
                city = st.text_input("المدينة")
            with c2:
                village = st.text_input("القرية / السكن")
                job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
                
                # --- ميزة التفاعل: المدرسة الثانية ---
                sec_sch_check = st.checkbox("يعمل في مدرسة ثانية؟")
                school2 = ""
                if sec_sch_check:
                    school2 = st.text_input("اسم المدرسة الثانية")
            
            st.divider()
            
            # --- ميزة التفاعل: القريب المباشر ---
            rel_check = st.radio("هل له قريب مباشر في الامتحان؟", ["لا يوجد", "يوجد"], horizontal=True)
            rel_n = ""
            if rel_check == "يوجد":
                rel_n = st.text_input("اسم القريب المباشر")
            
            st.divider()
            desire = st.radio("يرغب بالمراقبة؟", ["يرغب", "لا يرغب"], horizontal=True)
            note = st.radio("رأي المدير (هل يصلح للعمل؟):", ["يصلح", "لا يصلح"], horizontal=True)
            
            if st.form_submit_button("حفظ وإرسال البيانات"):
                if name and id_num:
                    c.execute("INSERT OR REPLACE INTO tawjihi_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (id_num, name, st.session_state.school_id, school2, phone, city, village, rel_n, job, desire, note))
                    conn.commit()
                    st.success(f"✅ تم حفظ بيانات {name} بنجاح")
                else: st.error("⚠️ يرجى إكمال البيانات الأساسية")

    else:
        st.subheader("📋 بيانات المعلم - امتحان التوظيف")
        with st.form("h_form", clear_on_submit=True):
            h_name = st.text_input("الاسم رباعي")
            h_id = st.text_input("رقم الهوية")
            h_job = st.selectbox("الوظيفة الحالية", ["معلم", "مدير", "سكرتير", "آذن"])
            
            # --- ميزة التفاعل في التوظيف ---
            h_rel = st.radio("هل له قريب متقدم لاختبار التوظيف؟", ["لا يوجد", "يوجد"], horizontal=True)
            h_exams = ""
            if h_rel == "يوجد":
                h_exams = st.text_area("اكتب أسماء الاختبارات (كل اختبار في سطر)")
            
            if st.form_submit_button("حفظ بيانات التوظيف"):
                if h_name and h_id:
                    c.execute("INSERT OR REPLACE INTO hiring_table VALUES (?,?,?,?,?,?)",
                              (h_id, h_name, st.session_state.school_id, "", h_job, h_exams))
                    conn.commit()
                    st.success(f"✅ تم الحفظ بنجاح")

# --- 6. واجهة المدير (تصدير البيانات) ---
elif st.session_state.user_type == "admin":
    st.title("🛠️ لوحة تحكم الإدارة")
    if st.sidebar.button("خروج"):
        st.session_state.auth = False
        st.rerun()

    d1 = pd.read_sql("SELECT * FROM tawjihi_table", conn)
    st.write("### بيانات الثانوية العامة المسجلة")
    st.dataframe(d1, use_container_width=True)
    
    # تحميل إكسل
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        d1.to_excel(writer, index=False, sheet_name='البيانات')
    st.download_button("📥 تحميل كافة البيانات (Excel)", data=buffer.getvalue(), file_name="General_Exams_2026.xlsx")

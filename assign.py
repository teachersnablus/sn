import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والروابط ---
st.set_page_config(page_title="نظام جمع البيانات 2026", layout="wide")

# الرابط المباشر الذي قدمته (تم التحقق منه)
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

# --- 3. دالة جلب البيانات مع معالجة الأخطاء ---
@st.cache_data(ttl=600)  # تحديث البيانات كل 10 دقائق
def fetch_accounts(url):
    try:
        # قراءة البيانات مع تحديد الترميز لضمان دعم اللغة العربية
        df = pd.read_csv(url)
        # إزالة أي مسافات زائدة في أسماء الأعمدة أو القيم
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None

# --- 4. إدارة الجلسة ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
    st.session_state['user_type'] = ""
    st.session_state['school_id'] = ""

# --- 5. شاشة تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - نابلس")
    
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم (المدرسة)").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("دخول"):
            df_acc = fetch_accounts(SCHOOLS_ACCOUNTS_URL)
            if df_acc is not None:
                # التحقق من وجود الحساب (تحويل القيم لنصوص للمقارنة الدقيقة)
                match = df_acc[(df_acc['school_user'].astype(str).str.strip() == u_input) & 
                               (df_acc['password'].astype(str).str.strip() == p_input)]
                if not match.empty:
                    st.session_state['auth'] = True
                    st.session_state['user_type'] = "school"
                    st.session_state['school_id'] = u_input
                    st.rerun()
                else:
                    st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
            else:
                st.error("❌ فشل جلب البيانات من Google Sheets. تأكد من إعدادات النشر.")

    with tab2:
        admin_pass = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول الإدارة"):
            if admin_pass == "ADMIN2026": # يمكنك تغييرها
                st.session_state['auth'] = True
                st.session_state['user_type'] = "admin"
                st.rerun()
            else: st.error("❌ كلمة المرور خطأ")
    st.stop()

# --- 6. واجهة المدارس ---
if st.session_state.user_type == "school":
    st.sidebar.success(f"المدرسة: {st.session_state.school_id}")
    if st.sidebar.button("خروج"):
        st.session_state.auth = False
        st.rerun()

    mode = st.radio("نوع النموذج:", ["الثانوية العامة", "امتحان التوظيف"], horizontal=True)
    
    if mode == "الثانوية العامة":
        with st.form("t_form"):
            st.subheader("📝 بيانات الثانوية العامة")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("اسم المعلم رباعي")
                id_num = st.text_input("رقم الهوية")
                phone = st.text_input("رقم الجوال")
                city = st.text_input("المدينة")
            with c2:
                village = st.text_input("القرية / السكن")
                job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
                sec_sch = st.checkbox("يعمل في مدرسة ثانية؟")
                school2 = st.text_input("اسم المدرسة الثانية") if sec_sch else ""
            
            st.divider()
            rel = st.radio("قريب مباشر في الامتحان؟", ["لا يوجد", "يوجد"])
            rel_n = st.text_input("اسم القريب") if rel == "يوجد" else ""
            desire = st.radio("يرغب بالمراقبة؟", ["يرغب", "لا يرغب"])
            note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"])
            
            if st.form_submit_button("حفظ"):
                if name and id_num:
                    c.execute("INSERT OR REPLACE INTO tawjihi_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (id_num, name, st.session_state.school_id, school2, phone, city, village, rel_n, job, desire, note))
                    conn.commit()
                    st.success("تم الحفظ!")
    else:
        with st.form("h_form"):
            st.subheader("📋 بيانات التوظيف")
            h_name = st.text_input("الاسم رباعي")
            h_id = st.text_input("رقم الهوية")
            h_job = st.selectbox("الوظيفة الحالية", ["معلم", "مدير", "سكرتير", "آذن"])
            h_rel = st.radio("قريب متقدم للتوظيف؟", ["لا يوجد", "يوجد"])
            h_exams = st.text_area("أسماء الاختبارات") if h_rel == "يوجد" else ""
            if st.form_submit_button("حفظ التوظيف"):
                c.execute("INSERT OR REPLACE INTO hiring_table VALUES (?,?,?,?,?,?)",
                          (h_id, h_name, st.session_state.school_id, "", h_job, h_exams))
                conn.commit()
                st.success("تم الحفظ!")

# --- 7. لوحة التحكم (المدير) ---
elif st.session_state.user_type == "admin":
    st.title("🛠️ لوحة الإدارة")
    if st.sidebar.button("خروج"):
        st.session_state.auth = False
        st.rerun()

    d1 = pd.read_sql("SELECT * FROM tawjihi_table", conn)
    st.write("بيانات الثانوية العامة")
    st.dataframe(d1)
    
    # تصدير إكسل
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        d1.to_excel(writer, index=False)
    st.download_button("📥 تحميل Excel", data=buffer.getvalue(), file_name="Data_2026.xlsx")

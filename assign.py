import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والتنسيق (RTL) ---
st.set_page_config(page_title="نظام جمع البيانات 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    input, select, textarea { direction: rtl !important; text-align: right !important; }
    .school-title { color: #1E3A8A; background-color: #f0f2f6; padding: 15px; border-radius: 8px; text-align: center; border-right: 5px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# رابط جوجل شيت (CSV)
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_data_2026.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tawjihi_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_name TEXT, school2 TEXT, phone TEXT, 
              city TEXT, village TEXT, relative_name TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT)''')
conn.commit()

# --- 3. تهيئة الجلسة (Session State) ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
if 'school_display_name' not in st.session_state:
    st.session_state['school_display_name'] = ""
if 'user_type' not in st.session_state:
    st.session_state['user_type'] = ""

# --- 4. تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم (رقم المدرسة)").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل الدخول"):
            try:
                # جلب البيانات من جوجل شيت
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                df_acc.columns = df_acc.columns.str.strip()
                
                # البحث عن الحساب المطابق
                match = df_acc[(df_acc['school_user'].astype(str) == u_input) & (df_acc['password'].astype(str) == p_input)]
                
                if not match.empty:
                    st.session_state['auth'] = True
                    st.session_state['user_type'] = "school"
                    
                    # --- التعديل المطلوب: جلب اسم المدرسة من العمود المقابل ---
                    # تأكد أن اسم العمود في الإكسل هو school_full_name
                    if 'school_full_name' in df_acc.columns:
                        st.session_state['school_display_name'] = match.iloc[0]['school_full_name']
                    else:
                        st.session_state['school_display_name'] = u_input # احتياطي لو العمود مش موجود
                    
                    st.rerun()
                else: 
                    st.error("❌ بيانات الدخول غير صحيحة")
            except Exception as e: 
                st.error(f"❌ حدث خطأ في الاتصال بقاعدة البيانات: {e}")
    
    with tab2:
        adm_p = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول الإدارة"):
            if adm_p == "ADMIN2026":
                st.session_state['auth'], st.session_state['user_type'] = True, "admin"
                st.rerun()
    st.stop()

# --- 5. واجهة المدارس (بعد تسجيل الدخول) ---
if st.session_state['user_type'] == "school":
    # عرض اسم المدرسة الكامل في العنوان
    st.markdown(f"<h2 class='school-title'>📝 نموذج مدرسة: {st.session_state['school_display_name']}</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state['auth'] = False
        st.rerun()

    with st.container():
        with st.form("my_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                t_name = st.text_input("اسم المعلم رباعي")
                t_id = st.text_input("رقم الهوية")
                t_phone = st.text_input("رقم الجوال")
            with col2:
                t_city = st.text_input("المدينة")
                t_village = st.text_input("القرية / السكن")
                t_job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])

            st.divider()
            
            # الخانات الإضافية داخل الصندوق (اختيارية)
            c_opt1, c_opt2 = st.columns(2)
            with c_opt1:
                t_school2 = st.text_input("اسم المدرسة الثانية (اتركه فارغاً إذا لا يوجد)")
            with c_opt2:
                t_rel_name = st.text_input("اسم القريب المباشر في الامتحان (اتركه فارغاً إذا لا يوجد)")

            st.divider()
            col_end1, col_end2 = st.columns(2)
            with col_end1:
                t_desire = st.radio("هل يرغب بالمراقبة؟", ["يرغب", "لا يرغب"], horizontal=True)
            with col_end2:
                t_note = st.radio("رأي المدير (هل يصلح للعمل؟):", ["يصلح", "لا يصلح"], horizontal=True)

            submit = st.form_submit_button("💾 حفظ البيانات وإرسالها")
            
            if submit:
                if t_name and t_id:
                    # حفظ اسم المدرسة الكامل في قاعدة البيانات أيضاً
                    c.execute("INSERT OR REPLACE INTO tawjihi_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (t_id, t_name, st.session_state['school_display_name'], t_school2, t_phone, t_city, t_village, t_rel_name, t_job, t_desire, t_note))
                    conn.commit()
                    st.success(f"✅ تم بنجاح حفظ بيانات: {t_name}")
                else:
                    st.error("⚠️ يرجى إدخال الاسم ورقم الهوية على الأقل")

# --- 6. لوحة المدير ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ لوحة الإدارة المركزية")
    df = pd.read_sql("SELECT * FROM tawjihi_table", conn)
    st.dataframe(df, use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 تحميل ملف Excel", data=buffer.getvalue(), file_name="Full_Data_2026.xlsx")

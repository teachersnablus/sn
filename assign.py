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
    .stHeader { color: #1E3A8A; }
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

# --- 3. إدارة الجلسة ودالة الحسابات ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user_type': "", 'school_display_name': "", 'school_user': ""})

def fetch_accounts():
    try:
        df = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
        df.columns = df.columns.str.strip()
        return df
    except: return None

# --- 4. تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم (رقم المدرسة)").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل الدخول"):
            df_acc = fetch_accounts()
            if df_acc is not None:
                # التحقق من الحساب وجلب الاسم الكامل school_full_name
                match = df_acc[(df_acc['school_user'].astype(str) == u_input) & (df_acc['password'].astype(str) == p_input)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user_type = "school"
                    st.session_state.school_user = u_input
                    # هنا السحر: جلب اسم المدرسة من عمود school_full_name
                    st.session_state.school_display_name = match.iloc[0]['school_full_name']
                    st.rerun()
                else: st.error("❌ بيانات الدخول غير صحيحة")
            else: st.error("❌ فشل الاتصال ببيانات المدارس")
    
    with tab2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول الإدارة"):
                st.session_state.auth, st.session_state.user_type = True, "admin"
                st.rerun()
    st.stop()

# --- 5. واجهة المدارس (التصميم الجديد) ---
if st.session_state.user_type == "school":
    # عرض اسم المدرسة في الأعلى بشكل واضح
    st.markdown(f"<h2 style='text-align: center;'>📝 نموذج مدرسة: {st.session_state.school_display_name}</h2>", unsafe_allow_html=True)
    
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth = False
        st.rerun()

    # استخدام حاوية لضمان التفاعل داخل الصندوق
    with st.container():
        with st.form("professional_form", clear_on_submit=True):
            st.subheader("📋 البيانات الأساسية")
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
            st.subheader("🔍 إعدادات إضافية (داخل الصندوق)")
            
            # وضع الخانات داخل الصندوق بشكل مرتب
            c_opt1, c_opt2 = st.columns(2)
            with c_opt1:
                # ملاحظة: في الـ Form، الخانات لا تفتح حقولاً جديدة فوراً إلا إذا كانت خارجها.
                # لجعلها تعمل "داخل" وبشكل "أحلى"، سنضع الحقول ونطلب تعبئتها إذا رغب المستخدم.
                has_school2 = st.checkbox("المعلم يعمل في مدرسة ثانية")
                t_school2 = st.text_input("اسم المدرسة الثانية", help="اكتب الاسم هنا إذا فعلت الخيار أعلاه")
            
            with c_opt2:
                has_relative = st.radio("هل له قريب مباشر في الامتحان؟", ["لا يوجد", "يوجد"], horizontal=True)
                t_rel_name = st.text_input("اسم القريب المباشر", help="اكتب الاسم هنا إذا اخترت يوجد")

            st.divider()
            col_end1, col_end2 = st.columns(2)
            with col_end1:
                t_desire = st.radio("هل يرغب بالمراقبة؟", ["يرغب", "لا يرغب"], horizontal=True)
            with col_end2:
                t_note = st.radio("رأي المدير (هل يصلح للعمل؟):", ["يصلح", "لا يصلح"], horizontal=True)

            if st.form_submit_button("حفظ وإرسال البيانات"):
                if t_name and t_id:
                    c.execute("INSERT OR REPLACE INTO tawjihi_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (t_id, t_name, st.session_state.school_display_name, t_school2, t_phone, t_city, t_village, t_rel_name, t_job, t_desire, t_note))
                    conn.commit()
                    st.success(f"✅ تم حفظ بيانات المعلم {t_name} في سجلات {st.session_state.school_display_name}")
                else:
                    st.error("⚠️ يرجى تعبئة الاسم ورقم الهوية")

# --- 6. لوحة المدير ---
elif st.session_state.user_type == "admin":
    st.title("🛠️ لوحة الإدارة المركزية")
    df = pd.read_sql("SELECT * FROM tawjihi_table", conn)
    st.dataframe(df, use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 تحميل ملف Excel", data=buffer.getvalue(), file_name="Full_Data_2026.xlsx")

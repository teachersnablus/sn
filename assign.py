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
    .school-title { color: #1E3A8A; background-color: #f0f2f6; padding: 15px; border-radius: 8px; text-align: center; border-right: 5px solid #1E3A8A; margin-bottom: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# رابط جوجل شيت (CSV)
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_data_2026.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tawjihi_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_name TEXT, school2 TEXT, phone TEXT, 
              city TEXT, village TEXT, relative_exam TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT, type TEXT)''')
conn.commit()

# --- 3. تهيئة الجلسة ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'user_type': ""})

# --- 4. تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    
    with tab1:
        u_input = st.text_input("اسم المستخدم (رقم المدرسة)").strip()
        p_input = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل الدخول"):
            try:
                # جلب البيانات وتنظيف شامل للأعمدة والبيانات
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                df_acc.columns = df_acc.columns.str.strip() # إزالة المسافات من أسماء الأعمدة
                
                # تحويل كل الأعمدة لنصوص وإزالة المسافات من القيم للمقارنة الدقيقة
                df_acc['school_user'] = df_acc['school_user'].astype(str).str.strip()
                df_acc['password'] = df_acc['password'].astype(str).str.strip()
                
                match = df_acc[(df_acc['school_user'] == u_input) & (df_acc['password'] == p_input)]
                
                if not match.empty:
                    st.session_state['auth'] = True
                    st.session_state['user_type'] = "school"
                    
                    # محاولة جلب الاسم من العمود المحدد
                    if 'school_full_name' in df_acc.columns:
                        st.session_state['school_display_name'] = str(match.iloc[0]['school_full_name']).strip()
                    else:
                        st.session_state['school_display_name'] = u_input
                    
                    st.rerun()
                else: 
                    st.error("❌ بيانات الدخول غير صحيحة")
            except Exception as e: 
                st.error(f"❌ خطأ: تأكد من رابط ملف الإكسل أو أسماء الأعمدة. التفاصيل: {e}")
    
    with tab2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول الإدارة"):
                st.session_state.auth, st.session_state.user_type = True, "admin"
                st.rerun()
    st.stop()

# --- 5. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    # عرض اسم المدرسة بوضوح
    st.markdown(f"<div class='school-title'>🏢 نموذج مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    
    if st.sidebar.button("تسجيل الخروج"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

    mode = st.radio("اختر نوع النموذج:", ["الثانوية العامة", "امتحان التوظيف"], horizontal=True)
    st.divider()

    with st.form("main_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("الاسم رباعي")
            id_num = st.text_input("رقم الهوية")
            phone = st.text_input("رقم الجوال")
        with col2:
            city = st.text_input("المدينة/السكن")
            job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
            village = st.text_input("القرية (إن وجد)")

        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            school2 = st.text_input("اسم المدرسة الثانية (إن وجد)")
        with c2:
            # التعديل المطلوب: امتحان القريب المباشر للتوظيف أو الثانوية
            rel_exam = st.text_input("امتحان القريب المباشر (اذكر الامتحان أو الامتحانات إن وجد)")

        st.divider()
        
        if mode == "الثانوية العامة":
            e1, e2 = st.columns(2)
            with e1:
                desire = st.radio("هل يرغب بالمراقبة؟", ["يرغب", "لا يرغب"], horizontal=True)
            with e2:
                note = st.radio("رأي المدير (هل يصلح للعمل؟):", ["يصلح", "لا يصلح"], horizontal=True)
        else:
            desire = "متقدم للامتحان"
            note = st.text_area("ملاحظات إضافية بخصوص امتحان التوظيف")

        if st.form_submit_button("💾 حفظ البيانات"):
            if name and id_num:
                c.execute("INSERT OR REPLACE INTO tawjihi_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                          (id_num, name, st.session_state['school_display_name'], school2, phone, city, village, rel_exam, job, desire, note, mode))
                conn.commit()
                st.success(f"✅ تم حفظ بيانات {name} بنجاح في سجلات {st.session_state['school_display_name']}")
            else: st.error("⚠️ يرجى كتابة الاسم ورقم الهوية")

# --- 6. لوحة الإدارة ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ لوحة الإدارة")
    df = pd.read_sql("SELECT * FROM tawjihi_table", conn)
    st.dataframe(df, use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 تحميل كافة البيانات Excel", data=buffer.getvalue(), file_name="Reports_2026.xlsx")

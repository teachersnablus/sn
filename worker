import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والروابط ---
st.set_page_config(page_title="نظام جمع بيانات الامتحانات 2026", layout="wide")

# رابط جوجل شيت الذي قدمته (CSV)
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. إعداد قاعدة البيانات المحلية ---
conn = sqlite3.connect("exams_data_collection.db", check_same_thread=False)
c = conn.cursor()

# إنشاء جداول البيانات إذا لم تكن موجودة
c.execute('''CREATE TABLE IF NOT EXISTS tawjihi_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school1 TEXT, school2 TEXT, phone TEXT, 
              city TEXT, village TEXT, relative_name TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS hiring_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school TEXT, phone TEXT, 
              job_title TEXT, relative_exams TEXT)''')
conn.commit()

# --- 3. نظام إدارة الجلسة (Session State) ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False
    st.session_state['user_type'] = "" # "school" أو "admin"
    st.session_state['school_id'] = ""

# --- 4. شاشة تسجيل الدخول ---
if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - نظام جمع البيانات")
    
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ لوحة الإدارة"])
    
    with tab1:
        with st.form("school_login"):
            u_input = st.text_input("اسم المستخدم (المدرسة)").strip()
            p_input = st.text_input("كلمة المرور", type="password").strip()
            submit_login = st.form_submit_button("دخول")
            
            if submit_login:
                try:
                    df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                    # التحقق من المطابقة
                    check = df_acc[(df_acc['school_user'].astype(str) == u_input) & 
                                   (df_acc['password'].astype(str) == p_input)]
                    if not check.empty:
                        st.session_state['auth'] = True
                        st.session_state['user_type'] = "school"
                        st.session_state['school_id'] = u_input
                        st.rerun()
                    else:
                        st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
                except:
                    st.error("❌ فشل الاتصال بقاعدة بيانات المدارس، تأكد من رابط Google Sheets")

    with tab2:
        with st.form("admin_login"):
            admin_pass = st.text_input("كلمة مرور الإدارة المركزية", type="password")
            if st.form_submit_button("دخول الإدارة"):
                if admin_pass == "ADMIN2026": # يمكنك تغييرها لأي كلمة سر تريدها
                    st.session_state['auth'] = True
                    st.session_state['user_type'] = "admin"
                    st.rerun()
                else:
                    st.error("❌ كلمة المرور غير صحيحة")
    st.stop()

# --- 5. واجهة المدارس ---
if st.session_state.user_type == "school":
    st.sidebar.success(f"مرحباً: {st.session_state.school_id}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.auth = False
        st.rerun()

    menu = st.radio("اختر نوع النموذج لتعبئته:", ["نموذج الثانوية العامة", "نموذج امتحان التوظيف"], horizontal=True)
    st.divider()

    if menu == "نموذج الثانوية العامة":
        st.subheader("📋 تعبئة بيانات المعلم - الثانوية العامة")
        with st.form("tawjihi_f"):
            c1, c2 = st.columns(2)
            with c1:
                t_name = st.text_input("اسم المعلم رباعي")
                t_id = st.text_input("رقم الهوية")
                t_phone = st.text_input("رقم الجوال")
                t_city = st.text_input("مكان السكن (المدينة)")
            with c2:
                t_village = st.text_input("القرية / الحي")
                t_job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
                t_sec_check = st.checkbox("هل يعمل المعلم في مدرسة ثانية؟")
                t_school2 = st.text_input("اسم المدرسة الثانية") if t_sec_check else ""
            
            st.markdown("---")
            t_rel_check = st.radio("هل له قريب مباشر في امتحان الثانوية العامة؟", ["لا يوجد", "يوجد"])
            t_rel_name = st.text_input("اسم القريب المباشر (في حال وجوده)") if t_rel_check == "يوجد" else ""
            
            t_desire = st.radio("هل يرغب بالمراقبة؟", ["يرغب", "لا يرغب"])
            t_note = st.radio("رأي مدير المدرسة:", ["يصلح للعمل في الامتحان", "لا يصلح للعمل في الامتحان"])
            
            if st.form_submit_button("إرسال البيانات"):
                if t_name and t_id:
                    c.execute("INSERT OR REPLACE INTO tawjihi_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                              (t_id, t_name, st.session_state.school_id, t_school2, t_phone, t_city, t_village, t_rel_name, t_job, t_desire, t_note))
                    conn.commit()
                    st.balloons()
                    st.success(f"✅ تم حفظ بيانات المعلم {t_name} بنجاح")
                else:
                    st.error("⚠️ يرجى إدخال الاسم ورقم الهوية على الأقل")

    else:
        st.subheader("📋 تعبئة بيانات المعلم - امتحان التوظيف")
        with st.form("hiring_f"):
            h_name = st.text_input("اسم المعلم رباعي")
            h_id = st.text_input("رقم الهوية")
            h_phone = st.text_input("رقم الجوال")
            h_job = st.selectbox("الوظيفة الحالية", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
            
            st.info("معلومات الأقارب في التوظيف")
            h_rel_check = st.radio("هل له قريب مباشر متقدم لاختبار التوظيف؟", ["لا يوجد", "يوجد"])
            h_rel_exams = st.text_area("إذا وجد، اكتب أسماء الاختبارات (كل اختبار في سطر)") if h_rel_check == "يوجد" else ""
            
            if st.form_submit_button("حفظ بيانات التوظيف"):
                if h_name and h_id:
                    c.execute("INSERT OR REPLACE INTO hiring_table VALUES (?,?,?,?,?,?)",
                              (h_id, h_name, st.session_state.school_id, h_phone, h_job, h_rel_exams))
                    conn.commit()
                    st.success("✅ تم حفظ البيانات بنجاح")

# --- 6. واجهة الإدارة ---
elif st.session_state.user_type == "admin":
    st.title("🛠️ لوحة التحكم الإدارية المركزية")
    if st.sidebar.button("خروج آمن"):
        st.session_state.auth = False
        st.rerun()

    adm_tab1, adm_tab2 = st.tabs(["📊 بيانات الثانوية العامة", "📋 بيانات التوظيف"])
    
    with adm_tab1:
        df_taw = pd.read_sql("SELECT * FROM tawjihi_table", conn)
        st.write(f"إجمالي السجلات: {len(df_taw)}")
        st.dataframe(df_taw, use_container_width=True)
        
        # تصدير إكسل
        out1 = io.BytesIO()
        with pd.ExcelWriter(out1, engine='xlsxwriter') as wr1:
            df_taw.to_excel(wr1, index=False, sheet_name='الكل')
        st.download_button("📥 تحميل ملف إكسل (ثانوية عامة)", data=out1.getvalue(), file_name="Tawjihi_Data_2026.xlsx")

    with adm_tab2:
        df_hir = pd.read_sql("SELECT * FROM hiring_table", conn)
        st.write(f"إجمالي السجلات: {len(df_hir)}")
        st.dataframe(df_hir, use_container_width=True)
        
        # تصدير إكسل
        out2 = io.BytesIO()
        with pd.ExcelWriter(out2, engine='xlsxwriter') as wr2:
            df_hir.to_excel(wr2, index=False, sheet_name='التوظيف')
        st.download_button("📥 تحميل ملف إكسل (توظيف)", data=out2.getvalue(), file_name="Hiring_Data_2026.xlsx")

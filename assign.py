import streamlit as st
import pandas as pd
import sqlite3

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام مديرية جنوب نابلس 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    input, select, textarea { direction: rtl !important; text-align: right !important; }
    .school-title { color: #ffffff; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 25px; }
    .search-section { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 2px solid #1E3A8A; margin-bottom: 20px; }
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_final_v8.db", check_same_thread=False)
c = conn.cursor()

# جداول البيانات
c.execute('''CREATE TABLE IF NOT EXISTS main_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, 
              phone TEXT, city TEXT, village TEXT, relative_exam TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT, type TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS correction_table 
             (id_num TEXT PRIMARY KEY, name TEXT, school_user TEXT, school_full_name TEXT, 
              subject TEXT, branch TEXT, city TEXT, village TEXT, 
              has_relative TEXT, relative_details TEXT, phone TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS system_settings (form_name TEXT PRIMARY KEY, is_open INTEGER)''')
for form in ['ثانوية', 'توظيف', 'تصحيح']:
    c.execute("INSERT OR IGNORE INTO system_settings VALUES (?, 1)", (form,))
conn.commit()

def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

# --- 3. تسجيل الدخول ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - جنوب نابلس")
    t1, t2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    with t1:
        u_in = st.text_input("رقم المدرسة").strip()
        p_in = st.text_input("كلمة المرور", type="password").strip()
        if st.button("دخول المدارس"):
            try:
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                match = df_acc[(df_acc['school_user'].astype(str) == u_in) & (df_acc['password'].astype(str) == p_in)]
                if not match.empty:
                    st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u_in, 'school_display_name': str(match.iloc[0]['school_full_name'])})
                    st.rerun()
                else: st.error("❌ بيانات خاطئة")
            except: st.error("❌ فشل الاتصال بالحسابات")
    with t2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول المسؤول"):
                st.session_state.update({'auth': True, 'user_type': "admin"})
                st.rerun()
    st.stop()

# --- 4. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear(); st.rerun()

    menu = st.sidebar.radio("القائمة الرئيسية:", ["تعبئة، تعديل وحذف", "استعراض السجلات (عرض فقط)"])

    if menu == "تعبئة، تعديل وحذف":
        st.markdown("<div class='search-section'>🔎 <b>إدارة الموظفين:</b> أدخل رقم الهوية للبحث. إذا كان الموظف مسجلاً، يمكنك تعديله أو حذفه من هنا.</div>", unsafe_allow_html=True)
        search_id = st.text_input("أدخل رقم الهوية للبحث أو البدء بالتعبئة:")
        
        found_row = None
        is_main_db = False
        if search_id:
            df_m = pd.read_sql(f"SELECT * FROM main_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
            if not df_m.empty:
                found_row = df_m.iloc[0]; is_main_db = True
            else:
                df_c = pd.read_sql(f"SELECT * FROM correction_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
                if not df_c.empty:
                    found_row = df_c.iloc[0]; is_main_db = False

        if found_row is not None:
            st.warning(f"🔔 تم العثور على بيانات الموظف: **{found_row['name']}**. يمكنك التعديل أدناه ثم الحفظ، أو الحذف نهائياً.")
            if st.button("🗑️ حذف هذا الموظف من النظام"):
                c.execute("DELETE FROM main_table WHERE id_num=?", (search_id,))
                c.execute("DELETE FROM correction_table WHERE id_num=?", (search_id,))
                conn.commit(); st.success("✅ تم الحذف بنجاح"); st.rerun()

        tab_m, tab_c = st.tabs(["📋 مراقبة وتوظيف", "✍️ طلبات التصحيح"])
        
        with tab_m:
            if get_form_status('ثانوية') or get_form_status('توظيف'):
                mode = st.radio("النموذج المختار:", ["الثانوية العامة", "امتحان التوظيف"], horizontal=True)
                with st.form("main_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("الاسم رباعي *", value=found_row['name'] if (found_row is not None and is_main_db) else "")
                    id_num = c2.text_input("رقم الهوية *", value=search_id)
                    phone = c1.text_input("رقم الجوال *", value=found_row['phone'] if (found_row is not None and is_main_db) else "")
                    city = c2.text_input("المدينة *", value=found_row['city'] if (found_row is not None and is_main_db) else "")
                    village = c1.text_input("القرية *", value=found_row['village'] if (found_row is not None and is_main_db) else "")
                    job = col2_sel = c2.selectbox("الوظيفة *", ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"])
                    
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية (اختياري)", value=found_row['school2'] if (found_row is not None and is_main_db) else "")
                    rel_ex = st.text_input("اسم وقرابة القريب (اختياري)", value=found_row['relative_exam'] if (found_row is not None and is_main_db) else "")
                    
                    c3, c4 = st.columns(2)
                    desire = c3.radio("الرغبة بالعمل:", ["يرغب", "لا يرغب"], horizontal=True)
                    note = c4.radio("رأي مدير المدرسة:", ["يصلح", "لا يصلح"], horizontal=True)

                    if st.form_submit_button("💾 حفظ / تحديث البيانات"):
                        if not (name and id_num and phone and city and village and job):
                            st.error("⚠️ يرجى تعبئة كافة الحقول الإجبارية (*)")
                        else:
                            c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                      (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, city, village, rel_ex, job, desire, note, mode))
                            conn.commit(); st.success("✅ تم الحفظ وتحديث السجلات"); st.rerun()
            else: st.warning("النماذج مغلقة")

        with tab_c:
            if get_form_status('تصحيح'):
                with st.form("corr_form", clear_on_submit=True):
                    c_name = st.text_input("الاسم الرباعي *", value=found_row['name'] if (found_row is not None and not is_main_db) else "")
                    c_id = st.text_input("رقم الهوية *", value=search_id)
                    c_phone = st.text_input("الجوال *", value=found_row['phone'] if (found_row is not None and not is_main_db) else "")
                    c_city = st.text_input("المدينة *", value=found_row['city'] if (found_row is not None and not is_main_db) else "")
                    c_subj = st.selectbox("المبحث *", ["", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "أخرى"])
                    
                    st.divider()
                    has_rel = st.radio("هل يوجد قريب مباشر؟", ["لا", "نعم"], horizontal=True)
                    rel_info = st.text_input("تفاصيل القريب (إن وجد)")

                    if st.form_submit_button("💾 حفظ طلب التصحيح"):
                        if not (c_name and c_id and c_phone and c_city and c_subj):
                            st.error("⚠️ يرجى تعبئة الحقول الأساسية")
                        else:
                            c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                      (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subj, "", c_city, "", has_rel, rel_info, c_phone))
                            conn.commit(); st.success("✅ تم الحفظ"); st.rerun()

    elif menu == "استعراض السجلات (عرض فقط)":
        st.subheader("📊 كشوفات الموظفين المسجلين")
        df1 = pd.read_sql(f"SELECT * FROM main_table WHERE school_user='{st.session_state['school_user']}'", conn)
        df2 = pd.read_sql(f"SELECT * FROM correction_table WHERE school_user='{st.session_state['school_user']}'", conn)
        
        if df1.empty and df2.empty:
            st.info("لا توجد بيانات مسجلة حالياً.")
        else:
            if not df1.empty:
                st.write("🔹 **المراقبة والتوظيف:**")
                st.table(df1[['id_num', 'name', 'phone', 'city', 'job_title', 'type']])
            
            if not df2.empty:
                st.write("🔹 **التصحيح:**")
                st.table(df2[['id_num', 'name', 'phone', 'subject', 'has_relative']])
        
        st.info("💡 ملاحظة: للتعديل أو الحذف، يرجى الانتقال إلى شاشة 'تعبئة وبحث' واستخدام رقم الهوية.")

# --- 5. واجهة الإدارة ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ لوحة التحكم الإدارية")
    if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()
    
    adm_tab1, adm_tab2 = st.tabs(["📊 البيانات", "⚙️ الإعدادات"])
    
    with adm_tab2:
        for f in ['ثانوية', 'توظيف', 'تصحيح']:
            curr = get_form_status(f)
            if st.button(f"{'إغلاق' if curr else 'فتح'} نموذج {f}", key=f"btn_{f}"):
                c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (0 if curr else 1, f))
                conn.commit(); st.rerun()

    with adm_tab1:
        def view_admin(d_type, k_s, is_c=False):
            df = pd.read_sql("SELECT * FROM correction_table", conn) if is_c else pd.read_sql(f"SELECT * FROM main_table WHERE type='{d_type}'", conn)
            st.dataframe(df)
            t_id = st.selectbox("حذف/تعديل هوية:", [""] + df['id_num'].tolist(), key=k_s)
            if t_id:
                if st.button(f"حذف {t_id}", key=f"d_{k_s}"):
                    c.execute(f"DELETE FROM {'correction_table' if is_c else 'main_table'} WHERE id_num=?", (t_id,))
                    conn.commit(); st.rerun()
        
        st.write("ثانوية:")
        view_admin("الثانوية العامة", "a1")
        st.write("توظيف:")
        view_admin("امتحان التوظيف", "a2")
        st.write("تصحيح:")
        view_admin("", "a3", True)

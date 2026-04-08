import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام جنوب نابلس المطور 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    input, select, textarea { direction: rtl !important; text-align: right !important; }
    .school-title { color: #ffffff; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 25px; }
    .search-box { background-color: #f0f8ff; padding: 15px; border-radius: 10px; border: 1px solid #1E3A8A; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# رابط ملف الحسابات
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_ultra_v4_2026.db", check_same_thread=False)
c = conn.cursor()

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

# --- 3. وظائف مساعدة ---
def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

# --- 4. تسجيل الدخول ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    with tab1:
        u_in = st.text_input("رقم المدرسة").strip()
        p_in = st.text_input("كلمة المرور", type="password").strip()
        if st.button("دخول"):
            try:
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                match = df_acc[(df_acc['school_user'].astype(str) == u_in) & (df_acc['password'].astype(str) == p_in)]
                if not match.empty:
                    st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u_in, 'school_display_name': str(match.iloc[0]['school_full_name'])})
                    st.rerun()
                else: st.error("❌ بيانات خاطئة")
            except: st.error("❌ فشل الاتصال")
    with tab2:
        if st.text_input("كلمة مرور الإدارة", type="password") == "ADMIN2026":
            if st.button("دخول المسؤول"):
                st.session_state.update({'auth': True, 'user_type': "admin"})
                st.rerun()
    st.stop()

# --- 5. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    if st.sidebar.button("خروج"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("القائمة:", ["تعبئة وبحث سريع", "عرض وتعديل كافة السجلات"])

    if menu == "تعبئة وبحث سريع":
        st.markdown("<div class='search-box'>🔍 <b>البحث السريع والتعديل:</b> أدخل رقم الهوية للتأكد إذا كان الموظف مسجلاً مسبقاً لتعديل بياناته أو حذفه.</div>", unsafe_allow_html=True)
        search_id = st.text_input("بحث برقم الهوية:")
        
        # البحث في الجداول
        existing_data = None
        found_in = ""
        if search_id:
            c.execute("SELECT * FROM main_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user']))
            res = c.fetchone()
            if res:
                existing_data = res
                found_in = "main"
            else:
                c.execute("SELECT * FROM correction_table WHERE id_num=? AND school_user=?", (search_id, st.session_state['school_user']))
                res = c.fetchone()
                if res:
                    existing_data = res
                    found_in = "corr"
        
        if existing_data:
            st.warning(f"⚠️ تم العثور على بيانات الموظف (<b>{existing_data[1]}</b>). يمكنك تعديل بياناته أدناه أو حذفه.")
            if st.button("🗑️ حذف هذا الموظف نهائياً"):
                c.execute(f"DELETE FROM main_table WHERE id_num=?", (search_id,))
                c.execute(f"DELETE FROM correction_table WHERE id_num=?", (search_id,))
                conn.commit()
                st.success("تم الحذف بنجاح")
                st.rerun()
        
        tab_m, tab_c = st.tabs(["📋 مراقبة وتوظيف", "✍️ تصحيح"])
        
        with tab_m:
            if get_form_status('ثانوية') or get_form_status('توظيف'):
                mode = st.radio("النوع:", ["الثانوية العامة", "امتحان التوظيف"], horizontal=True)
                # جلب القيم الافتراضية إذا وجد بحث
                d_name = existing_data[1] if (existing_data and found_in=="main") else ""
                d_phone = existing_data[5] if (existing_data and found_in=="main") else ""
                d_city = existing_data[6] if (existing_data and found_in=="main") else ""
                d_vill = existing_data[7] if (existing_data and found_in=="main") else ""
                
                with st.form("form_main"):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("الاسم رباعي", value=d_name)
                    id_val = c2.text_input("رقم الهوية", value=search_id if search_id else "")
                    phone = c1.text_input("الجوال", value=d_phone)
                    city = c2.text_input("المدينة", value=d_city)
                    village = c1.text_input("القرية", value=d_vill)
                    job = c2.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
                    
                    st.divider()
                    school2 = st.text_input("مدرسة ثانية")
                    rel_ex = st.text_input("قريب في الامتحان")
                    
                    des, nte = "", ""
                    if mode == "الثانوية العامة":
                        des = st.radio("الرغبة:", ["يرغب", "لا يرغب"], horizontal=True)
                        nte = st.radio("المدير:", ["يصلح", "لا يصلح"], horizontal=True)
                    else: des = "توظيف"

                    if st.form_submit_button("💾 حفظ البيانات"):
                        c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                  (id_val, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, city, village, rel_ex, job, des, nte, mode))
                        conn.commit()
                        st.success("✅ تم الحفظ")
            else: st.error("النماذج مغلقة")

        with tab_c:
            if get_form_status('تصحيح'):
                d_name = existing_data[1] if (existing_data and found_in=="corr") else ""
                d_phone = existing_data[10] if (existing_data and found_in=="corr") else ""
                
                with st.form("form_corr"):
                    name_c = st.text_input("الاسم الرباعي", value=d_name)
                    id_c = st.text_input("رقم الهوية ", value=search_id if search_id else "")
                    subj_c = st.selectbox("المبحث", ["اللغة العربية", "اللغة الانجليزية", "الرياضيات", "الكيمياء", "الفيزياء", "أخرى"])
                    phone_c = st.text_input("الجوال ", value=d_phone)
                    city_c = st.text_input("المدينة ")
                    branch_c = st.selectbox("الفرع", ["الأدبي", "العلمي", "الريادة", "المهني"])
                    
                    if st.form_submit_button("💾 حفظ طلب التصحيح"):
                        c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                  (id_c, name_c, st.session_state['school_user'], st.session_state['school_display_name'], subj_c, branch_c, city_c, "", "", "", phone_c))
                        conn.commit()
                        st.success("✅ تم الحفظ")

    elif menu == "عرض وتعديل كافة السجلات":
        st.subheader("📋 كافة سجلات مدرستكم")
        df1 = pd.read_sql(f"SELECT * FROM main_table WHERE school_user='{st.session_state['school_user']}'", conn)
        df2 = pd.read_sql(f"SELECT * FROM correction_table WHERE school_user='{st.session_state['school_user']}'", conn)
        
        if not df1.empty:
            st.write("🔹 المراقبة والتوظيف:")
            st.dataframe(df1)
        if not df2.empty:
            st.write("🔹 التصحيح:")
            st.dataframe(df2)
            
        st.divider()
        st.subheader("🛠️ تعديل شامل للسجل")
        all_ids = list(set(df1['id_num'].tolist() + df2['id_num'].tolist()))
        target = st.selectbox("اختر الهوية للتعديل الشامل:", [""] + all_ids)
        
        if target:
            # هنا يظهر نموذج تعديل يحتوي على كل شيء
            is_main = target in df1['id_num'].values
            row = df1[df1['id_num']==target].iloc[0] if is_main else df2[df2['id_num']==target].iloc[0]
            
            with st.form("mega_edit"):
                st.write(f"تعديل بيانات: {row[1]}")
                new_n = st.text_input("الاسم", value=row[1])
                new_p = st.text_input("الهاتف", value=row[5] if is_main else row[10])
                new_c = st.text_input("المدينة", value=row[6])
                new_v = st.text_input("القرية", value=row[7])
                
                if st.form_submit_button("💾 حفظ التعديلات الشاملة"):
                    if is_main:
                        c.execute("UPDATE main_table SET name=?, phone=?, city=?, village=? WHERE id_num=?", (new_n, new_p, new_c, new_v, target))
                    else:
                        c.execute("UPDATE correction_table SET name=?, phone=?, city=?, village=? WHERE id_num=?", (new_n, new_p, new_c, new_v, target))
                    conn.commit()
                    st.success("تم التحديث بنجاح")
                    st.rerun()

# --- 6. لوحة الإدارة ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ التحكم الإداري")
    if st.sidebar.button("خروج "): st.session_state.clear(); st.rerun()
    
    adm_tab1, adm_tab2 = st.tabs(["⚙️ الصلاحيات", "📊 عرض البيانات"])
    
    with adm_tab1:
        st.header("فتح/إغلاق النماذج")
        for f in ['ثانوية', 'توظيف', 'تصحيح']:
            curr = get_form_status(f)
            if st.button(f"{'إغلاق' if curr else 'فتح'} نموذج {f}"):
                c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (0 if curr else 1, f))
                conn.commit(); st.rerun()
                
    with adm_tab2:
        df_all = pd.read_sql("SELECT * FROM main_table", conn)
        st.dataframe(df_all)
        if st.button("تفريغ كافة البيانات (⚠️ خطير)"):
            c.execute("DELETE FROM main_table"); c.execute("DELETE FROM correction_table")
            conn.commit(); st.rerun()

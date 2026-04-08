import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام إدارة جنوب نابلس 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    .school-title { color: #ffffff; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# رابط ملف الحسابات
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_pro_v3_2026.db", check_same_thread=False)
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

# --- 3. وظائف التحكم بالبيانات (إدارة) ---
def delete_record(table, id_val):
    c.execute(f"DELETE FROM {table} WHERE id_num=?", (id_val,))
    conn.commit()
    st.success(f"تم حذف السجل ذو الهوية {id_val} بنجاح")
    st.rerun()

def update_main_record(id_val, data_dict):
    query = "UPDATE main_table SET name=?, phone=?, city=?, village=?, job_title=?, desire=?, principal_note=? WHERE id_num=?"
    c.execute(query, (data_dict['name'], data_dict['phone'], data_dict['city'], data_dict['village'], data_dict['job'], data_dict['desire'], data_dict['note'], id_val))
    conn.commit()
    st.success("تم تحديث البيانات بنجاح")

# --- 4. تسجيل الدخول ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية جنوب نابلس")
    t1, t2 = st.tabs(["🔐 المدارس", "🛠️ الإدارة"])
    with t1:
        u = st.text_input("رقم المدرسة").strip()
        p = st.text_input("المرور", type="password").strip()
        if st.button("دخول المدارس"):
            df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
            match = df_acc[(df_acc['school_user'].astype(str) == u) & (df_acc['password'].astype(str) == p)]
            if not match.empty:
                st.session_state.update({'auth':True, 'user_type':'school', 'school_user':u, 'school_display_name':match.iloc[0]['school_full_name']})
                st.rerun()
    with t2:
        if st.text_input("كلمة مرور الإدارة ", type="password") == "ADMIN2026":
            if st.button("دخول المسؤول"):
                st.session_state.update({'auth':True, 'user_type':'admin'})
                st.rerun()
    st.stop()

# --- 5. واجهة المدارس (مختصرة للتركيز على طلبك) ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    if st.sidebar.button("خروج"):
        st.session_state.clear()
        st.rerun()
    st.info("استخدم لوحة التحكم لتعبئة البيانات أو مراجعتها")
    # (هنا يوضع كود التعبئة السابق...)

# --- 6. لوحة الإدارة (التعديلات المطلوبة) ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ التحكم المركزي والتحرير - جنوب نابلس")
    if st.sidebar.button("تسجيل الخروج "):
        st.session_state.clear()
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📊 المراقبة", "📝 التوظيف", "✍️ التصحيح"])

    # وظيفة لعرض الجدول مع خيارات التعديل والحذف
    def render_admin_table(table_type, db_table):
        st.subheader(f"إدارة بيانات: {table_type}")
        
        # جلب البيانات
        if db_table == "main_table":
            df = pd.read_sql(f"SELECT * FROM main_table WHERE type='{table_type}'", conn)
        else:
            df = pd.read_sql("SELECT * FROM correction_table", conn)

        if df.empty:
            st.warning("لا توجد بيانات حالياً")
            return

        # قائمة منسدلة للمدارس
        schools_list = ["الكل"] + df['school_full_name'].unique().tolist()
        selected_school = st.selectbox(f"تصفية حسب المدرسة ({table_type}):", schools_list)
        
        display_df = df if selected_school == "الكل" else df[df['school_full_name'] == selected_school]
        
        # عرض الجدول
        st.dataframe(display_df, use_container_width=True)

        # عمليات التعديل والحذف
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            target_id = st.selectbox(f"اختر الهوية للإجراء ({table_type}):", [""] + display_df['id_num'].tolist())
        
        if target_id:
            row = display_df[display_df['id_num'] == target_id].iloc[0]
            
            c_edit, c_del = st.columns(2)
            with c_del:
                if st.button(f"🗑️ حذف سجل {target_id}", key=f"del_{target_id}_{table_type}"):
                    delete_record(db_table, target_id)
            
            with c_edit:
                st.write("📝 تعديل البيانات:")
                with st.expander("افتح لتعديل بيانات السجل المختار"):
                    new_name = st.text_input("الاسم", value=row['name'], key=f"n_{target_id}")
                    new_phone = st.text_input("الجوال", value=row['phone'], key=f"p_{target_id}")
                    
                    if st.button("💾 حفظ التعديلات", key=f"save_{target_id}"):
                        if db_table == "main_table":
                            c.execute("UPDATE main_table SET name=?, phone=? WHERE id_num=?", (new_name, new_phone, target_id))
                        else:
                            c.execute("UPDATE correction_table SET name=?, phone=? WHERE id_num=?", (new_name, new_phone, target_id))
                        conn.commit()
                        st.success("تم التعديل")
                        st.rerun()

    with tab1: render_admin_table("الثانوية العامة", "main_table")
    with tab2: render_admin_table("امتحان التوظيف", "main_table")
    with tab3: render_admin_table("التصحيح", "correction_table")

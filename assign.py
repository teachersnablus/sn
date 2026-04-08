import streamlit as st
import pandas as pd
import sqlite3
import io

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام مديرية جنوب نابلس 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { direction: rtl; text-align: right; }
    div[data-testid="stForm"] { text-align: right; border: 1px solid #ddd; padding: 20px; border-radius: 10px; }
    input, select, textarea { direction: rtl !important; text-align: right !important; }
    .school-title { color: #ffffff; background-color: #1E3A8A; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 25px; }
    .admin-header { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-right: 5px solid #1E3A8A; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# رابط ملف الحسابات
SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_final_system_2026.db", check_same_thread=False)
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

# --- 3. وظائف النظام ---
def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

def delete_record(table, id_val):
    c.execute(f"DELETE FROM {table} WHERE id_num=?", (id_val,))
    conn.commit()
    st.success(f"✅ تم حذف السجل {id_val}")
    st.rerun()

# --- 4. تسجيل الدخول ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    with tab1:
        u_in = st.text_input("رقم المدرسة").strip()
        p_in = st.text_input("كلمة المرور", type="password").strip()
        if st.button("تسجيل دخول المدارس"):
            try:
                df_acc = pd.read_csv(SCHOOLS_ACCOUNTS_URL)
                df_acc.columns = df_acc.columns.str.strip()
                match = df_acc[(df_acc['school_user'].astype(str) == u_in) & (df_acc['password'].astype(str) == p_in)]
                if not match.empty:
                    st.session_state.update({'auth': True, 'user_type': "school", 'school_user': u_in, 'school_display_name': str(match.iloc[0]['school_full_name'])})
                    st.rerun()
                else: st.error("❌ بيانات الدخول خاطئة")
            except: st.error("❌ فشل الاتصال بقاعدة بيانات الحسابات")
    with tab2:
        admin_pass = st.text_input("كلمة مرور الإدارة", type="password")
        if st.button("دخول المسؤول"):
            if admin_pass == "ADMIN2026":
                st.session_state.update({'auth': True, 'user_type': "admin"})
                st.rerun()
    st.stop()

# --- 5. واجهة المدارس ---
if st.session_state['user_type'] == "school":
    st.markdown(f"<div class='school-title'>🏢 مدرسة: {st.session_state['school_display_name']}</div>", unsafe_allow_html=True)
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    menu = st.sidebar.radio("القائمة:", ["تعبئة نماذج جديدة", "استعراض وتعديل وحذف بياناتنا"])

    if menu == "تعبئة نماذج جديدة":
        open_tawjihi = get_form_status('ثانوية')
        open_employment = get_form_status('توظيف')
        open_correct = get_form_status('تصحيح')
        t_m, t_c = st.tabs(["📝 مراقبة وتوظيف", "✍️ تصحيح الثانوية العامة"])
        
        with t_m:
            modes = []
            if open_tawjihi: modes.append("الثانوية العامة")
            if open_employment: modes.append("امتحان التوظيف")
            if not modes:
                st.warning("⚠️ جميع نماذج المراقبة والتوظيف مغلقة حالياً.")
            else:
                mode = st.radio("النموذج الحالي:", modes, horizontal=True)
                with st.form("school_main_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("الاسم رباعي")
                        id_num = st.text_input("رقم الهوية")
                        phone = st.text_input("رقم الجوال")
                    with col2:
                        city = st.text_input("المدينة")
                        village = st.text_input("القرية")
                        job = st.selectbox("الوظيفة", ["معلم", "مدير مدرسة", "سكرتير", "آذن"])
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية (إن وجد)")
                    rel_ex = st.text_input("امتحان القريب المباشر")
                    desire, note = "", ""
                    if mode == "الثانوية العامة":
                        c1, c2 = st.columns(2)
                        with c1: desire = st.radio("يرغب بالمراقبة؟", ["يرغب", "لا يرغب"], horizontal=True)
                        with c2: note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True)
                    else: desire = "توظيف"
                    if st.form_submit_button(f"💾 حفظ بيانات {mode}"):
                        if name and id_num:
                            c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                      (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, city, village, rel_ex, job, desire, note, mode))
                            conn.commit()
                            st.success("✅ تم الحفظ بنجاح")
                        else: st.error("⚠️ يرجى تعبئة الاسم والهوية")

        with t_c:
            if open_correct:
                with st.form("school_correct_form", clear_on_submit=True):
                    st.subheader("طلب تصحيح الثانوية العامة")
                    f1, f2 = st.columns(2)
                    with f1:
                        c_name = st.text_input("الاسم الرباعي ")
                        c_id = st.text_input("رقم الهوية ")
                        c_subj = st.selectbox("المبحث", ["اللغة العربية", "اللغة الانجليزية", "الرياضيات", "الكيمياء", "الفيزياء", "أخرى"])
                    with f2:
                        c_city = st.text_input("المدينة ")
                        c_vill = st.text_input("القرية ")
                        c_branch = st.selectbox("الفرع", ["الأدبي", "العلمي", "الريادة", "المهني"])
                    c_phone = st.text_input("رقم الجوال ")
                    has_rel = st.radio("قريب مباشر؟", ["لا", "نعم"], horizontal=True)
                    rel_dt = st.text_input("اسم وقرابة القريب (إن وجد)")
                    if st.form_submit_button("💾 حفظ طلب التصحيح"):
                        if c_name and c_id:
                            c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                      (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subj, c_branch, c_city, c_vill, has_rel, rel_dt, c_phone))
                            conn.commit()
                            st.success("✅ تم الحفظ")
            else:
                st.warning("⚠️ نموذج التصحيح مغلق حالياً.")

    elif menu == "استعراض وتعديل وحذف بياناتنا":
        st.subheader("🔍 السجلات الخاصة بمدرستكم")
        
        # جلب كل البيانات المتعلقة بالمدرسة
        df_m = pd.read_sql(f"SELECT * FROM main_table WHERE school_user='{st.session_state['school_user']}'", conn)
        df_c = pd.read_sql(f"SELECT * FROM correction_table WHERE school_user='{st.session_state['school_user']}'", conn)
        
        if df_m.empty and df_c.empty:
            st.info("لا توجد سجلات محفوظة لمدرستكم حالياً.")
        else:
            if not df_m.empty:
                st.write("📊 سجلات المراقبة والتوظيف:")
                st.dataframe(df_m, use_container_width=True)
            if not df_c.empty:
                st.write("✍️ سجلات التصحيح:")
                st.dataframe(df_c, use_container_width=True)
            
            st.divider()
            st.subheader("⚙️ أدوات التحكم (تعديل / حذف)")
            
            # دمج الهويات من الجدولين للاختيار
            all_ids = sorted(list(set(df_m['id_num'].tolist() + df_c['id_num'].tolist())))
            target_id = st.selectbox("اختر رقم هوية الموظف للإجراء:", [""] + all_ids)
            
            if target_id:
                # فحص في أي جدول موجود
                is_in_main = target_id in df_m['id_num'].values
                is_in_corr = target_id in df_c['id_num'].values
                
                # جلب البيانات الحالية
                if is_in_main:
                    row = df_m[df_m['id_num'] == target_id].iloc[0]
                else:
                    row = df_c[df_c['id_num'] == target_id].iloc[0]
                
                col_edit, col_del = st.columns(2)
                
                with col_edit:
                    with st.expander(f"📝 تعديل بيانات: {row['name']}"):
                        new_name = st.text_input("تعديل الاسم", value=row['name'], key="edit_name")
                        new_phone = st.text_input("تعديل الهاتف", value=row['phone'], key="edit_phone")
                        if st.button("💾 حفظ التعديلات الجديدة"):
                            if is_in_main:
                                c.execute("UPDATE main_table SET name=?, phone=? WHERE id_num=?", (new_name, new_phone, target_id))
                            if is_in_corr:
                                c.execute("UPDATE correction_table SET name=?, phone=? WHERE id_num=?", (new_name, new_phone, target_id))
                            conn.commit()
                            st.success("✅ تم تحديث البيانات")
                            st.rerun()
                
                with col_del:
                    st.write("⚠️ منطقة خطرة")
                    if st.button(f"🗑️ حذف السجل {target_id} نهائياً"):
                        c.execute("DELETE FROM main_table WHERE id_num=? AND school_user=?", (target_id, st.session_state['school_user']))
                        c.execute("DELETE FROM correction_table WHERE id_num=? AND school_user=?", (target_id, st.session_state['school_user']))
                        conn.commit()
                        st.success("✅ تم الحذف")
                        st.rerun()

# --- 6. لوحة الإدارة ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ التحكم المركزي والتحرير - جنوب نابلس")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

    adm_menu = st.sidebar.selectbox("الانتقال إلى:", ["إدارة البيانات (تعديل/حذف)", "الصلاحيات (فتح/إغلاق النماذج)"])

    if adm_menu == "الصلاحيات (فتح/إغلاق النماذج)":
        st.header("🔓 التحكم في استقبال الطلبات")
        cols = st.columns(3)
        forms = [('ثانوية', 'الثانوية العامة'), ('توظيف', 'امتحان التوظيف'), ('تصحيح', 'تصحيح الثانوية')]
        for i, (f_key, f_label) in enumerate(forms):
            with cols[i]:
                current_st = get_form_status(f_key)
                st.markdown(f"### {f_label}")
                st.write("الحالة الحالية:", "✅ مفتوح" if current_st else "❌ مغلق")
                if st.button(f"تغيير حالة {f_label}", key=f"btn_toggle_{f_key}"):
                    new_st = 0 if current_st else 1
                    c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (new_st, f_key))
                    conn.commit()
                    st.rerun()

    else:
        tab1, tab2, tab3 = st.tabs(["📊 المراقبة", "📝 التوظيف", "✍️ التصحيح"])
        def admin_view(table_label, db_type, is_correction=False):
            st.markdown(f"<div class='admin-header'>إدارة بيانات {table_label}</div>", unsafe_allow_html=True)
            df = pd.read_sql("SELECT * FROM correction_table", conn) if is_correction else pd.read_sql(f"SELECT * FROM main_table WHERE type='{db_type}'", conn)
            if df.empty:
                st.info("لا توجد بيانات حالياً.")
                return
            schools = ["الكل"] + sorted(df['school_full_name'].unique().tolist())
            sel_school = st.selectbox(f"تصفية حسب المدرسة ({table_label}):", schools)
            final_df = df if sel_school == "الكل" else df[df['school_full_name'] == sel_school]
            st.dataframe(final_df, use_container_width=True)
            target_id = st.selectbox(f"اختر الهوية للإجراء ({table_label}):", [""] + final_df['id_num'].tolist())
            if target_id:
                row = final_df[final_df['id_num'] == target_id].iloc[0]
                with st.expander(f"📝 تعديل بيانات: {row['name']}"):
                    new_n = st.text_input("الاسم", value=row['name'], key=f"n_{target_id}_{table_label}")
                    new_p = st.text_input("الهاتف", value=row['phone'], key=f"p_{target_id}_{table_label}")
                    if st.button("💾 حفظ التعديل", key=f"sv_{target_id}_{table_label}"):
                        tbl = "correction_table" if is_correction else "main_table"
                        c.execute(f"UPDATE {tbl} SET name=?, phone=? WHERE id_num=?", (new_n, new_p, target_id))
                        conn.commit()
                        st.success("تم التحديث")
                        st.rerun()
                if st.button(f"🗑️ حذف السجل {target_id}", key=f"del_{target_id}_{table_label}"):
                    delete_record("correction_table" if is_correction else "main_table", target_id)
        with tab1: admin_view("الثانوية العامة", "الثانوية العامة")
        with tab2: admin_view("امتحان التوظيف", "امتحان التوظيف")
        with tab3: admin_view("التصحيح", "", is_correction=True)

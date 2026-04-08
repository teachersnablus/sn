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
    .search-section { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px dashed #1E3A8A; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

SCHOOLS_ACCOUNTS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSOJxPb5ehu2HFPrbcqY2eXXkmjEu6-LVG-6klv03BNeskIF1JwoM3acLy2zTilT74FlFhQ0ohDVItT/pub?gid=1573939462&single=true&output=csv"

# --- 2. قاعدة البيانات ---
conn = sqlite3.connect("exams_system_final_v9.db", check_same_thread=False)
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

def get_form_status(form_name):
    c.execute("SELECT is_open FROM system_settings WHERE form_name=?", (form_name,))
    res = c.fetchone()
    return res[0] == 1 if res else True

# --- 3. تسجيل الدخول ---
if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'school_display_name': "", 'school_user': "", 'user_type': ""})

if not st.session_state['auth']:
    st.title("🏛️ بوابة مديرية التربية والتعليم - جنوب نابلس")
    tab1, tab2 = st.tabs(["🔐 دخول المدارس", "🛠️ دخول الإدارة"])
    with tab1:
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
            except: st.error("❌ فشل الاتصال")
    with tab2:
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

    menu = st.sidebar.radio("القائمة:", ["تعبئة وبحث (إدارة)", "استعراض السجلات (عرض فقط)"])

    if menu == "تعبئة وبحث (إدارة)":
        st.markdown("<div class='search-section'>🔎 <b>بحث وتعديل:</b> أدخل رقم الهوية لجلب البيانات. يمكنك الحفظ للتحديث أو الحذف من هنا.</div>", unsafe_allow_html=True)
        search_id = st.text_input("رقم الهوية:")
        
        found_row = None
        is_in_main = False
        if search_id:
            df_m = pd.read_sql(f"SELECT * FROM main_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
            if not df_m.empty:
                found_row = df_m.iloc[0]; is_in_main = True
            else:
                df_c = pd.read_sql(f"SELECT * FROM correction_table WHERE id_num='{search_id}' AND school_user='{st.session_state['school_user']}'", conn)
                if not df_c.empty:
                    found_row = df_c.iloc[0]; is_in_main = False

        if found_row is not None:
            if st.button("🗑️ حذف هذا السجل نهائياً من النظام"):
                c.execute("DELETE FROM main_table WHERE id_num=?", (search_id,))
                c.execute("DELETE FROM correction_table WHERE id_num=?", (search_id,))
                conn.commit(); st.success("✅ تم الحذف"); st.rerun()

        t_m, t_c = st.tabs(["📝 مراقبة وتوظيف", "✍️ تصحيح"])
        
        with t_m:
            if get_form_status('ثانوية') or get_form_status('توظيف'):
                mode = st.radio("نوع النموذج:", ["الثانوية العامة", "امتحان التوظيف"], horizontal=True)
                with st.form("main_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    name = col1.text_input("الاسم رباعي *", value=found_row['name'] if (found_row is not None and is_in_main) else "")
                    id_num = col2.text_input("رقم الهوية *", value=search_id)
                    phone = col1.text_input("رقم الجوال *", value=found_row['phone'] if (found_row is not None and is_in_main) else "")
                    city = col2.text_input("المدينة *", value=found_row['city'] if (found_row is not None and is_in_main) else "")
                    village = col1.text_input("القرية *", value=found_row['village'] if (found_row is not None and is_in_main) else "")
                    job = col2.selectbox("الوظيفة *", ["", "معلم", "مدير مدرسة", "سكرتير", "آذن"])
                    st.divider()
                    school2 = st.text_input("المدرسة الثانية (اختياري)", value=found_row['school2'] if (found_row is not None and is_in_main) else "")
                    rel_ex = st.text_input("القريب المباشر (اختياري)", value=found_row['relative_exam'] if (found_row is not None and is_in_main) else "")
                    desire = st.radio("الرغبة:", ["يرغب", "لا يرغب"], horizontal=True)
                    note = st.radio("رأي المدير:", ["يصلح", "لا يصلح"], horizontal=True)

                    if st.form_submit_button("💾 حفظ البيانات"):
                        if not (name and id_num and phone and city and village and job):
                            st.error("⚠️ يرجى تعبئة كافة الحقول الإجبارية")
                        else:
                            c.execute("INSERT OR REPLACE INTO main_table VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                      (id_num, name, st.session_state['school_user'], st.session_state['school_display_name'], school2, phone, city, village, rel_ex, job, desire, note, mode))
                            conn.commit(); st.success("✅ تم الحفظ بنجاح"); st.rerun()
            else: st.warning("النماذج مغلقة")

        with t_c:
            if get_form_status('تصحيح'):
                with st.form("corr_form", clear_on_submit=True):
                    c_name = st.text_input("الاسم الرباعي *", value=found_row['name'] if (found_row is not None and not is_in_main) else "")
                    c_id = st.text_input("رقم الهوية *", value=search_id)
                    c_phone = st.text_input("الجوال *", value=found_row['phone'] if (found_row is not None and not is_in_main) else "")
                    c_city = st.text_input("المدينة *", value=found_row['city'] if (found_row is not None and not is_in_main) else "")
                    c_subj = st.selectbox("المبحث *", ["", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "أخرى"])
                    if st.form_submit_button("💾 حفظ طلب التصحيح"):
                        if not (c_name and c_id and c_phone and c_city and c_subj):
                            st.error("⚠️ يرجى تعبئة الحقول الأساسية")
                        else:
                            c.execute("INSERT OR REPLACE INTO correction_table VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                      (c_id, c_name, st.session_state['school_user'], st.session_state['school_display_name'], c_subj, "", c_city, "", "", "", c_phone))
                            conn.commit(); st.success("✅ تم الحفظ"); st.rerun()

    elif menu == "استعراض السجلات (عرض فقط)":
        st.subheader("📊 السجلات المسجلة")
        df1 = pd.read_sql(f"SELECT * FROM main_table WHERE school_user='{st.session_state['school_user']}'", conn)
        df2 = pd.read_sql(f"SELECT * FROM correction_table WHERE school_user='{st.session_state['school_user']}'", conn)
        if not df1.empty: st.write("مراقبة وتوظيف:"); st.table(df1[['id_num', 'name', 'phone', 'job_title', 'type']])
        if not df2.empty: st.write("تصحيح:"); st.table(df2[['id_num', 'name', 'phone', 'subject']])

# --- 5. واجهة الإدارة (رجعت كما كانت) ---
elif st.session_state['user_type'] == "admin":
    st.title("🛠️ التحكم المركزي - الإدارة")
    if st.sidebar.button("خروج"): st.session_state.clear(); st.rerun()
    
    adm_menu = st.sidebar.selectbox("القائمة:", ["إدارة البيانات", "صلاحيات النماذج"])
    
    if adm_menu == "صلاحيات النماذج":
        cols = st.columns(3)
        for i, f in enumerate(['ثانوية', 'توظيف', 'تصحيح']):
            with cols[i]:
                curr = get_form_status(f)
                st.write(f"نموذج {f}: {'✅ مفتوح' if curr else '❌ مغلق'}")
                if st.button(f"تغيير الحالة لـ {f}", key=f"adm_t_{f}"):
                    c.execute("UPDATE system_settings SET is_open=? WHERE form_name=?", (0 if curr else 1, f))
                    conn.commit(); st.rerun()
    else:
        tab1, tab2, tab3 = st.tabs(["المراقبة", "التوظيف", "التصحيح"])
        def view_data(t_name, d_type, k_s, is_corr=False):
            df = pd.read_sql("SELECT * FROM correction_table", conn) if is_corr else pd.read_sql(f"SELECT * FROM main_table WHERE type='{d_type}'", conn)
            schools = ["الكل"] + sorted(df['school_full_name'].unique().tolist())
            sel = st.selectbox(f"مدرسة ({t_name}):", schools, key=f"sel_{k_s}")
            f_df = df if sel == "الكل" else df[df['school_full_name'] == sel]
            st.dataframe(f_df)
            target_del = st.selectbox(f"حذف هوية ({t_name}):", [""] + f_df['id_num'].tolist(), key=f"del_{k_s}")
            if st.button(f"تأكيد حذف {target_del}", key=f"btn_{k_s}"):
                if target_del:
                    c.execute(f"DELETE FROM {'correction_table' if is_corr else 'main_table'} WHERE id_num=?", (target_del,))
                    conn.commit(); st.rerun()
        
        with tab1: view_data("ثانوية عامة", "الثانوية العامة", "tw")
        with tab2: view_data("توظيف", "امتحان التوظيف", "em")
        with tab3: view_data("تصحيح", "", "cr", True)

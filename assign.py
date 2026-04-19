# كود تحديث قاعدة البيانات (تشغيل مرة واحدة فقط)
conn = sqlite3.connect("exams_system_final_v31.db", check_same_thread=False)
c = conn.cursor()

# إنشاء جداول جديدة بالهيكل المحدَّث
c.execute('''CREATE TABLE IF NOT EXISTS main_table_new
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              id_num TEXT, name TEXT, school_user TEXT, school_full_name TEXT, school2 TEXT, 
              phone TEXT, address TEXT, relative_exam TEXT, job_title TEXT, 
              desire TEXT, principal_note TEXT, type TEXT, gender TEXT)''')

c.execute('''INSERT INTO main_table_new (id_num, name, school_user, school_full_name, school2, 
              phone, address, relative_exam, job_title, desire, principal_note, type, gender)
             SELECT id_num, name, school_user, school_full_name, school2, 
              phone, address, relative_exam, job_title, desire, principal_note, type, gender 
              FROM main_table''')

c.execute("DROP TABLE main_table")
c.execute("ALTER TABLE main_table_new RENAME TO main_table")
conn.commit()
conn.close()

import streamlit as st
import sqlite3
import pandas as pd
import io
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SGS Pro Connect", page_icon="🇹🇭", layout="wide")

# --- CONSTANTS ---
DB_NAME = "sgs_database_v7.db" # <--- New Version for Class No.

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    
    # Added: class_no column
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            class_no TEXT,
            student_name TEXT,
            grade_level TEXT,
            room TEXT,
            subject TEXT,
            quarter TEXT,
            school_year TEXT,
            test1 REAL,
            test2 REAL,
            test3 REAL,
            final_score REAL,
            total_score REAL,
            recorded_by TEXT,
            photo BLOB,
            UNIQUE(student_id, subject, quarter, school_year)
        )
    """)
    conn.commit()
    conn.close()

# --- FUNCTIONS ---

def register_user(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def save_grade(s_id, cls_no, name, grade, room, subj, q, year, t1, t2, t3, final, teacher_name, photo_bytes):
    # Strict Validation
    if not s_id.strip() or not name.strip() or not subj.strip():
        return False, "⚠️ Error: ID, Name, and Subject are required."

    total = t1 + t2 + t3 + final
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # Check for existing photo
        c.execute("SELECT photo FROM grades WHERE student_id = ? AND subject = ? AND quarter = ? AND school_year = ?", (s_id, subj, q, year))
        existing_data = c.fetchone()
        
        final_photo = photo_bytes if photo_bytes else (existing_data[0] if existing_data else None)

        # Delete old record
        c.execute("DELETE FROM grades WHERE student_id = ? AND subject = ? AND quarter = ? AND school_year = ?", (s_id, subj, q, year))
        
        c.execute("""
            INSERT INTO grades (student_id, class_no, student_name, grade_level, room, subject, quarter, school_year, test1, test2, test3, final_score, total_score, recorded_by, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (s_id, cls_no, name, grade, room, subj, q, year, t1, t2, t3, final, total, teacher_name, final_photo))
        
        conn.commit()
        conn.close()
        return True, f"✅ Saved: No.{cls_no} {name}"
    except Exception as e:
        conn.close()
        return False, f"Database Error: {str(e)}"

def delete_record(record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM grades WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def get_grades(teacher_name):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM grades WHERE recorded_by = ?", conn, params=(teacher_name,))
    conn.close()
    return df

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
init_db()

# --- AUTH PAGE ---
def auth_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🇹🇭 Student Grading System")
        st.title("Professional Connect")
        st.caption("Official Online Grade Management Portal")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        with tab1:
            with st.form("login"):
                user = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if login_user(user, pwd):
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        st.rerun()
                    else:
                        st.error("Incorrect Password")
        with tab2:
            st.write("Teacher Registration")
            with st.form("reg"):
                u = st.text_input("Create Username")
                p = st.text_input("Create Password", type="password")
                c = st.text_input("School Master Code", type="password")
                if st.form_submit_button("Register"):
                    if c == "SK2025": 
                        if register_user(u, p): st.success("Registered! Go to Login.")
                        else: st.error("User taken")
                    else: st.error("Invalid Code")

# --- DASHBOARD ---
def dashboard():
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.markdown("---")
        st.write("⚠️ **Correction Tool**")
        del_id = st.number_input("ID to Delete", min_value=0)
        if st.button("Delete Record"):
            delete_record(del_id)
            st.success("Deleted")
            st.rerun()

    st.title("📊 SGS Teacher Dashboard")
    st.markdown("---")

    tab_input, tab_view = st.tabs(["📝 Input & Calculator", "📇 View Cards & Export"])

    # --- INPUT TAB ---
    with tab_input:
        st.subheader("1. Class Details")
        c_y, c_s, c_q = st.columns([1, 1, 1])
        with c_y: sch_year = st.selectbox("School Year", ["2024-2025", "2025-2026", "2026-2027"])
        with c_s: subject = st.text_input("Subject", placeholder="e.g. Math")
        with c_q: quarter = st.selectbox("Quarter", ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"], index=2)

        r1, r2 = st.columns(2)
        with r1: grade_lvl = st.selectbox("Level", ["M1", "M2", "M3", "M4", "M5", "M6"])
        with r2: room_num = st.selectbox("Room/Section", [str(i) for i in range(1, 16)])

        st.markdown("---")
        st.subheader("2. Student Data & Score Calculator")
        
        # Student Info Section
        c_info, c_photo = st.columns([3, 1])
        with c_info:
            co1, co2, co3 = st.columns([1, 2, 3])
            with co1: cls_no = st.text_input("Class No.", placeholder="01")
            with co2: s_id = st.text_input("Student ID")
            with co3: name = st.text_input("Student Name")
        with c_photo:
            st.write("📸 Photo")
            uploaded_file = st.file_uploader("Img", type=['jpg', 'png'], label_visibility="collapsed")
            photo_data = uploaded_file.getvalue() if uploaded_file else None

        st.info("💡 **How to use:** Enter the Student's Raw Score and the Max Score. The system will calculate the final weight automatically.")
        
        # --- SCORE CALCULATOR SECTION ---
        # We use Columns to create a "Calculator Layout"
        
        # TEST 1 (Max 10)
        st.markdown("##### 📘 Test 1 (Attendance/Participation) -> Max 10")
        t1_col1, t1_col2, t1_col3 = st.columns([1, 1, 1])
        with t1_col1: t1_raw = st.number_input("T1 Raw Score", 0.0, 100.0, 0.0, step=1.0)
        with t1_col2: t1_max = st.number_input("T1 Max Items", 1.0, 100.0, 10.0, step=1.0) # Default 10
        # Calculation
        t1_final = (t1_raw / t1_max) * 10
        with t1_col3: st.metric("Weighted Score", f"{t1_final:.2f} / 10")

        # TEST 2 (Max 10)
        st.markdown("##### 📗 Test 2 (Quizzes) -> Max 10")
        t2_col1, t2_col2, t2_col3 = st.columns([1, 1, 1])
        with t2_col1: t2_raw = st.number_input("T2 Raw Score", 0.0, 100.0, 0.0, step=1.0)
        with t2_col2: t2_max = st.number_input("T2 Max Items", 1.0, 100.0, 10.0, step=1.0)
        # Calculation
        t2_final = (t2_raw / t2_max) * 10
        with t2_col3: st.metric("Weighted Score", f"{t2_final:.2f} / 10")

        # TEST 3 (Max 10)
        st.markdown("##### 📙 Test 3 (Unit Test) -> Max 10")
        t3_col1, t3_col2, t3_col3 = st.columns([1, 1, 1])
        with t3_col1: t3_raw = st.number_input("T3 Raw Score", 0.0, 100.0, 0.0, step=1.0)
        with t3_col2: t3_max = st.number_input("T3 Max Items", 1.0, 100.0, 10.0, step=1.0)
        # Calculation
        t3_final = (t3_raw / t3_max) * 10
        with t3_col3: st.metric("Weighted Score", f"{t3_final:.2f} / 10")

        # FINAL (Max 20)
        st.markdown("##### 📕 Final Exam -> Max 20")
        tf_col1, tf_col2, tf_col3 = st.columns([1, 1, 1])
        with tf_col1: tf_raw = st.number_input("Final Raw Score", 0.0, 100.0, 0.0, step=1.0)
        with tf_col2: tf_max = st.number_input("Final Max Items", 1.0, 100.0, 20.0, step=1.0) # Default 20
        # Calculation
        tf_final = (tf_raw / tf_max) * 20
        with tf_col3: st.metric("Weighted Score", f"{tf_final:.2f} / 20")

        # Total Display
        total_calc = t1_final + t2_final + t3_final + tf_final
        st.markdown(f"### 🏆 Total Grade: {total_calc:.2f} / 50")

        if st.button("💾 Save Grade Record", use_container_width=True):
            # Save the CALCULATED scores (t1_final), not the raw ones
            success, msg = save_grade(s_id, cls_no, name, grade_lvl, room_num, subject, quarter, sch_year, t1_final, t2_final, t3_final, tf_final, st.session_state.username, photo_data)
            if success: st.success(msg)
            else: st.error(msg)

    # --- VIEW CARDS TAB ---
    with tab_view:
        st.header("Classroom Records")
        df = get_grades(st.session_state.username)
        
        if not df.empty:
            # FILTERS
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: f_year = st.selectbox("Filter Year", ["All"] + sorted(df['school_year'].unique().tolist()))
            with c_f2: f_subj = st.selectbox("Filter Subject", ["All"] + sorted(df['subject'].unique().tolist()))
            with c_f3: f_grade = st.selectbox("Filter Grade", ["All"] + sorted(df['grade_level'].unique().tolist()))
            
            # Apply Filters
            dff = df.copy()
            if f_year != "All": dff = dff[dff['school_year'] == f_year]
            if f_subj != "All": dff = dff[dff['subject'] == f_subj]
            if f_grade != "All": dff = dff[dff['grade_level'] == f_grade]

            st.success(f"Found {len(dff)} records.")
            
            # DISPLAY CARDS
            for index, row in dff.iterrows():
                with st.container():
                    c_img, c_info, c_score = st.columns([1, 3, 1])
                    
                    with c_img:
                        if row['photo']:
                            try:
                                image = Image.open(io.BytesIO(row['photo']))
                                st.image(image, width=100)
                            except: st.write("❌ Error")
                        else: st.write("👤")
                    
                    with c_info:
                        # Updated to show Class No.
                        st.subheader(f"No. {row['class_no']} - {row['student_name']}")
                        st.caption(f"ID: {row['student_id']} | {row['grade_level']}/{row['room']} | {row['subject']}")
                        # Show scores rounded to 2 decimals
                        st.write(f"Scores: {row['test1']:.2f} + {row['test2']:.2f} + {row['test3']:.2f} + {row['final_score']:.2f}")

                    with c_score:
                        st.metric("Total", f"{row['total_score']:.2f}/50")
                    st.markdown("---")

            # EXPORT
            df_export = dff.drop(columns=['photo'])
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # Reorder columns so Class No is first
                cols = ['class_no'] + [c for c in df_export.columns if c != 'class_no']
                df_export[cols].to_excel(writer, sheet_name='SGS_Export', index=False)
            
            st.download_button(
                label=f"📥 Download Excel", 
                data=buffer.getvalue(), 
                file_name=f"SGS_Grades.xlsx", 
                mime="application/vnd.ms-excel"
            )
        else:
            st.info("No data found.")

# --- MAIN ---
if st.session_state.logged_in:
    dashboard()
else:
    auth_page()
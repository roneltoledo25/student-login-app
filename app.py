import streamlit as st
import sqlite3
import pandas as pd
import io
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SGS Pro Connect", page_icon="🇹🇭", layout="wide")

# --- CONSTANTS ---
DB_NAME = "sgs_database_v6.db" # <--- New Database for School Year Support

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
    
    # Added: school_year column
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            grade_level TEXT,
            room TEXT,
            subject TEXT,
            quarter TEXT,
            school_year TEXT,
            test1 INTEGER,
            test2 INTEGER,
            test3 INTEGER,
            final_score INTEGER,
            total_score INTEGER,
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

def save_grade(s_id, name, grade, room, subj, q, year, t1, t2, t3, final, teacher_name, photo_bytes):
    # Strict Validation
    if not s_id.strip() or not name.strip() or not subj.strip():
        return False, "⚠️ Error: ID, Name, and Subject are required."

    total = t1 + t2 + t3 + final
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # Check for existing photo to preserve it
        c.execute("SELECT photo FROM grades WHERE student_id = ? AND subject = ? AND quarter = ? AND school_year = ?", (s_id, subj, q, year))
        existing_data = c.fetchone()
        
        final_photo = photo_bytes if photo_bytes else (existing_data[0] if existing_data else None)

        # Delete old record (specific to this Year/Quarter/Subject)
        c.execute("DELETE FROM grades WHERE student_id = ? AND subject = ? AND quarter = ? AND school_year = ?", (s_id, subj, q, year))
        
        c.execute("""
            INSERT INTO grades (student_id, student_name, grade_level, room, subject, quarter, school_year, test1, test2, test3, final_score, total_score, recorded_by, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (s_id, name, grade, room, subj, q, year, t1, t2, t3, final, total, teacher_name, final_photo))
        
        conn.commit()
        conn.close()
        return True, f"✅ Saved: {name} ({year})"
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
            # HIDDEN CODE: The text is removed. Only you know it is "SK2025"
            st.write("Teacher Registration Area") 
            with st.form("reg"):
                u = st.text_input("Create Username")
                p = st.text_input("Create Password", type="password")
                c = st.text_input("School Master Code", type="password") # This hides the typing
                
                if st.form_submit_button("Register"):
                    if c == "SK2025": # <--- LOGIC REMAINS, BUT USER DOESN'T SEE IT
                        if u and p:
                            if register_user(u, p): st.success("Registered! Go to Login.")
                            else: st.error("Username taken")
                        else: st.warning("Fill all fields")
                    else: st.error("⛔ Invalid Master Code")

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

    tab_input, tab_view = st.tabs(["📝 Input Grades", "📇 View Cards & Export"])

    # --- INPUT TAB ---
    with tab_input:
        st.subheader("1. Academic Year & Class Details")
        
        # ROW 1: Year & Subject
        c_y, c_s = st.columns([1, 2])
        with c_y:
            # SCHOOL YEAR SELECTOR
            sch_year = st.selectbox("School Year", ["2024-2025", "2025-2026", "2026-2027", "2027-2028"])
        with c_s:
            subject = st.text_input("Subject", placeholder="e.g. Math")

        # ROW 2: Quarter, Level, Room
        r1, r2, r3 = st.columns(3)
        with r1:
            quarter = st.selectbox("Quarter", ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"], index=2)
        with r2:
            grade_lvl = st.selectbox("Level", ["M1", "M2", "M3", "M4", "M5", "M6"])
        with r3:
            room_num = st.selectbox("Room/Section", [str(i) for i in range(1, 16)])

        st.markdown("---")
        st.subheader("2. Student Data")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.write("📸 **Photo**")
            uploaded_file = st.file_uploader("Upload", type=['jpg', 'png', 'jpeg'])
            if uploaded_file:
                st.image(uploaded_file, width=150)
                photo_data = uploaded_file.getvalue()
            else:
                photo_data = None

        with c2:
            col_a, col_b = st.columns(2)
            with col_a:
                s_id = st.text_input("Student ID")
                name = st.text_input("Student Name")
            with col_b:
                t1 = st.number_input("Test 1", 0, 10)
                t2 = st.number_input("Test 2", 0, 10)
                t3 = st.number_input("Test 3", 0, 10)
                final = st.number_input("Final", 0, 20)

        if st.button("💾 Save Grade", use_container_width=True):
            success, msg = save_grade(s_id, name, grade_lvl, room_num, subject, quarter, sch_year, t1, t2, t3, final, st.session_state.username, photo_data)
            if success: st.success(msg)
            else: st.error(msg)

    # --- VIEW CARDS TAB ---
    with tab_view:
        st.header("Classroom Records")
        df = get_grades(st.session_state.username)
        
        if not df.empty:
            # FILTERS
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                f_year = st.selectbox("Filter Year", ["All"] + sorted(df['school_year'].unique().tolist()))
            with c_f2:
                f_subj = st.selectbox("Filter Subject", ["All"] + sorted(df['subject'].unique().tolist()))
            with c_f3:
                f_grade = st.selectbox("Filter Grade", ["All"] + sorted(df['grade_level'].unique().tolist()))
            
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
                        else: st.write("👤 No Photo")
                    
                    with c_info:
                        st.subheader(f"{row['student_name']} ({row['grade_level']}/{row['room']})")
                        st.caption(f"ID: {row['student_id']} | {row['subject']} | {row['quarter']} | {row['school_year']}")
                        st.write(f"Scores: {row['test1']} + {row['test2']} + {row['test3']} + {row['final_score']}")

                    with c_score:
                        st.metric("Total", f"{row['total_score']}/50")
                    st.markdown("---")

            # EXPORT
            df_export = dff.drop(columns=['photo'])
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, sheet_name='SGS_Export', index=False)
            
            st.download_button(
                label=f"📥 Download Excel ({f_year})", 
                data=buffer.getvalue(), 
                file_name=f"SGS_{f_year}_Grades.xlsx", 
                mime="application/vnd.ms-excel"
            )
        else:
            st.info("No data found.")

# --- MAIN ---
if st.session_state.logged_in:
    dashboard()
else:
    auth_page()

# --- HIDE STREAMLIT DEFAULT UI ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}       /* Hide hamburger menu */
    footer {visibility: hidden;}          /* Hide footer */
    header {visibility: hidden;}          /* Hide header */
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

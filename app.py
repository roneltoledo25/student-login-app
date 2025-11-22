import streamlit as st
import sqlite3
import pandas as pd
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SGS Pro Connect", page_icon="🇹🇭", layout="wide")

# --- CONSTANTS ---
# I changed the name to v3 to ensure a fresh database is created with new columns
DB_NAME = "sgs_database_v3.db" 

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Table for TEACHERS
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    
    # 2. Table for GRADES
    # UNIQUE Constraint: A student cannot have 2 grades for the SAME Subject in the SAME Quarter.
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            subject TEXT,
            quarter TEXT,
            test1 INTEGER,
            test2 INTEGER,
            test3 INTEGER,
            final_score INTEGER,
            total_score INTEGER,
            recorded_by TEXT,
            UNIQUE(student_id, subject, quarter)
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

def save_grade(s_id, name, subj, q, t1, t2, t3, final, teacher_name):
    total = t1 + t2 + t3 + final
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # If a grade exists for this Student + Subject + Quarter, replace it.
    c.execute("""
        INSERT OR REPLACE INTO grades (student_id, student_name, subject, quarter, test1, test2, test3, final_score, total_score, recorded_by)
        VALUES ((SELECT student_id FROM grades WHERE student_id = ? AND subject = ? AND quarter = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (s_id, subj, q, name, subj, q, t1, t2, t3, final, total, teacher_name))
    
    # Fallback for simple Insert if replace logic gets complex in SQLite
    # We delete the old one first (if exists) then insert new to be safe
    c.execute("DELETE FROM grades WHERE student_id = ? AND subject = ? AND quarter = ?", (s_id, subj, q))
    c.execute("""
        INSERT INTO grades (student_id, student_name, subject, quarter, test1, test2, test3, final_score, total_score, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (s_id, name, subj, q, t1, t2, t3, final, total, teacher_name))
    
    conn.commit()
    conn.close()

def get_grades(teacher_name):
    """Get grades only for the specific teacher"""
    conn = sqlite3.connect(DB_NAME)
    # We filter so teachers only see the grades THEY added (optional, or remove WHERE to see all)
    df = pd.read_sql_query("SELECT * FROM grades WHERE recorded_by = ?", conn, params=(teacher_name,))
    conn.close()
    return df

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

init_db()

# --- AUTHENTICATION PAGES ---
def auth_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🇹🇭 Student Grading System")
        st.title("Professional Connect")
        st.caption("Official Online Grade Management Portal")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register New Teacher"])
        
        with tab1:
            with st.form("login_form"):
                user = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if login_user(user, pwd):
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        st.rerun()
                    else:
                        st.error("❌ Incorrect Username or Password")

        with tab2:
            st.info("School Master Code Required")
            with st.form("register_form"):
                new_user = st.text_input("Create Username")
                new_pwd = st.text_input("Create Password", type="password")
                school_code = st.text_input("School Master Code", type="password")
                
                if st.form_submit_button("Register"):
                    if school_code == "SK2025": 
                        if new_user and new_pwd:
                            if register_user(new_user, new_pwd):
                                st.success("✅ Account Created! Please Login.")
                            else:
                                st.error("⚠️ Username taken.")
                        else:
                            st.warning("Fill all fields.")
                    else:
                        st.error("⛔ Invalid School Code.")

# --- DASHBOARD PAGE ---
def dashboard():
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    st.title("📊 SGS Teacher Dashboard")
    st.markdown("---")

    tab_input, tab_view = st.tabs(["📝 Input Grades", "📂 View & Export"])

    # --- INPUT SECTION ---
    with tab_input:
        st.subheader("1. Select Subject & Quarter")
        c1, c2 = st.columns(2)
        with c1:
            # Teachers can type their subject here
            subject = st.text_input("Subject Name", placeholder="e.g. Mathematics, English, Science")
        with c2:
            # Default is set to 2 (Quarter 3) because lists start at 0
            quarter = st.selectbox("Quarter", ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"], index=2)

        st.markdown("---")
        st.subheader("2. Student Details & Scores")
        
        col_a, col_b = st.columns(2)
        with col_a:
            s_id = st.text_input("Student ID", placeholder="e.g. 101")
            name = st.text_input("Student Name", placeholder="e.g. Somsak")
        
        with col_b:
            t1 = st.number_input("Test 1 (Max 10)", 0, 10)
            t2 = st.number_input("Test 2 (Max 10)", 0, 10)
            t3 = st.number_input("Test 3 (Max 10)", 0, 10)
            final = st.number_input("Final (Max 20)", 0, 20)
            
        # Save Button
        if st.button("💾 Save Grade Record", use_container_width=True):
            if s_id and name and subject:
                save_grade(s_id, name, subject, quarter, t1, t2, t3, final, st.session_state.username)
                st.success(f"✅ Saved: {name} | {subject} | {quarter}")
            else:
                st.warning("⚠️ Please fill in Student ID, Name, and Subject.")

    # --- VIEW & EXPORT SECTION ---
    with tab_view:
        st.header("Class Records")
        
        # Filter options
        filter_q = st.selectbox("Filter by Quarter", ["All", "Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"], index=3)
        
        df = get_grades(st.session_state.username)
        
        if not df.empty:
            # Apply Filter
            if filter_q != "All":
                df = df[df['quarter'] == filter_q]

            st.dataframe(df)

            # Export Button
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='SGS_Grades', index=False)
                
            st.download_button(
                label=f"📥 Download Excel ({filter_q})",
                data=buffer.getvalue(),
                file_name=f"SGS_{filter_q}_Grades.xlsx",
                mime="application/vnd.ms-excel"
            )
        else:
            st.info("No records found. Go to 'Input Grades' to add data.")

# --- MAIN CONTROLLER ---
if st.session_state.logged_in:
    dashboard()
else:
    auth_page()
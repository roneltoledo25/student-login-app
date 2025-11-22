import streamlit as st
import sqlite3
import pandas as pd
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SGS Pro Connect", page_icon="🇹🇭", layout="wide")

# --- CONSTANTS ---
DB_NAME = "sgs_database_v4.db" 

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
    # STRICT VALIDATION: Prevent saving if ID or Name is empty
    if not s_id.strip() or not name.strip() or not subj.strip():
        return False, "⚠️ Error: Student ID, Name, and Subject cannot be empty."

    total = t1 + t2 + t3 + final
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # 1. Try to DELETE existing record (to avoid duplicates)
        c.execute("DELETE FROM grades WHERE student_id = ? AND subject = ? AND quarter = ?", (s_id, subj, q))
        
        # 2. INSERT new record
        c.execute("""
            INSERT INTO grades (student_id, student_name, subject, quarter, test1, test2, test3, final_score, total_score, recorded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (s_id, name, subj, q, t1, t2, t3, final, total, teacher_name))
        conn.commit()
        conn.close()
        return True, f"✅ Saved: {name} ({subj})"
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
if 'username' not in st.session_state:
    st.session_state.username = ""

init_db()

# --- AUTH PAGES ---
def auth_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("## 🇹🇭 Student Grading System")
        st.title("Professional Connect")
        st.caption("Official Online Grade Management Portal")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
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
            st.info("Code Required: SK2025")
            with st.form("register_form"):
                new_user = st.text_input("Username")
                new_pwd = st.text_input("Password", type="password")
                code = st.text_input("School Master Code", type="password")
                
                if st.form_submit_button("Register"):
                    if code == "SK2025": 
                        if new_user and new_pwd:
                            if register_user(new_user, new_pwd):
                                st.success("✅ Account Created!")
                            else:
                                st.error("⚠️ Username taken.")
                    else:
                        st.error("⛔ Invalid Code.")

# --- DASHBOARD ---
def dashboard():
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
        
        st.markdown("---")
        st.write("⚠️ **Correction Tool**")
        del_id = st.number_input("ID to Delete", min_value=0, step=1)
        if st.button("Delete Record ID"):
            delete_record(del_id)
            st.success(f"Deleted Record ID: {del_id}")
            st.rerun()

    st.title("📊 SGS Teacher Dashboard")
    st.markdown("---")

    tab_input, tab_view = st.tabs(["📝 Input Grades", "📂 View & Export"])

    # --- INPUT TAB ---
    with tab_input:
        c1, c2 = st.columns(2)
        with c1:
            subject = st.text_input("Subject Name", placeholder="e.g. Mathematics")
        with c2:
            quarter = st.selectbox("Quarter", ["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"], index=2)

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            s_id = st.text_input("Student ID", placeholder="e.g. 101")
            name = st.text_input("Student Name", placeholder="e.g. Somsak")
        
        with col_b:
            t1 = st.number_input("Test 1", 0, 10)
            t2 = st.number_input("Test 2", 0, 10)
            t3 = st.number_input("Test 3", 0, 10)
            final = st.number_input("Final", 0, 20)
            
        if st.button("💾 Save Grade Record", use_container_width=True):
            success, msg = save_grade(s_id, name, subject, quarter, t1, t2, t3, final, st.session_state.username)
            if success:
                st.success(msg)
            else:
                st.error(msg)

    # --- VIEW & EXPORT TAB ---
    with tab_view:
        st.header("Filter & Export Records")
        
        df = get_grades(st.session_state.username)
        
        if not df.empty:
            # 1. GET LIST OF SUBJECTS FROM DATABASE
            unique_subjects = df['subject'].unique().tolist()
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                # FILTER BY SUBJECT
                filter_subj = st.selectbox("Filter by Subject", ["All Subjects"] + unique_subjects)
            with col_f2:
                # FILTER BY QUARTER
                filter_q = st.selectbox("Filter by Quarter", ["All Quarters", "Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"], index=3)

            # APPLY FILTERS
            df_filtered = df.copy()
            if filter_subj != "All Subjects":
                df_filtered = df_filtered[df_filtered['subject'] == filter_subj]
            
            if filter_q != "All Quarters":
                df_filtered = df_filtered[df_filtered['quarter'] == filter_q]

            # SHOW TABLE
            st.write(f"Showing **{len(df_filtered)}** students found.")
            st.dataframe(df_filtered)

            # EXPORT BUTTON
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_filtered.to_excel(writer, sheet_name='SGS_Export', index=False)
            
            file_name_label = f"SGS_{filter_subj}_{filter_q}.xlsx"
            
            st.download_button(
                label=f"📥 Download Excel ({filter_subj})",
                data=buffer.getvalue(),
                file_name=file_name_label,
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
        else:
            st.info("No records found yet.")

# --- MAIN CONTROLLER ---
if st.session_state.logged_in:
    dashboard()
else:
    auth_page()
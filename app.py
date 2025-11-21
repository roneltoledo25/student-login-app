import streamlit as st
import sqlite3
import pandas as pd
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SGS Pro Connect", page_icon="🇹🇭", layout="wide")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    
    # 1. Table for TEACHERS
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    
    # 2. Table for GRADES
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            student_id TEXT PRIMARY KEY,
            student_name TEXT,
            test1 INTEGER,
            test2 INTEGER,
            test3 INTEGER,
            final_score INTEGER,
            total_score INTEGER,
            recorded_by TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- FUNCTIONS ---

def register_user(username, password):
    try:
        conn = sqlite3.connect('student.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False # Username already exists

def login_user(username, password):
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def save_grade(s_id, name, t1, t2, t3, final, teacher_name):
    total = t1 + t2 + t3 + final
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO grades (student_id, student_name, test1, test2, test3, final_score, total_score, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (s_id, name, t1, t2, t3, final, total, teacher_name))
    conn.commit()
    conn.close()

def get_all_grades():
    conn = sqlite3.connect('student.db')
    df = pd.read_sql_query("SELECT * FROM grades", conn)
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
        st.title("🇹🇭 SGS Pro Connect")
        st.write("Online Grading System for Teachers")
        
        # TABS: LOGIN vs REGISTER
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register New Teacher"])
        
        # --- LOGIN TAB ---
        with tab1:
            with st.form("login_form"):
                user = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Login")
                
                if btn_login:
                    if login_user(user, pwd):
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        st.rerun()
                    else:
                        st.error("❌ Incorrect Username or Password")

        # --- REGISTER TAB ---
        with tab2:
            st.info("Please enter the School Master Code to register.")
            with st.form("register_form"):
                new_user = st.text_input("Create Username")
                new_pwd = st.text_input("Create Password", type="password")
                school_code = st.text_input("School Master Code", type="password")
                btn_reg = st.form_submit_button("Register")
                
                if btn_reg:
                    if school_code == "SK2025": # <--- THIS IS YOUR SECRET CODE
                        if new_user and new_pwd:
                            if register_user(new_user, new_pwd):
                                st.success("✅ Account Created! Please switch to Login tab.")
                            else:
                                st.error("⚠️ Username already taken.")
                        else:
                            st.warning("Please fill all fields.")
                    else:
                        st.error("⛔ Invalid School Master Code.")

# --- DASHBOARD PAGE ---

def dashboard():
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    st.title("📊 SGS Grading Dashboard (Q1)")
    st.markdown("---")

    tab_input, tab_export = st.tabs(["📝 Input Grades", "📥 Export Excel"])

    # --- INPUT SECTION ---
    with tab_input:
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Student Info")
            s_id = st.text_input("Student ID", placeholder="e.g. 101")
            name = st.text_input("Student Name", placeholder="e.g. Somsak")
        
        with col_b:
            st.subheader("Scores (10-10-10-20)")
            t1 = st.number_input("Test 1 (Max 10)", 0, 10)
            t2 = st.number_input("Test 2 (Max 10)", 0, 10)
            t3 = st.number_input("Test 3 (Max 10)", 0, 10)
            final = st.number_input("Final (Max 20)", 0, 20)
            
        if st.button("💾 Save Grade", use_container_width=True):
            if s_id and name:
                save_grade(s_id, name, t1, t2, t3, final, st.session_state.username)
                st.success(f"Saved: {name} (Total: {t1+t2+t3+final})")
            else:
                st.warning("Enter ID and Name.")

        st.markdown("### 📋 Class Record Preview")
        df = get_all_grades()
        if not df.empty:
            st.dataframe(df.tail(10), hide_index=True)

    # --- EXPORT SECTION ---
    with tab_export:
        st.header("Download for SGS Upload")
        st.write("Download the class record in Excel format.")
        
        df_all = get_all_grades()
        if not df_all.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_all.to_excel(writer, sheet_name='SGS_Q1', index=False)
                
            st.download_button(
                label="📥 Download Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="SGS_Grades_Q1.xlsx",
                mime="application/vnd.ms-excel"
            )
            st.dataframe(df_all)
        else:
            st.info("No grades recorded yet.")

# --- MAIN CONTROLLER ---
if st.session_state.logged_in:
    dashboard()
else:
    auth_page()
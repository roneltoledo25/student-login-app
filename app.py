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
    
    # 1. Table for TEACHERS (Login)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    
    # 2. Table for STUDENT GRADES (SGS Format)
    # We verify if columns exist to avoid errors if you run this on old DB
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            student_id TEXT PRIMARY KEY,
            student_name TEXT,
            test1 INTEGER,
            test2 INTEGER,
            test3 INTEGER,
            final_score INTEGER,
            total_score INTEGER
        )
    """)
    conn.commit()
    conn.close()

# --- FUNCTIONS ---

def login_user(username, password):
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def save_grade(s_id, name, t1, t2, t3, final):
    total = t1 + t2 + t3 + final
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    # This command performs "INSERT OR REPLACE" 
    # (If student ID exists, it updates the score. If not, it creates new.)
    c.execute("""
        INSERT OR REPLACE INTO grades (student_id, student_name, test1, test2, test3, final_score, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (s_id, name, t1, t2, t3, final, total))
    conn.commit()
    conn.close()

def get_all_grades():
    conn = sqlite3.connect('student.db')
    df = pd.read_sql_query("SELECT * FROM grades", conn)
    conn.close()
    return df

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
init_db()

# --- PAGES ---

def login_page():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🇹🇭 SGS Pro Connect")
        st.write("Sign in to manage student grades.")
        
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            btn = st.form_submit_button("Login to System")
            
            if btn:
                if login_user(user, pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Incorrect Username or Password")

def dashboard():
    # Sidebar
    with st.sidebar:
        st.title(f"Teacher: {st.session_state.username}")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()
    
    st.title("📊 Grading Dashboard (Quarter 1)")
    st.markdown("---")

    # TWO TABS: One for Input, One for Export
    tab1, tab2 = st.tabs(["📝 Input Grades", "📥 Export for SGS"])

    # --- TAB 1: INPUT GRADES ---
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Student Details")
            s_id = st.text_input("Student ID (No.)", placeholder="e.g., 1001")
            name = st.text_input("Student Name", placeholder="e.g., Somchai Jai-dee")
        
        with col2:
            st.subheader("Quarter 1 Scores")
            # Limits set to 10, 10, 10, 20 as requested
            t1 = st.number_input("Test 1 (Max 10)", 0, 10)
            t2 = st.number_input("Test 2 (Max 10)", 0, 10)
            t3 = st.number_input("Test 3 (Max 10)", 0, 10)
            final = st.number_input("Final Exam (Max 20)", 0, 20)
        
        if st.button("💾 Save Student Grade", use_container_width=True):
            if s_id and name:
                save_grade(s_id, name, t1, t2, t3, final)
                st.success(f"✅ Saved: {name} (Total: {t1+t2+t3+final}/50)")
            else:
                st.warning("⚠️ Please enter Student ID and Name.")

        # Quick Preview of Data
        st.markdown("### 📋 Recent Updates")
        df = get_all_grades()
        st.dataframe(df.tail(5), hide_index=True)

    # --- TAB 2: EXPORT TO EXCEL ---
    with tab2:
        st.header("Download Excel for SGS Upload")
        st.write("This will generate an .xlsx file with all student scores.")
        
        df_all = get_all_grades()
        
        if not df_all.empty:
            # Convert DataFrame to Excel in memory
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_all.to_excel(writer, sheet_name='SGS_Upload', index=False)
                
            # Download Button
            st.download_button(
                label="📥 Download SGS Excel File (.xlsx)",
                data=buffer.getvalue(),
                file_name="SGS_Quarter1_Grades.xlsx",
                mime="application/vnd.ms-excel"
            )
            
            st.dataframe(df_all, hide_index=True)
        else:
            st.info("No data to export yet. Please add students in the Input tab.")

# --- MAIN APP CONTROL ---
if st.session_state.logged_in:
    dashboard()
else:
    login_page()

# --- ADMIN SETUP (Run once to create your user) ---
# Uncomment the lines below, run the app once, then comment them out again!
conn = sqlite3.connect('student.db')
c = conn.cursor()
c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("teacher", "1234"))
conn.commit()
conn.close()
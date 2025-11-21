import streamlit as st
import sqlite3
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="School Grading System", page_icon="🏫")

# --- 1. DATABASE FUNCTIONS ---
def init_db():
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    # Table for Users (Teachers/Admins)
    c.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT UNIQUE,
            Password TEXT
        )
    """)
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    c.execute("SELECT * FROM student WHERE Username = ? AND Password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def add_user(username, password):
    try:
        conn = sqlite3.connect('student.db')
        c = conn.cursor()
        c.execute("INSERT INTO student (Username, Password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# Initialize DB on startup
init_db()

# --- 2. SESSION STATE (The Memory) ---
# This checks: "Is someone logged in right now?"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# --- 3. THE LOGOUT FUNCTION ---
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# --- 4. THE LOGIN PAGE (What they see first) ---
def login_page():
    st.title("🏫 Teacher Login Portal")
    
    with st.form("login_form"):
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if login_user(user, pwd):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success("Login Successful!")
                st.rerun() # Reload the page to show the dashboard
            else:
                st.error("❌ Invalid Username or Password")

# --- 5. THE ADMIN PANEL (For YOU only) ---
def admin_page():
    st.header("Admin Panel (Add Teachers)")
    
    # Registration Form
    with st.form("register_teacher"):
        new_user = st.text_input("New Teacher Username")
        new_pwd = st.text_input("New Teacher Password", type="password")
        admin_code = st.text_input("Admin Security Code", type="password")
        
        if st.form_submit_button("Add Teacher"):
            if admin_code == "2527": # Your secret code
                if add_user(new_user, new_pwd):
                    st.success(f"Teacher {new_user} added!")
                else:
                    st.error("Username already taken.")
            else:
                st.error("Wrong Admin Code!")

    # View Users Table
    st.markdown("---")
    if st.checkbox("Show Database"):
        conn = sqlite3.connect('student.db')
        df = pd.read_sql_query("SELECT * FROM student", conn)
        conn.close()
        st.dataframe(df)

# --- 6. THE GRADING DASHBOARD (The Goal) ---
def grading_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        logout()
    
    st.title("📝 Student Grading System")
    st.write("Here is where you will input grades.")
    
    # --- PLACEHOLDER FOR GRADING LOGIC ---
    # Next step: We will build the table to save grades here!
    
    tab1, tab2 = st.tabs(["Input Grades", "View Report Card"])
    
    with tab1:
        st.info("Select a student and enter their grade below.")
        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("Student Name")
        with col2:
            grade = st.number_input("Grade", 0, 100)
        
        if st.button("Save Grade"):
            st.toast(f"Saved grade {grade} for {student_name}")
            # We need to create a database table for this next!

# --- 7. MAIN APP CONTROLLER ---
# This decides which page to show

sidebar_choice = st.sidebar.radio("Navigation", ["Login / Dashboard", "Admin Panel"])

if sidebar_choice == "Admin Panel":
    admin_page()
else:
    if st.session_state.logged_in:
        grading_dashboard()
    else:
        login_page()
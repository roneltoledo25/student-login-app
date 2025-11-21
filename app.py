import pandas as pd
import streamlit as st
import sqlite3

# --- PAGE SETUP ---
st.set_page_config(page_title="Student Registration", page_icon="🎓")

# --- HIDE STREAMLIT STYLE (Optional, makes it look cleaner) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- DATABASE FUNCTIONS ---
def init_db():
    """Initializes the SQLite database."""
    try:
        # Connect to SQLite (creates the file 'student.db' if it doesn't exist)
        conn = sqlite3.connect('student.db')
        c = conn.cursor()
        
        # Create table (Note: SQLite syntax is slightly different from MySQL)
        c.execute("""
            CREATE TABLE IF NOT EXISTS student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE,
                Password TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database Error: {e}")

def add_user(username, password):
    """Adds a user to the database."""
    try:
        conn = sqlite3.connect('student.db')
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT * FROM student WHERE Username = ?", (username,))
        if c.fetchone():
            return False, "Username already taken."
        
        # Insert new user
        c.execute("INSERT INTO student (Username, Password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True, "User added successfully!"
    except Exception as e:
        return False, f"Error: {e}"

# --- RUN DATABASE SETUP ---
init_db()

# --- THE WEB INTERFACE ---
st.title("New User Registration")
st.write("Enter details to register a new student account.")

# We use a 'form' so the page doesn't reload until you hit Submit
with st.form("register_form"):
    
    # The Input Fields
    # Note: 'type="password"' hides the text, just like show="*" in Tkinter
    admin_code = st.text_input("Admin Code", type="password", placeholder="Enter Admin Code")
    username = st.text_input("Username", placeholder="Create a UserID")
    password = st.text_input("Password", type="password", placeholder="Create a Password")
    
    # The Submit Button
    submitted = st.form_submit_button("ADD NEW USER")

# --- THE LOGIC (Runs when button is clicked) ---
if submitted:
    # 1. Check Admin Code
    if admin_code != "2527":
        st.error("❌ Incorrect Admin Code! You are not authorized.")
        
    # 2. Check Empty Fields
    elif not username or username == "UserID":
        st.warning("⚠️ Username cannot be empty!")
        
    elif not password or password == "Password":
        st.warning("⚠️ Password cannot be empty!")
        
    # 3. Try to Register
    else:
        success, message = add_user(username, password)
        if success:
            st.success(f"✅ {message}")
            st.balloons() # A fun animation!
        else:
            st.error(f"❌ {message}")

# --- VIEW USERS ON PAGE ---
if st.checkbox("Show All Registered Users"):
    conn = sqlite3.connect('student.db')
    c = conn.cursor()
    
    # Get the data
    c.execute("SELECT * FROM student")
    data = c.fetchall()
    conn.close()

    # Create a nicely labeled table
    # We assume the columns are: ID, Username, Password (based on your CREATE TABLE code)
    df = pd.DataFrame(data, columns=["ID", "Username", "Password"])
    
    # Display it!
    st.table(df)

    # --- DOWNLOAD DATABASE SECTION ---
st.markdown("---")

# 1. Read the database file as binary data
with open("student.db", "rb") as file:
    btn = st.download_button(
        label="📥 Download Database File",
        data=file,
        file_name="student.db",
        mime="application/octet-stream"
    )
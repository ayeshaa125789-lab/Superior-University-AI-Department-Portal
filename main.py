import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import os
from datetime import datetime

# ------------------ FILE PATHS ------------------
USER_FILE = "users.csv"
COURSE_FILE = "courses.csv"

# ------------------ INITIAL SETUP ------------------
def init_files():
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["username", "password", "role", "name", "roll"])
        df.to_csv(USER_FILE, index=False)
    else:
        df = pd.read_csv(USER_FILE)
        for col in ["username", "password", "role", "name", "roll"]:
            if col not in df.columns:
                df[col] = ""
        save_data(df, USER_FILE)

    if not os.path.exists(COURSE_FILE):
        df = pd.DataFrame(columns=["course_id", "course_name", "teacher"])
        df.to_csv(COURSE_FILE, index=False)

    # Create default admin if not exists
    df = pd.read_csv(USER_FILE)
    if "admin" not in df['username'].values:
        admin_user = pd.DataFrame([["admin", "admin123", "Admin", "Administrator", ""]], columns=df.columns)
        df = pd.concat([df, admin_user], ignore_index=True)
        df.to_csv(USER_FILE, index=False)

init_files()

# ------------------ LOAD & SAVE ------------------
def load_data(file_path):
    return pd.read_csv(file_path)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# ------------------ USER MANAGEMENT ------------------
def add_user(username, password, role, name="", roll=""):
    df = load_data(USER_FILE)

    # Check if username exists
    if username in df['username'].values:
        st.warning("User already exists!")
        return

    # Ensure CSV has all columns
    for col in ["username", "password", "role", "name", "roll"]:
        if col not in df.columns:
            df[col] = ""

    # Add new user
    new_user = pd.DataFrame([[username, password, role, name, roll]], columns=df.columns)
    df = pd.concat([df, new_user], ignore_index=True)
    save_data(df, USER_FILE)
    st.success(f"{role} added successfully!")

# ------------------ LOGIN ------------------
def login():
    st.title("Superior University AI Portal - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        df = load_data(USER_FILE)
        user = df[(df['username'] == username) & (df['password'] == password)]
        if not user.empty:
            role = user.iloc[0]['role']
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['role'] = role
        else:
            st.error("Invalid username or password!")

# ------------------ DASHBOARD ------------------
def dashboard():
    role = st.session_state['role']
    st.title(f"Welcome, {st.session_state['username']} ({role})")

    if role == "Admin":
        with st.expander("➕ Add User"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            name = st.text_input("Name")
            role_select = st.selectbox("Role", ["Teacher", "Student"])
            roll = st.text_input("Roll No (for Students only)")
            if st.button("Add User"):
                add_user(username, password, role_select, name, roll)

        with st.expander("➕ Add Course"):
            c_id = st.text_input("Course ID")
            c_name = st.text_input("Course Name")
            teacher = st.text_input("Teacher Name")
            if st.button("Add Course"):
                df = load_data(COURSE_FILE)
                new_course = pd.DataFrame([[c_id, c_name, teacher]], columns=df.columns)
                df = pd.concat([df, new_course], ignore_index=True)
                save_data(df, COURSE_FILE)
                st.success("Course added successfully!")

    elif role == "Teacher":
        st.write("### Your Courses")
        df = load_data(COURSE_FILE)
        courses = df[df['teacher'] == st.session_state['username']]
        st.table(courses if not courses.empty else "No courses assigned yet.")

    elif role == "Student":
        st.write("### Available Courses")
        df = load_data(COURSE_FILE)
        st.table(df if not df.empty else "No courses available.")

# ------------------ SESSION HANDLING ------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    dashboard()
else:
    login()

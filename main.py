import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ------------------ FILE PATHS ------------------
USER_FILE = "users.csv"
COURSE_FILE = "courses.csv"

# ------------------ FUNCTIONS ------------------

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

def init_files():
    # Initialize users file
    if not os.path.exists(USER_FILE):
        df = pd.DataFrame(columns=["username", "password", "role", "name", "roll"])
        save_data(df, USER_FILE)
    # Initialize courses file
    if not os.path.exists(COURSE_FILE):
        df = pd.DataFrame(columns=["course_id", "course_name", "teacher"])
        save_data(df, COURSE_FILE)

def load_users():
    return pd.read_csv(USER_FILE)

def load_courses():
    return pd.read_csv(COURSE_FILE)

def add_user(username, password, role, name, roll):
    df = load_users()
    if username in df['username'].values:
        st.warning("User already exists!")
        return
    new_user = pd.DataFrame([[username, password, role, name, roll]], columns=df.columns)
    df = pd.concat([df, new_user], ignore_index=True)
    save_data(df, USER_FILE)
    st.success(f"{role} added successfully!")

def add_course(course_id, course_name, teacher):
    df = load_courses()
    if course_id in df['course_id'].values:
        st.warning("Course already exists!")
        return
    new_course = pd.DataFrame([[course_id, course_name, teacher]], columns=df.columns)
    df = pd.concat([df, new_course], ignore_index=True)
    save_data(df, COURSE_FILE)
    st.success(f"Course {course_name} added successfully!")

def login(username, password):
    df = load_users()
    user = df[(df['username']==username) & (df['password']==password)]
    if not user.empty:
        return user.iloc[0]['role']
    else:
        return None

# ------------------ INITIALIZE ------------------
init_files()

# ------------------ APP ------------------
st.title("Superior University AI Department Portal")

# ------------------ LOGIN ------------------
st.header("Login")
username = st.text_input("Username")
password = st.text_input("Password", type="password")
if st.button("Login"):
    role = login(username, password)
    if role == "Admin":
        st.success("Logged in as Admin")
        st.write("### ➕ Add User")
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        role_select = st.selectbox("Role", ["Teacher", "Student"])
        name = st.text_input("Name")
        roll = st.text_input("Roll No (for students)")
        if st.button("Add User"):
            add_user(new_username, new_password, role_select, name, roll)
        st.write("### ➕ Add Course")
        course_id = st.text_input("Course ID")
        course_name = st.text_input("Course Name")
        teacher_name = st.text_input("Teacher Name")
        if st.button("Add Course"):
            add_course(course_id, course_name, teacher_name)

    elif role == "Teacher":
        st.success(f"Logged in as Teacher: {username}")
        st.write("### Students List")
        df = load_users()
        st.dataframe(df[df['role']=="Student"])
        st.write("### Your Courses")
        courses = load_courses()
        st.dataframe(courses[courses['teacher']==username])

    elif role == "Student":
        st.success(f"Logged in as Student: {username}")
        courses = load_courses()
        st.write("### Available Courses")
        st.dataframe(courses)

    else:
        st.error("Invalid username or password")

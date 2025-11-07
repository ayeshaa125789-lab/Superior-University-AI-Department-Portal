import streamlit as st
import pandas as pd
import os
import time

# --------------------- PAGE CONFIG --------------------- #
st.set_page_config(page_title="AI Department Portal | Superior University", layout="wide")

# --------------------- STYLES --------------------- #
st.markdown("""
    <style>
    body {
        background-color: #000;
        color: white;
    }
    .main-title {
        text-align: center;
        color: #bb86fc;
        font-size: 40px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sub-title {
        text-align: center;
        color: #a87df0;
        font-size: 20px;
        margin-bottom: 30px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #8e2de2, #4a00e0);
        color: white;
        border: none;
        border-radius: 10px;
        height: 50px;
        font-size: 18px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #9b59b6, #6a0dad);
    }
    .card {
        background: linear-gradient(145deg, #4a00e0, #8e2de2);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        color: white;
        font-size: 18px;
        box-shadow: 0 0 15px #8e2de2;
        transition: 0.3s;
    }
    .card:hover {
        transform: scale(1.05);
        box-shadow: 0 0 30px #9b59b6;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------- FILE SETUP --------------------- #
def ensure_file(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

ensure_file("teachers.csv", ["username", "password", "name"])
ensure_file("students.csv", ["roll_no", "name", "semester", "password"])
ensure_file("courses.csv", ["course_name", "semester"])
ensure_file("attendance.csv", ["roll_no", "course", "status"])
ensure_file("results.csv", ["roll_no", "course", "marks", "grade", "gpa"])
ensure_file("announcements.csv", ["message"])
ensure_file("feedback.csv", ["roll_no", "message"])

# --------------------- LOGIN --------------------- #
st.markdown("<div class='main-title'>AI Department Portal</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Superior University</div>", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user = None

if not st.session_state.logged_in:
    username = st.text_input("Username / Roll No")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.session_state.user = "Administrator"
        else:
            t_df = pd.read_csv("teachers.csv")
            s_df = pd.read_csv("students.csv")

            if not t_df.empty and username in t_df["username"].values:
                user = t_df[t_df["username"] == username].iloc[0]
                if password == user["password"]:
                    st.session_state.logged_in = True
                    st.session_state.role = "teacher"
                    st.session_state.user = user["name"]
            elif not s_df.empty and username in s_df["roll_no"].values:
                user = s_df[s_df["roll_no"] == username].iloc[0]
                if password == user["password"]:
                    st.session_state.logged_in = True
                    st.session_state.role = "student"
                    st.session_state.user = user["name"]
            else:
                st.error("Invalid username or password!")
    st.stop()

# --------------------- SIDEBAR --------------------- #
st.sidebar.title(f"Welcome, {st.session_state.user}")
st.sidebar.write(f"Role: **{st.session_state.role.capitalize()}**")
menu = []

if st.session_state.role == "admin":
    menu = ["Dashboard", "Add Teacher", "Add Student", "Add Course",
            "Results", "Announcements", "Feedback", "Logout"]
elif st.session_state.role == "teacher":
    menu = ["Dashboard", "Mark Attendance", "Add Results", "View Students", "Logout"]
else:
    menu = ["Dashboard", "My Attendance", "My Results", "Announcements", "Feedback", "Logout"]

choice = st.sidebar.radio("Navigation", menu)

# --------------------- DASHBOARD --------------------- #
if choice == "Dashboard":
    st.markdown("<h2 style='color:#bb86fc;'>Dashboard Overview</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    stu_count = len(pd.read_csv("students.csv"))
    cour_count = len(pd.read_csv("courses.csv"))
    ann_count = len(pd.read_csv("announcements.csv"))

    with col1:
        st.markdown(f"<div class='card'>👨‍🎓<br>Total Students<br><b>{stu_count}</b></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'>📘<br>Total Courses<br><b>{cour_count}</b></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'>📢<br>Announcements<br><b>{ann_count}</b></div>", unsafe_allow_html=True)

# --------------------- ADMIN FEATURES --------------------- #
if st.session_state.role == "admin":

    if choice == "Add Teacher":
        st.subheader("Add New Teacher")
        name = st.text_input("Teacher Name")
        uname = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Add Teacher"):
            df = pd.read_csv("teachers.csv")
            df.loc[len(df)] = [uname, pw, name]
            df.to_csv("teachers.csv", index=False)
            st.success("Teacher added successfully!")

    elif choice == "Add Student":
        st.subheader("Add New Student")
        roll = st.text_input("Roll Number")
        name = st.text_input("Student Name")
        sem = st.selectbox("Semester", [f"Semester {i}" for i in range(1, 9)])
        pw = st.text_input("Password", type="password")
        if st.button("Add Student"):
            df = pd.read_csv("students.csv")
            df.loc[len(df)] = [roll, name, sem, pw]
            df.to_csv("students.csv", index=False)
            st.success("Student added successfully!")

    elif choice == "Add Course":
        st.subheader("Add New Course")
        cname = st.text_input("Course Name")
        sem = st.selectbox("Semester", [f"Semester {i}" for i in range(1, 9)])
        if st.button("Add Course"):
            df = pd.read_csv("courses.csv")
            df.loc[len(df)] = [cname, sem]
            df.to_csv("courses.csv", index=False)
            st.success("Course added successfully!")

    elif choice == "Results":
        st.subheader("All Results")
        df = pd.read_csv("results.csv")
        st.dataframe(df)

    elif choice == "Announcements":
        st.subheader("Add Announcement")
        msg = st.text_area("Enter announcement")
        if st.button("Post Announcement"):
            df = pd.read_csv("announcements.csv")
            df.loc[len(df)] = [msg]
            df.to_csv("announcements.csv", index=False)
            st.success("Announcement posted!")

    elif choice == "Feedback":
        st.subheader("Student Feedback")
        df = pd.read_csv("feedback.csv")
        st.dataframe(df)

# --------------------- TEACHER FEATURES --------------------- #
if st.session_state.role == "teacher":
    if choice == "Mark Attendance":
        st.subheader("Mark Attendance")
        students = pd.read_csv("students.csv")
        course = st.text_input("Course Name")
        for i, row in students.iterrows():
            status = st.radio(f"{row['name']} ({row['roll_no']})", ["Present", "Absent"], key=i)
            if st.button(f"Save {row['roll_no']}", key=f"s{i}"):
                df = pd.read_csv("attendance.csv")
                df.loc[len(df)] = [row['roll_no'], course, status]
                df.to_csv("attendance.csv", index=False)
                st.success(f"Attendance saved for {row['name']}")

    elif choice == "Add Results":
        st.subheader("Add Student Results")
        roll = st.text_input("Student Roll No")
        course = st.text_input("Course Name")
        marks = st.number_input("Marks", 0, 100)
        grade = st.selectbox("Grade", ["A", "B", "C", "D", "F"])
        gpa = st.number_input("GPA", 0.0, 4.0)
        if st.button("Add Result"):
            df = pd.read_csv("results.csv")
            df.loc[len(df)] = [roll, course, marks, grade, gpa]
            df.to_csv("results.csv", index=False)
            st.success("Result added successfully!")

    elif choice == "View Students":
        st.subheader("All Students")
        df = pd.read_csv("students.csv")
        st.dataframe(df)

# --------------------- STUDENT FEATURES --------------------- #
if st.session_state.role == "student":
    if choice == "My Attendance":
        st.subheader("My Attendance")
        df = pd.read_csv("attendance.csv")
        df = df[df["roll_no"] == username]
        st.dataframe(df)

    elif choice == "My Results":
        st.subheader("My Results")
        df = pd.read_csv("results.csv")
        df = df[df["roll_no"] == username]
        st.dataframe(df)

    elif choice == "Announcements":
        st.subheader("Announcements")
        df = pd.read_csv("announcements.csv")
        for msg in df["message"]:
            st.info(msg)

    elif choice == "Feedback":
        st.subheader("Send Feedback")
        msg = st.text_area("Write your feedback")
        if st.button("Send"):
            df = pd.read_csv("feedback.csv")
            df.loc[len(df)] = [username, msg]
            df.to_csv("feedback.csv", index=False)
            st.success("Feedback sent!")

# --------------------- LOGOUT --------------------- #
if choice == "Logout":
    st.session_state.logged_in = False
    st.experimental_rerun()

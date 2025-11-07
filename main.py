import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Superior University - AI Department", layout="wide")

# Theme colors
PRIMARY_COLOR = "#9b59b6"  # purple
BACKGROUND_COLOR = "#000000"  # black
TEXT_COLOR = "#ffffff"

# Apply custom CSS
st.markdown(f"""
    <style>
        body {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
        }}
        .stApp {{
            background-color: {BACKGROUND_COLOR};
        }}
        .main-title {{
            color: {PRIMARY_COLOR};
            text-align: center;
            font-size: 40px;
            font-weight: bold;
        }}
        .sub-title {{
            color: {PRIMARY_COLOR};
            text-align: center;
            font-size: 20px;
        }}
        .stButton > button {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border-radius: 10px;
            width: 100%;
            height: 50px;
            font-size: 18px;
        }}
    </style>
""", unsafe_allow_html=True)

# Ensure CSV files exist
def ensure_file(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

ensure_file("users.csv", ["role", "username", "password"])
ensure_file("students.csv", ["roll_no", "name", "semester", "password"])
ensure_file("courses.csv", ["course_name", "semester"])
ensure_file("attendance.csv", ["roll_no", "course", "status"])
ensure_file("results.csv", ["roll_no", "course", "marks", "grade", "gpa"])
ensure_file("announcements.csv", ["message"])
ensure_file("feedback.csv", ["roll_no", "message"])

# Admin credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# Login
st.markdown("<div class='main-title'>Superior University</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>AI Department Portal</div>", unsafe_allow_html=True)
st.write("")

username = st.text_input("Username")
password = st.text_input("Password", type="password")
login_btn = st.button("Login")

if login_btn:
    if username == ADMIN_USER and password == ADMIN_PASS:
        role = "admin"
    else:
        users = pd.read_csv("students.csv")
        match = users[(users["roll_no"] == username) & (users["password"] == password)]
        if not match.empty:
            role = "student"
        else:
            st.error("Invalid login credentials!")
            role = None
else:
    role = None

# ---------------- ADMIN PANEL ---------------- #
if role == "admin":
    st.sidebar.title("Admin Dashboard")
    choice = st.sidebar.radio("Select Option", [
        "Add Student", "View Students", "Add Course", "View Courses",
        "Mark Attendance", "Add Results", "View Results",
        "Announcements", "View Feedback"
    ])

    if choice == "Add Student":
        st.subheader("➕ Add New Student")
        roll = st.text_input("Roll Number")
        name = st.text_input("Full Name")
        sem = st.selectbox("Semester", [f"Semester {i}" for i in range(1, 9)])
        pw = st.text_input("Set Password", type="password")
        if st.button("Add Student"):
            df = pd.read_csv("students.csv")
            if roll in df["roll_no"].values:
                st.warning("Student already exists!")
            else:
                df.loc[len(df)] = [roll, name, sem, pw]
                df.to_csv("students.csv", index=False)
                st.success("Student added successfully!")

    elif choice == "View Students":
        st.subheader("📋 All Students")
        df = pd.read_csv("students.csv")
        st.dataframe(df)

    elif choice == "Add Course":
        st.subheader("➕ Add Course")
        cname = st.text_input("Course Name")
        sem = st.selectbox("Select Semester", [f"Semester {i}" for i in range(1, 9)])
        if st.button("Add Course"):
            df = pd.read_csv("courses.csv")
            df.loc[len(df)] = [cname, sem]
            df.to_csv("courses.csv", index=False)
            st.success("Course added successfully!")

    elif choice == "View Courses":
        st.subheader("📘 All Courses")
        df = pd.read_csv("courses.csv")
        st.dataframe(df)

    elif choice == "Mark Attendance":
        st.subheader("🗓 Mark Attendance")
        students = pd.read_csv("students.csv")
        courses = pd.read_csv("courses.csv")
        course = st.selectbox("Select Course", courses["course_name"])
        for i, row in students.iterrows():
            status = st.radio(f"{row['name']} ({row['roll_no']})", ["Present", "Absent"], key=i)
            if st.button(f"Save {row['roll_no']}", key=f"s{i}"):
                df = pd.read_csv("attendance.csv")
                df.loc[len(df)] = [row['roll_no'], course, status]
                df.to_csv("attendance.csv", index=False)
                st.success(f"Attendance saved for {row['name']}")

    elif choice == "Add Results":
        st.subheader("📊 Add Student Results")
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

    elif choice == "View Results":
        st.subheader("📈 All Results")
        df = pd.read_csv("results.csv")
        st.dataframe(df)

    elif choice == "Announcements":
        st.subheader("📢 Post Announcement")
        msg = st.text_area("Write your message here...")
        if st.button("Post"):
            df = pd.read_csv("announcements.csv")
            df.loc[len(df)] = [msg]
            df.to_csv("announcements.csv", index=False)
            st.success("Announcement posted!")

    elif choice == "View Feedback":
        st.subheader("💬 Student Feedback")
        df = pd.read_csv("feedback.csv")
        st.dataframe(df)

# ---------------- STUDENT PANEL ---------------- #
elif role == "student":
    st.sidebar.title("Student Dashboard")
    choice = st.sidebar.radio("Select Option", [
        "Profile", "Attendance", "Results", "Announcements", "Feedback"
    ])

    df = pd.read_csv("students.csv")
    student = df[df["roll_no"] == username].iloc[0]

    if choice == "Profile":
        st.subheader("👤 My Profile")
        st.write(f"**Name:** {student['name']}")
        st.write(f"**Roll Number:** {student['roll_no']}")
        st.write(f"**Semester:** {student['semester']}")

    elif choice == "Attendance":
        st.subheader("🗓 My Attendance")
        att = pd.read_csv("attendance.csv")
        att = att[att["roll_no"] == username]
        st.dataframe(att)

    elif choice == "Results":
        st.subheader("📊 My Results")
        res = pd.read_csv("results.csv")
        res = res[res["roll_no"] == username]
        st.dataframe(res)

    elif choice == "Announcements":
        st.subheader("📢 Announcements")
        df = pd.read_csv("announcements.csv")
        for msg in df["message"]:
            st.info(msg)

    elif choice == "Feedback":
        st.subheader("💬 Send Feedback")
        msg = st.text_area("Write your message")
        if st.button("Send"):
            df = pd.read_csv("feedback.csv")
            df.loc[len(df)] = [username, msg]
            df.to_csv("feedback.csv", index=False)
            st.success("Feedback sent successfully!")


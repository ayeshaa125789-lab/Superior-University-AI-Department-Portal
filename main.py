import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_option_menu import option_menu

# ------------------ FILE PATHS ------------------
USER_FILE = "users.csv"
COURSE_FILE = "courses.csv"
ATTEND_FILE = "attendance.csv"
RESULT_FILE = "results.csv"
NEWS_FILE = "news.csv"
FEEDBACK_FILE = "feedback.csv"

# ------------------ INITIAL SETUP (CSV Safe) ------------------
files_columns = {
    USER_FILE: ["username", "password", "role", "name", "roll"],
    COURSE_FILE: ["course_id", "course_name", "teacher"],
    ATTEND_FILE: ["roll", "course_id", "date", "status"],
    RESULT_FILE: ["roll", "course_id", "marks"],
    NEWS_FILE: ["date", "announcement"],
    FEEDBACK_FILE: ["roll", "feedback", "date"]
}

for file, columns in files_columns.items():
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

# ------------------ UTILITY FUNCTIONS ------------------
def load_data(file):
    return pd.read_csv(file)

def save_data(df, file):
    df.to_csv(file, index=False)

def login(username, password):
    df = load_data(USER_FILE)
    user = df[(df['username'] == username) & (df['password'] == password)]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

def add_course(course_id, course_name, teacher):
    df = load_data(COURSE_FILE)
    if course_id in df['course_id'].values:
        st.warning("Course ID already exists!")
        return
    new_course = pd.DataFrame([[course_id, course_name, teacher]], columns=df.columns)
    df = pd.concat([df, new_course], ignore_index=True)
    save_data(df, COURSE_FILE)
    st.success("Course added successfully!")

def mark_attendance(roll, course_id, status):
    df = load_data(ATTEND_FILE)
    new = pd.DataFrame([[roll, course_id, datetime.now().strftime("%Y-%m-%d"), status]], columns=df.columns)
    df = pd.concat([df, new], ignore_index=True)
    save_data(df, ATTEND_FILE)
    st.success("Attendance marked successfully!")

def post_news(announcement):
    df = load_data(NEWS_FILE)
    new = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), announcement]], columns=df.columns)
    df = pd.concat([df, new], ignore_index=True)
    save_data(df, NEWS_FILE)
    st.success("News posted successfully!")

def submit_feedback(roll, feedback):
    df = load_data(FEEDBACK_FILE)
    new = pd.DataFrame([[roll, feedback, datetime.now().strftime("%Y-%m-%d")]], columns=df.columns)
    df = pd.concat([df, new], ignore_index=True)
    save_data(df, FEEDBACK_FILE)
    st.success("Feedback submitted successfully!")

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Department Portal", layout="wide")

# ------------------ CUSTOM CSS ------------------
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #f5f0ff; }
    .css-1d391kg, .css-12oz5g7 { background-color: #ffffff !important; }
    .profile-box { text-align:center; padding:20px 10px; }
    .profile-name { font-weight:bold; color:#5E17EB; }
    .topbar { background-color:#5E17EB; padding:10px; color:white; border-radius:8px; margin-bottom:15px; }
    .metric-card { background:#f5f0ff; border-radius:10px; padding:20px; text-align:center; font-weight:bold; color:#5E17EB; box-shadow:2px 2px 8px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# ------------------ LOGIN SYSTEM ------------------
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h2 style='text-align:center;color:#5E17EB;'>🎓 Department Management Portal</h2>", unsafe_allow_html=True)
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == ADMIN_USER and password == ADMIN_PASS:
            st.session_state.user = {"username": ADMIN_USER, "role": "Admin", "name": "Administrator"}
            st.success("Admin login successful!")
        else:
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Welcome {user['name']} ({user['role']})")
            else:
                st.error("Invalid username or password.")
else:
    user = st.session_state.user

    # ------------------ SIDEBAR ------------------
    with st.sidebar:
        st.markdown(f"""
            <div class='profile-box'>
                <div style='font-size:60px;'>👤</div>
                <div class='profile-name'>{user['name']}</div>
                <div>{user['role']}</div>
            </div>
        """, unsafe_allow_html=True)

        choice = option_menu(
            menu_title="Menu",
            options=["Dashboard", "Courses", "Attendance", "Results", "News", "Feedback", "Logout"],
            icons=["speedometer", "book", "check2-square", "award", "newspaper", "chat", "box-arrow-right"],
            menu_icon="cast",
            default_index=0,
        )

    st.markdown(f"<div class='topbar'>🔔 Welcome {user['name']} ({user['role']})</div>", unsafe_allow_html=True)

    # ------------------ ADMIN PANEL ------------------
    if user['role'] == "Admin":
        if choice == "Dashboard":
            st.subheader("📊 Admin Dashboard")
            users = load_data(USER_FILE)
            courses = load_data(COURSE_FILE)

            col1, col2, col3 = st.columns(3)
            col1.markdown(f"<div class='metric-card'>👨‍🎓 Total Students<br>{len(users[users['role']=='Student'])}</div>", unsafe_allow_html=True)
            col2.markdown(f"<div class='metric-card'>👨‍🏫 Total Teachers<br>{len(users[users['role']=='Teacher'])}</div>", unsafe_allow_html=True)
            col3.markdown(f"<div class='metric-card'>📘 Total Courses<br>{len(courses)}</div>", unsafe_allow_html=True)

        elif choice == "News":
            st.subheader("📰 Manage Announcements")
            news_text = st.text_area("Write Announcement")
            if st.button("Post News"):
                post_news(news_text)
            st.dataframe(load_data(NEWS_FILE))

        elif choice == "Feedback":
            st.subheader("💬 Student Feedback")
            st.dataframe(load_data(FEEDBACK_FILE))

        elif choice == "Attendance":
            st.subheader("📋 Attendance Records")
            st.dataframe(load_data(ATTEND_FILE))

        elif choice == "Results":
            st.subheader("🏆 Results Summary")
            st.dataframe(load_data(RESULT_FILE))

        elif choice == "Logout":
            st.session_state.user = None
            st.rerun()

    # ------------------ TEACHER PANEL ------------------
    elif user['role'] == "Teacher":
        if choice == "Dashboard":
            st.subheader("📘 Teacher Dashboard")
        elif choice == "Courses":
            st.subheader("📚 Your Courses")
            df = load_data(COURSE_FILE)
            st.dataframe(df[df["teacher"] == user["username"]])

            st.write("### ➕ Add Course")
            course_id = st.text_input("Course ID")
            course_name = st.text_input("Course Name")
            if st.button("Add Course"):
                add_course(course_id, course_name, user["username"])

        elif choice == "Attendance":
            st.subheader("📋 Mark Attendance")
            roll = st.text_input("Student Roll No")
            course_id = st.text_input("Course ID")
            status = st.selectbox("Status", ["Present", "Absent"])
            if st.button("Mark Attendance"):
                mark_attendance(roll, course_id, status)

        elif choice == "Results":
            st.subheader("🏆 Add Results")
            roll = st.text_input("Student Roll")
            course_id = st.text_input("Course ID")
            marks = st.number_input("Marks", 0, 100)
            if st.button("Add Result"):
                df = load_data(RESULT_FILE)
                new = pd.DataFrame([[roll, course_id, marks]], columns=df.columns)
                df = pd.concat([df, new], ignore_index=True)
                save_data(df, RESULT_FILE)
                st.success("Result added successfully!")

        elif choice == "News":
            st.subheader("📰 News & Announcements")
            st.dataframe(load_data(NEWS_FILE))

        elif choice == "Logout":
            st.session_state.user = None
            st.rerun()

    # ------------------ STUDENT PANEL ------------------
    elif user['role'] == "Student":
        if choice == "Dashboard":
            st.subheader("🎓 Student Dashboard")
        elif choice == "Courses":
            st.subheader("📘 Enrolled Courses")
            st.dataframe(load_data(COURSE_FILE))
        elif choice == "Attendance":
            st.subheader("📋 Your Attendance")
            att = load_data(ATTEND_FILE)
            st.dataframe(att[att["roll"] == user["roll"]])
        elif choice == "Results":
            st.subheader("🏆 Your Results")
            res = load_data(RESULT_FILE)
            st.dataframe(res[res["roll"] == user["roll"]])
        elif choice == "News":
            st.subheader("📰 Latest Announcements")
            st.dataframe(load_data(NEWS_FILE))
        elif choice == "Feedback":
            st.subheader("💬 Submit Feedback")
            fb = st.text_area("Write Feedback")
            if st.button("Submit Feedback"):
                submit_feedback(user["roll"], fb)
        elif choice == "Logout":
            st.session_state.user = None
            st.rerun()

# app.py
# Superior University - AI Department Portal (Single-file)
# Features: Signup (any role), Login, role-based UI (Admin/Student),
# Students/Courses/Feedback/News stored in CSV, Purple theme.
# Save as app.py, upload to GitHub, deploy on Streamlit Cloud.

import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime

# -------------------- FILE PATHS --------------------
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
COURSES_FILE = "courses.csv"
FEEDBACK_FILE = "feedback.csv"
NEWS_FILE = "news.csv"

# -------------------- HELPERS --------------------
def ensure_csv(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def load_users() -> pd.DataFrame:
    ensure_csv(USERS_FILE, ["username","display_name","password_hash","role","email","created_at"])
    return pd.read_csv(USERS_FILE)

def save_users(df: pd.DataFrame):
    df.to_csv(USERS_FILE, index=False)

def user_exists(username: str) -> bool:
    df = load_users()
    return username in df['username'].astype(str).values

def create_user(username: str, display_name: str, password: str, role: str, email: str = ""):
    df = load_users()
    pw_hash = hash_password(password)
    now = datetime.utcnow().isoformat()
    new = pd.DataFrame([[username, display_name, pw_hash, role, email, now]], columns=df.columns)
    df = pd.concat([df, new], ignore_index=True)
    save_users(df)

def verify_user(username: str, password: str):
    df = load_users()
    row = df[df['username'].astype(str) == str(username)]
    if row.empty:
        return None
    if row.iloc[0]['password_hash'] == hash_password(password):
        return {
            "username": row.iloc[0]['username'],
            "display_name": row.iloc[0]['display_name'],
            "role": row.iloc[0]['role'],
            "email": row.iloc[0].get('email', "")
        }
    return None

# -------------------- ENSURE DATA FILES --------------------
ensure_csv(USERS_FILE, ["username","display_name","password_hash","role","email","created_at"])
ensure_csv(STUDENTS_FILE, ["Name","Roll No","Semester","Email"])
ensure_csv(COURSES_FILE, ["Course Name","Code","Instructor"])
ensure_csv(FEEDBACK_FILE, ["username","name","message","rating","created_at"])
ensure_csv(NEWS_FILE, ["title","details","created_at"])

# -------------------- PAGE STYLING --------------------
st.set_page_config(page_title="AI Dept Portal (Superior)", page_icon="💜", layout="wide")
st.markdown("""
    <style>
        .stApp { background: #fbf8ff; }
        .main-title { text-align:center; color:#5e17eb; font-size:34px; font-weight:700; padding:12px 0; }
        .card { background: #fff; border-radius:14px; padding:18px; box-shadow: 0 6px 18px rgba(94,23,235,0.06); margin-bottom:18px; }
        .stButton>button { background-color: #5e17eb; color: white; border-radius:10px; padding:8px 18px; border:none; }
        .stButton>button:hover { background-color:#7b3ff6; color:white; }
        .sidebar .sidebar-content { background: linear-gradient(180deg,#f3e9ff,#efe6ff); }
        .small-muted { color: #6b6b6b; font-size:12px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>💜 Superior University — AI Department Portal</div>", unsafe_allow_html=True)

# -------------------- AUTH STATE --------------------
if 'auth' not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None}

def logout():
    st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None}
    st.experimental_rerun()

# -------------------- SIDEBAR: LOGIN & SIGNUP --------------------
st.sidebar.header("Account")

if not st.session_state.auth["logged_in"]:
    tab = st.sidebar.radio("Action", ("Login","Sign up"))
    if tab == "Login":
        li_user = st.sidebar.text_input("Username", key="li_user")
        li_pw = st.sidebar.text_input("Password", type="password", key="li_pw")
        if st.sidebar.button("Login"):
            result = verify_user(li_user.strip(), li_pw)
            if result:
                st.session_state.auth = {"logged_in": True, "username": result['username'], "display_name": result['display_name'], "role": result['role']}
                st.sidebar.success(f"Logged in: {result['display_name']} ({result['role']})")
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid username or password.")
    else:  # Sign up
        st.sidebar.subheader("Create an account")
        su_name = st.sidebar.text_input("Full name", key="su_name")
        su_username = st.sidebar.text_input("Choose username", key="su_username")
        su_email = st.sidebar.text_input("Email (optional)", key="su_email")
        su_role = st.sidebar.selectbox("Role (select)", ["Student","Admin"], key="su_role")
        su_pw = st.sidebar.text_input("Password", type="password", key="su_pw")
        su_pw2 = st.sidebar.text_input("Confirm password", type="password", key="su_pw2")
        if st.sidebar.button("Sign up"):
            if not (su_name and su_username and su_pw and su_pw2):
                st.sidebar.warning("Please fill required fields.")
            elif su_pw != su_pw2:
                st.sidebar.warning("Passwords do not match.")
            elif user_exists(su_username.strip()):
                st.sidebar.warning("Username already exists. Choose another.")
            else:
                create_user(su_username.strip(), su_name.strip(), su_pw.strip(), su_role.strip(), su_email.strip())
                st.sidebar.success("Account created! Now login.")
else:
    st.sidebar.success(f"{st.session_state.auth['display_name']} ({st.session_state.auth['role']})")
    if st.sidebar.button("Logout"):
        logout()

# -------------------- PUBLIC VIEW IF NOT LOGGED IN --------------------
if not st.session_state.auth["logged_in"]:
    st.info("Please Sign up or Login from the sidebar to continue.")
    st.subheader("Latest Announcements")
    news = pd.read_csv(NEWS_FILE)
    if not news.empty:
        for _, r in news.sort_values("created_at", ascending=False).head(5).iterrows():
            st.markdown(f"**{r['title']}**")
            st.write(r['details'])
            st.caption(r['created_at'])
            st.write("---")
    else:
        st.write("No announcements yet.")
    st.stop()

# -------------------- AFTER LOGIN: ROLE-BASED UI --------------------
user = st.session_state.auth
st.sidebar.markdown("---")
st.sidebar.write("Logged in as:")
st.sidebar.write(f"**{user['display_name']}**")
st.sidebar.write(f"Role: `{user['role']}`")
st.sidebar.markdown("---")

if user['role'].lower() == 'admin':
    page = st.sidebar.selectbox("Admin Menu", ["Dashboard","Manage Students","Manage Courses","News","Feedback","Users"])
else:
    page = st.sidebar.selectbox("Student Menu", ["Home","My Profile","Courses","Submit Feedback","Announcements"])

# -------------------- ADMIN PAGES --------------------
if user['role'].lower() == 'admin':
    if page == "Dashboard":
        st.header("📊 Admin Dashboard")
        students = pd.read_csv(STUDENTS_FILE)
        courses = pd.read_csv(COURSES_FILE)
        feedback = pd.read_csv(FEEDBACK_FILE)
        st.metric("Students", len(students))
        st.metric("Courses", len(courses))
        st.metric("Feedbacks", len(feedback))
        st.subheader("Recent Feedback")
        if not feedback.empty:
            st.dataframe(feedback.sort_values("created_at", ascending=False).head(10))
        else:
            st.write("No feedback yet.")

    elif page == "Manage Students":
        st.header("👥 Manage Students")
        with st.expander("Add New Student"):
            s_name = st.text_input("Name", key="add_name")
            s_roll = st.text_input("Roll No", key="add_roll")
            s_sem = st.selectbox("Semester", ["1st","3rd"], key="add_sem")
            s_email = st.text_input("Email", key="add_stu_email")
            if st.button("Add Student", key="add_student_btn"):
                if s_name and s_roll:
                    df = pd.read_csv(STUDENTS_FILE)
                    if str(s_roll) in df['Roll No'].astype(str).values:
                        st.warning("Roll already exists.")
                    else:
                        new = pd.DataFrame([[s_name, s_roll, s_sem, s_email]], columns=df.columns)
                        df = pd.concat([df, new], ignore_index=True)
                        df.to_csv(STUDENTS_FILE, index=False)
                        st.success("Student added.")
                else:
                    st.warning("Provide name and roll.")

        st.subheader("All Students")
        st.dataframe(pd.read_csv(STUDENTS_FILE))

        with st.expander("Delete Student"):
            df = pd.read_csv(STUDENTS_FILE)
            if not df.empty:
                sel = st.selectbox("Select Roll to delete", df['Roll No'].astype(str).tolist(), key="del_student_sel")
                if st.button("Delete Student"):
                    df = df[df['Roll No'].astype(str) != sel]
                    df.to_csv(STUDENTS_FILE, index=False)
                    st.success("Deleted.")
            else:
                st.info("No students to delete.")

    elif page == "Manage Courses":
        st.header("📚 Manage Courses")
        with st.expander("Add Course"):
            c_name = st.text_input("Course Name", key="c_name")
            c_code = st.text_input("Course Code", key="c_code")
            c_instr = st.text_input("Instructor", key="c_instr")
            if st.button("Add Course", key="add_course_btn"):
                if c_name and c_code:
                    df = pd.read_csv(COURSES_FILE)
                    if str(c_code) in df['Code'].astype(str).values:
                        st.warning("Course code exists.")
                    else:
                        new = pd.DataFrame([[c_name, c_code, c_instr]], columns=df.columns)
                        df = pd.concat([df, new], ignore_index=True)
                        df.to_csv(COURSES_FILE, index=False)
                        st.success("Course added.")
                else:
                    st.warning("Provide course name and code.")
        st.subheader("All Courses")
        st.dataframe(pd.read_csv(COURSES_FILE))
        with st.expander("Delete Course"):
            df = pd.read_csv(COURSES_FILE)
            if not df.empty:
                sel = st.selectbox("Select Course Code to delete", df['Code'].astype(str).tolist(), key="del_course_sel")
                if st.button("Delete Course"):
                    df = df[df['Code'].astype(str) != sel]
                    df.to_csv(COURSES_FILE, index=False)
                    st.success("Deleted.")
            else:
                st.info("No courses to delete.")

    elif page == "News":
        st.header("📰 Manage News / Announcements")
        n_title = st.text_input("Title", key="news_title")
        n_details = st.text_area("Details", key="news_details")
        if st.button("Publish News"):
            if n_title and n_details:
                df = pd.read_csv(NEWS_FILE)
                now = datetime.utcnow().isoformat()
                new = pd.DataFrame([[n_title, n_details, now]], columns=df.columns)
                df = pd.concat([df, new], ignore_index=True)
                df.to_csv(NEWS_FILE, index=False)
                st.success("Published.")
            else:
                st.warning("Provide title and details.")
        st.subheader("All News")
        st.dataframe(pd.read_csv(NEWS_FILE).sort_values("created_at", ascending=False))

    elif page == "Feedback":
        st.header("💬 Student Feedback")
        df = pd.read_csv(FEEDBACK_FILE)
        if df.empty:
            st.write("No feedback yet.")
        else:
            st.dataframe(df.sort_values("created_at", ascending=False))
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download feedback CSV", csv, "feedback.csv")

    elif page == "Users":
        st.header("🔐 Users")
        users = load_users()
        st.dataframe(users[['username','display_name','role','email','created_at']])
        with st.expander("Create user manually"):
            u_name = st.text_input("Username", key="manual_u")
            u_display = st.text_input("Display name", key="manual_dn")
            u_email = st.text_input("Email", key="manual_email")
            u_role = st.selectbox("Role", ["Student","Admin"], key="manual_role")
            u_pw = st.text_input("Password", type="password", key="manual_pw")
            if st.button("Create User"):
                if not (u_name and u_display and u_pw):
                    st.warning("Fill required fields.")
                elif user_exists(u_name.strip()):
                    st.warning("Username exists.")
                else:
                    create_user(u_name.strip(), u_display.strip(), u_pw.strip(), u_role.strip(), u_email.strip())
                    st.success("User created.")

# -------------------- STUDENT PAGES --------------------
else:
    if page == "Home":
        st.header("Welcome Student")
        st.write("Use the menu to view courses, submit feedback, or read announcements.")
    elif page == "My Profile":
        st.header("🧾 My Profile")
        users = load_users()
        row = users[users['username'].astype(str) == user['username']]
        if not row.empty:
            r = row.iloc[0]
            st.write(f"**Username:** {r['username']}")
            st.write(f"**Name:** {r['display_name']}")
            st.write(f"**Role:** {r['role']}")
            if r.get('email', ""):
                st.write(f"**Email:** {r['email']}")
            st.write(f"**Joined:** {r['created_at']}")
        else:
            st.info("Profile not found.")
    elif page == "Courses":
        st.header("📘 Available Courses")
        df = pd.read_csv(COURSES_FILE)
        if df.empty:
            st.info("No courses added yet.")
        else:
            st.dataframe(df)
    elif page == "Submit Feedback":
        st.header("✉️ Submit Feedback")
        name = st.text_input("Your name", value=user['display_name'], key="fb_name")
        message = st.text_area("Message", key="fb_msg")
        rating = st.slider("Rating (1-5)", 1, 5, key="fb_rating")
        if st.button("Submit Feedback"):
            if name and message:
                df = pd.read_csv(FEEDBACK_FILE)
                now = datetime.utcnow().isoformat()
                new = pd.DataFrame([[user['username'], name, message, rating, now]], columns=df.columns)
                df = pd.concat([df, new], ignore_index=True)
                df.to_csv(FEEDBACK_FILE, index=False)
                st.success("Thank you — feedback submitted.")
            else:
                st.warning("Please fill name and message.")
    elif page == "Announcements":
        st.header("📰 Announcements")
        df = pd.read_csv(NEWS_FILE)
        if df.empty:
            st.info("No announcements yet.")
        else:
            for _, r in df.sort_values("created_at", ascending=False).iterrows():
                st.markdown(f"**{r['title']}**")
                st.write(r['details'])
                st.caption(r['created_at'])
                st.write("---")

# -------------------- FOOTER --------------------
st.markdown("---")
st.caption("AI Department Portal • Purple Superior theme • Single-file app (app.py).")

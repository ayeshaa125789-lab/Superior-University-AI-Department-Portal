import streamlit as st
import pandas as pd
import os
import hashlib

# ---------------- FILE PATHS ----------------
USER_FILE = "users.csv"
ASSIGNMENT_FILE = "assignments.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"
NEWS_FILE = "news.csv"
UPLOAD_FOLDER = "uploads"

for folder in [UPLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ---------------- HELPER FUNCTIONS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_csv(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
        return df

def save_csv(df, file):
    df.to_csv(file, index=False)

# --- USERS ---
def authenticate(username, password):
    users = load_csv(USER_FILE, ["username", "password", "role", "info"])
    hashed_pw = hash_password(password)
    user = users[(users['username'] == username) & (users['password'] == hashed_pw)]
    return not user.empty

def get_role(username):
    users = load_csv(USER_FILE, ["username", "password", "role", "info"])
    return users[users['username'] == username]['role'].values[0]

def add_user(username, password, role, info=""):
    users = load_csv(USER_FILE, ["username", "password", "role", "info"])
    if username in users['username'].values:
        return False
    new_user = pd.DataFrame({"username": [username],
                             "password": [hash_password(password)],
                             "role": [role],
                             "info": [info]})
    users = pd.concat([users, new_user], ignore_index=True)
    save_csv(users, USER_FILE)
    return True

def update_password(username, new_password):
    users = load_csv(USER_FILE, ["username", "password", "role", "info"])
    users.loc[users['username'] == username, 'password'] = hash_password(new_password)
    save_csv(users, USER_FILE)

# ---------------- ASSIGNMENTS ----------------
def upload_assignment(username, file):
    save_path = os.path.join(UPLOAD_FOLDER, f"{username}_{file.name}")
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    df = load_csv(ASSIGNMENT_FILE, ["username", "filename"])
    df = pd.concat([df, pd.DataFrame({"username": [username], "filename": [file.name]})], ignore_index=True)
    save_csv(df, ASSIGNMENT_FILE)

# ---------------- UI CONFIG ----------------
st.set_page_config(page_title="AI Department Portal", page_icon="🧠", layout="wide")

st.markdown("""
    <style>
        .main-title {
            background-color: #6A0DAD;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 10px;
            font-size: 32px;
            font-weight: bold;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #f2e6ff;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">AI Department Portal</div>', unsafe_allow_html=True)

# ---------------- SESSION ----------------
if 'login' not in st.session_state:
    st.session_state['login'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# ---------------- LOGIN ----------------
if not st.session_state['login']:
    st.subheader("Login Panel 🔑")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Default admin
    if not os.path.exists(USER_FILE):
        add_user("admin", "admin123", "admin", "Default Administrator")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state['login'] = True
            st.session_state['username'] = username
            st.session_state['role'] = get_role(username)
            st.success(f"Welcome, {username}!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password!")

# ---------------- LOGOUT ----------------
if st.session_state['login']:
    st.sidebar.info(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['login'] = False
        st.experimental_rerun()

# ---------------- ADMIN DASHBOARD ----------------
if st.session_state['login'] and st.session_state['role'] == "admin":
    st.subheader("Admin Dashboard ⚙️")
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Manage Users", "📚 Courses", "📰 News", "💬 Feedback"])

    # Manage Users
    with tab1:
        st.write("### Add New User")
        new_username = st.text_input("Username (Roll No for students)")
        new_password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["student", "teacher", "admin"])
        info = st.text_area("Additional Info (e.g., student details)")
        if st.button("Add User"):
            if add_user(new_username, new_password, role, info):
                st.success("User added successfully!")
            else:
                st.error("User already exists!")
        st.write("### Current Users")
        st.dataframe(load_csv(USER_FILE, ["username", "password", "role", "info"]))

    # Courses
    with tab2:
        st.write("### Manage Courses")
        st.info("Admin can upload course outlines or materials here (feature expandable).")

    # News
    with tab3:
        st.write("### Add / View News")
        news_df = load_csv(NEWS_FILE, ["title", "content"])
        title = st.text_input("News Title")
        content = st.text_area("News Content")
        if st.button("Add News"):
            new_news = pd.DataFrame({"title": [title], "content": [content]})
            news_df = pd.concat([news_df, new_news], ignore_index=True)
            save_csv(news_df, NEWS_FILE)
            st.success("News added!")
        st.dataframe(news_df)

    # Feedback
    with tab4:
        st.write("### Student Feedback")
        if os.path.exists("feedback.csv"):
            st.dataframe(pd.read_csv("feedback.csv"))
        else:
            st.info("No feedback yet.")

# ---------------- TEACHER DASHBOARD ----------------
if st.session_state['login'] and st.session_state['role'] == "teacher":
    st.subheader("Teacher Dashboard 🍎")
    tab1, tab2 = st.tabs(["📋 Attendance", "📊 Marks"])
    
    with tab1:
        st.write("### Mark Attendance")
        users = load_csv(USER_FILE, ["username", "password", "role", "info"])
        students = users[users["role"] == "student"]["username"].tolist()
        attendance = {student: st.checkbox(student) for student in students}
        if st.button("Save Attendance"):
            df = load_csv(ATTENDANCE_FILE, ["student", "status"])
            for student, present in attendance.items():
                df = pd.concat([df, pd.DataFrame({"student": [student], "status": ["Present" if present else "Absent"]})], ignore_index=True)
            save_csv(df, ATTENDANCE_FILE)
            st.success("Attendance Saved!")

    with tab2:
        st.write("### Update Marks")
        student = st.selectbox("Select Student", load_csv(USER_FILE, ["username", "password", "role", "info"])["username"].tolist())
        marks = st.number_input("Enter Marks", 0, 100)
        if st.button("Save Marks"):
            df = load_csv(MARKS_FILE, ["student", "marks"])
            df = pd.concat([df, pd.DataFrame({"student": [student], "marks": [marks]})], ignore_index=True)
            save_csv(df, MARKS_FILE)
            st.success("Marks saved successfully!")

# ---------------- STUDENT DASHBOARD ----------------
if st.session_state['login'] and st.session_state['role'] == "student":
    st.subheader("Student Dashboard 🎓")
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "📁 Assignments", "📊 Marks", "💬 Feedback"])

    with tab1:
        st.write("Username:", st.session_state['username'])
        users = load_csv(USER_FILE, ["username", "password", "role", "info"])
        info = users[users['username'] == st.session_state['username']]['info'].values[0]
        st.write("Info:", info)
        st.write("### Change Password")
        old_pw = st.text_input("Old Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            if authenticate(st.session_state['username'], old_pw):
                update_password(st.session_state['username'], new_pw)
                st.success("Password updated!")
            else:
                st.error("Old password is incorrect!")

    with tab2:
        st.write("### Upload Assignment")
        uploaded_file = st.file_uploader("Choose file", type=["pdf", "docx", "txt"])
        if st.button("Upload Assignment"):
            if uploaded_file:
                upload_assignment(st.session_state['username'], uploaded_file)
                st.success("Assignment uploaded!")
            else:
                st.warning("Please select a file first!")

    with tab3:
        st.write("### Your Marks")
        marks_df = load_csv(MARKS_FILE, ["student", "marks"])
        student_marks = marks_df[marks_df["student"] == st.session_state['username']]
        st.dataframe(student_marks)

    with tab4:
        st.write("### Submit Feedback")
        feedback = st.text_area("Write your feedback or suggestion")
        if st.button("Submit Feedback"):
            df = load_csv("feedback.csv", ["username", "feedback"])
            df = pd.concat([df, pd.DataFrame({"username": [st.session_state['username']], "feedback": [feedback]})], ignore_index=True)
            save_csv(df, "feedback.csv")
            st.success("Feedback submitted successfully!")

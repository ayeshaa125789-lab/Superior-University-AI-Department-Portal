import streamlit as st
import pandas as pd
import os
import hashlib

# ------------------ FILE PATHS ------------------
USER_FILE = "users.csv"
COURSE_FILE = "courses.csv"
ASSIGNMENT_FILE = "assignments.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"
FEEDBACK_FILE = "feedback.csv"
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ------------------ HELPER FUNCTIONS ------------------
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

def authenticate(username, password):
    users = load_csv(USER_FILE, ["username", "password", "role"])
    hashed_pw = hash_password(password)
    user = users[(users["username"] == username) & (users["password"] == hashed_pw)]
    return not user.empty

def get_role(username):
    users = load_csv(USER_FILE, ["username", "password", "role"])
    if username in users["username"].values:
        return users[users["username"] == username]["role"].values[0]
    return None

def add_user(username, password, role):
    users = load_csv(USER_FILE, ["username", "password", "role"])
    if username in users["username"].values:
        return False
    users = pd.concat([users, pd.DataFrame({
        "username":[username],
        "password":[hash_password(password)],
        "role":[role]
    })], ignore_index=True)
    save_csv(users, USER_FILE)
    return True

def upload_assignment(username, file):
    save_path = os.path.join(UPLOAD_FOLDER, f"{username}_{file.name}")
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    assignments = load_csv(ASSIGNMENT_FILE, ["username", "filename"])
    assignments = pd.concat([assignments, pd.DataFrame({"username":[username], "filename":[file.name]})], ignore_index=True)
    save_csv(assignments, ASSIGNMENT_FILE)
    return True

# ------------------ STREAMLIT SETUP ------------------
st.set_page_config(page_title="AI Department Portal", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F3E5F5; }
    h1, h2, h3, h4 { color: #4A148C; }
    .stButton>button { background-color: #7E57C2; color: white; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if 'login' not in st.session_state:
    st.session_state['login'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# ------------------ LOGIN ------------------
if not st.session_state['login']:
    st.title("AI Department Portal Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state['login'] = True
            st.session_state['username'] = username
            st.session_state['role'] = get_role(username)
            st.rerun()
        else:
            st.error("Invalid username or password!")

# ------------------ LOGOUT ------------------
if st.session_state['login']:
    st.sidebar.write(f"Logged in as: **{st.session_state['username']}** ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['login'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.rerun()

# ------------------ DASHBOARDS ------------------
if st.session_state['login']:
    username = st.session_state['username']
    role = st.session_state['role']

    # ------------------ ADMIN ------------------
    if role == "admin":
        st.header("👑 Admin Dashboard")
        tab1, tab2, tab3, tab4 = st.tabs(["Users", "Courses", "News", "Assignments"])

        with tab1:
            st.subheader("User Management")
            users = load_csv(USER_FILE, ["username", "password", "role"])
            st.dataframe(users)
            st.write("### ➕ Add New User")
            new_user = st.text_input("Username", key="new_user")
            new_pass = st.text_input("Password", type="password", key="new_pass")
            new_role = st.selectbox("Role", ["student", "teacher", "admin"], key="new_role")
            if st.button("Add User", key="add_user"):
                if add_user(new_user, new_pass, new_role):
                    st.success("User Added Successfully")
                else:
                    st.error("Username already exists")

        with tab2:
            st.subheader("📚 Course Management")
            courses = load_csv(COURSE_FILE, ["course_code", "course_name", "teacher"])
            st.dataframe(courses)
            st.write("### ➕ Add Course")
            code = st.text_input("Course Code", key="code")
            cname = st.text_input("Course Name", key="cname")
            teacher = st.text_input("Teacher Username", key="teacher")
            if st.button("Add Course", key="add_course"):
                courses = pd.concat([courses, pd.DataFrame({
                    "course_code":[code],
                    "course_name":[cname],
                    "teacher":[teacher]
                })], ignore_index=True)
                save_csv(courses, COURSE_FILE)
                st.success("Course Added Successfully")

        with tab3:
            st.subheader("📰 News / Announcements")
            news = load_csv("news.csv", ["title","description"])
            st.dataframe(news)
            ntitle = st.text_input("Title", key="title")
            ndesc = st.text_area("Description", key="desc")
            if st.button("Add News", key="add_news"):
                news = pd.concat([news, pd.DataFrame({"title":[ntitle],"description":[ndesc]})], ignore_index=True)
                save_csv(news, "news.csv")
                st.success("News Added")

        with tab4:
            st.subheader("📂 All Assignments")
            assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
            st.dataframe(assignments)

    # ------------------ TEACHER ------------------
    elif role == "teacher":
        st.header("👨‍🏫 Teacher Dashboard")
        tab1, tab2 = st.tabs(["Attendance", "Marks"])

        with tab1:
            st.subheader("📋 Update Attendance")
            attendance = load_csv(ATTENDANCE_FILE, ["roll_no","course_code","attendance"])
            st.dataframe(attendance)
            rno = st.text_input("Roll No", key="att_rno")
            ccode = st.text_input("Course Code", key="att_course")
            att = st.number_input("Attendance (%)", min_value=0, max_value=100, key="att_val")
            if st.button("Update Attendance", key="update_att"):
                attendance = attendance[~((attendance["roll_no"]==rno) & (attendance["course_code"]==ccode))]
                attendance = pd.concat([attendance, pd.DataFrame({
                    "roll_no":[rno], "course_code":[ccode], "attendance":[att]
                })], ignore_index=True)
                save_csv(attendance, ATTENDANCE_FILE)
                st.success("Attendance Updated")

        with tab2:
            st.subheader("🧾 Update Marks")
            marks = load_csv(MARKS_FILE, ["roll_no","course_code","marks"])
            st.dataframe(marks)
            rno = st.text_input("Roll No", key="mark_rno")
            ccode = st.text_input("Course Code", key="mark_course")
            mark = st.number_input("Marks", min_value=0, max_value=100, key="mark_val")
            if st.button("Update Marks", key="update_marks"):
                marks = marks[~((marks["roll_no"]==rno) & (marks["course_code"]==ccode))]
                marks = pd.concat([marks, pd.DataFrame({
                    "roll_no":[rno], "course_code":[ccode], "marks":[mark]
                })], ignore_index=True)
                save_csv(marks, MARKS_FILE)
                st.success("Marks Updated")

    # ------------------ STUDENT ------------------
    elif role == "student":
        st.header("🎓 Student Dashboard")
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Profile", "Assignments", "Marks", "Attendance", "Change Password"
        ])

        with tab1:
            st.write(f"**Username:** {username}")
            st.write(f"**Role:** {role}")

        with tab2:
            st.subheader("📤 Upload Assignment")
            uploaded_file = st.file_uploader("Choose file", type=["pdf","docx","txt"])
            if st.button("Upload", key="stu_upload"):
                if uploaded_file:
                    upload_assignment(username, uploaded_file)
                    st.success("Assignment Uploaded Successfully")
            assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
            st.dataframe(assignments[assignments["username"]==username])

        with tab3:
            st.subheader("🧾 My Marks")
            marks = load_csv(MARKS_FILE, ["roll_no","course_code","marks"])
            st.dataframe(marks[marks["roll_no"]==username])

        with tab4:
            st.subheader("📋 My Attendance")
            attendance = load_csv(ATTENDANCE_FILE, ["roll_no","course_code","attendance"])
            st.dataframe(attendance[attendance["roll_no"]==username])

        with tab5:
            st.subheader("🔒 Change Password")
            old_pw = st.text_input("Old Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            if st.button("Change Password"):
                if authenticate(username, old_pw):
                    users = load_csv(USER_FILE, ["username","password","role"])
                    users.loc[users["username"]==username, "password"] = hash_password(new_pw)
                    save_csv(users, USER_FILE)
                    st.success("Password Changed")
                else:
                    st.error("Old Password Incorrect")

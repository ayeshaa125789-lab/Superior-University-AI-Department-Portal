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
NEWS_FILE = "news.csv"
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
    users = load_csv(USER_FILE, ["username","password","role"])
    hashed_pw = hash_password(password)
    user = users[(users["username"] == username) & (users["password"] == hashed_pw)]
    return not user.empty

def get_role(username):
    users = load_csv(USER_FILE, ["username","password","role"])
    if username in users["username"].values:
        return users[users["username"]==username]["role"].values[0]
    return None

def add_user(username,password,role):
    users = load_csv(USER_FILE, ["username","password","role"])
    if username in users["username"].values:
        return False
    users = pd.concat([users, pd.DataFrame({"username":[username],
                                            "password":[hash_password(password)],
                                            "role":[role]})], ignore_index=True)
    save_csv(users, USER_FILE)
    return True

def upload_assignment(username, file):
    save_path = os.path.join(UPLOAD_FOLDER, f"{username}_{file.name}")
    with open(save_path,"wb") as f:
        f.write(file.getbuffer())
    assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
    assignments = pd.concat([assignments, pd.DataFrame({"username":[username],"filename":[file.name]})], ignore_index=True)
    save_csv(assignments, ASSIGNMENT_FILE)
    return True

# ------------------ STREAMLIT SETUP ------------------
st.set_page_config(page_title="AI Department Portal", layout="wide")

# Purple theme styling
st.markdown("""
<style>
.stApp {background-color: #F3E5F5;}
h1, h2, h3, h4 {color: #4A148C; text-transform: capitalize;}
.stButton>button {
    background-color: #6A1B9A;
    color: white;
    border-radius: 6px;
    padding: 8px 18px;
    border: none;
    font-weight: 500;
}
.stDataFrame {border: 1px solid #CE93D8;}
input, textarea {
    border: 1px solid #BA68C8 !important;
    border-radius: 4px !important;
}
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
    st.title("AI Department Portal")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username,password):
            st.session_state['login'] = True
            st.session_state['username'] = username
            st.session_state['role'] = get_role(username)
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# ------------------ LOGOUT ------------------
if st.session_state['login']:
    st.sidebar.write(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['login'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.experimental_rerun()

# ------------------ DASHBOARD ------------------
if st.session_state['login']:
    username = st.session_state['username']
    role = st.session_state['role']

    # ================= ADMIN DASHBOARD =================
    if role=="admin":
        st.header("Admin Dashboard")

        students = load_csv(USER_FILE, ["username","password","role"])
        courses = load_csv(COURSE_FILE, ["course_code","course_name","teacher"])
        assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
        news = load_csv(NEWS_FILE, ["title","description"])

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Students", len(students[students["role"]=="student"]))
        col2.metric("Teachers", len(students[students["role"]=="teacher"]))
        col3.metric("Courses", len(courses))
        col4.metric("Assignments", len(assignments))

        st.subheader("Manage Users")
        st.dataframe(students)
        new_user = st.text_input("Username", key="new_user")
        new_pass = st.text_input("Password", type="password", key="new_pass")
        new_role = st.selectbox("Role", ["student","teacher","admin"], key="new_role")
        if st.button("Add User", key="add_user"):
            if add_user(new_user,new_pass,new_role):
                st.success("User added successfully")
            else:
                st.error("Username already exists")

        st.subheader("Manage Courses")
        st.dataframe(courses)
        code = st.text_input("Course Code", key="code")
        cname = st.text_input("Course Name", key="cname")
        teacher = st.text_input("Teacher Username", key="teacher")
        if st.button("Add Course", key="add_course"):
            courses = pd.concat([courses,pd.DataFrame({"course_code":[code],
                                                       "course_name":[cname],
                                                       "teacher":[teacher]})], ignore_index=True)
            save_csv(courses, COURSE_FILE)
            st.success("Course added")

        st.subheader("News / Announcements")
        st.dataframe(news)
        ntitle = st.text_input("Title", key="ntitle")
        ndesc = st.text_area("Description", key="ndesc")
        if st.button("Add News", key="add_news"):
            news = pd.concat([news,pd.DataFrame({"title":[ntitle],"description":[ndesc]})], ignore_index=True)
            save_csv(news, NEWS_FILE)
            st.success("News added")

        st.subheader("Assignments Overview")
        st.dataframe(assignments)

    # ================= TEACHER DASHBOARD =================
    elif role=="teacher":
        st.header("Teacher Dashboard")

        attendance = load_csv(ATTENDANCE_FILE, ["roll_no","course_code","attendance"])
        marks = load_csv(MARKS_FILE, ["roll_no","course_code","marks"])
        courses = load_csv(COURSE_FILE, ["course_code","course_name","teacher"])

        col1,col2,col3 = st.columns(3)
        col1.metric("Total Courses", len(courses[courses["teacher"]==username]))
        col2.metric("Students Recorded", len(attendance))
        col3.metric("Assignments", len(load_csv(ASSIGNMENT_FILE, ["username","filename"])))

        st.subheader("Update Attendance")
        st.dataframe(attendance)
        rno = st.text_input("Student Roll No", key="att_rno")
        ccode = st.text_input("Course Code", key="att_course")
        att = st.number_input("Attendance (%)", min_value=0, max_value=100, key="att_val")
        if st.button("Update Attendance"):
            attendance = attendance[~((attendance["roll_no"]==rno)&(attendance["course_code"]==ccode))]
            attendance = pd.concat([attendance,pd.DataFrame({"roll_no":[rno],
                                                             "course_code":[ccode],
                                                             "attendance":[att]})], ignore_index=True)
            save_csv(attendance, ATTENDANCE_FILE)
            st.success("Attendance updated")

        st.subheader("Update Marks")
        st.dataframe(marks)
        rno2 = st.text_input("Student Roll No", key="mark_rno")
        ccode2 = st.text_input("Course Code", key="mark_course")
        mark = st.number_input("Marks", min_value=0, max_value=100, key="mark_val")
        if st.button("Update Marks"):
            marks = marks[~((marks["roll_no"]==rno2)&(marks["course_code"]==ccode2))]
            marks = pd.concat([marks,pd.DataFrame({"roll_no":[rno2],
                                                   "course_code":[ccode2],
                                                   "marks":[mark]})], ignore_index=True)
            save_csv(marks, MARKS_FILE)
            st.success("Marks updated")

    # ================= STUDENT DASHBOARD =================
    elif role=="student":
        st.header("Student Dashboard")

        marks = load_csv(MARKS_FILE, ["roll_no","course_code","marks"])
        attendance = load_csv(ATTENDANCE_FILE, ["roll_no","course_code","attendance"])
        assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])

        col1,col2,col3 = st.columns(3)
        col1.metric("Assignments Submitted", len(assignments[assignments["username"]==username]))
        col2.metric("Courses Enrolled", len(load_csv(COURSE_FILE, ["course_code","course_name","teacher"])))
        col3.metric("Attendance Records", len(attendance[attendance["roll_no"]==username]))

        st.subheader("Profile")
        st.write(f"Username: {username}")
        st.write(f"Role: {role}")

        st.subheader("Assignments")
        uploaded_file = st.file_uploader("Upload Assignment", type=["pdf","docx","txt"])
        if st.button("Upload Assignment"):
            if uploaded_file:
                upload_assignment(username, uploaded_file)
                st.success("Assignment uploaded successfully")
        st.dataframe(assignments[assignments["username"]==username])

        st.subheader("My Marks")
        st.dataframe(marks[marks["roll_no"]==username])

        st.subheader("My Attendance")
        st.dataframe(attendance[attendance["roll_no"]==username])

        st.subheader("Change Password")
        old_pw = st.text_input("Old Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        if st.button("Change Password"):
            if authenticate(username, old_pw):
                users = load_csv(USER_FILE, ["username","password","role"])
                users.loc[users["username"]==username,"password"] = hash_password(new_pw)
                save_csv(users, USER_FILE)
                st.success("Password changed successfully")
            else:
                st.error("Old password incorrect")

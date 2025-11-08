import streamlit as st
import pandas as pd
import os
import hashlib

# --- Compatibility patch for Streamlit rerun ---
if not hasattr(st, "rerun"):
    st.rerun = st.experimental_rerun

# ------------------ FILE PATHS ------------------
USER_FILE = "users.csv"
ASSIGNMENT_FILE = "assignments.csv"
COURSE_FILE = "courses.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"
FEEDBACK_FILE = "feedback.csv"
NEWS_FILE = "news.csv"
UPLOAD_FOLDER = "uploads"

for folder in [UPLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

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
    user = users[(users['username'] == username) & (users['password'] == hashed_pw)]
    return not user.empty

def get_role(username):
    users = load_csv(USER_FILE, ["username", "password", "role"])
    if username in users['username'].values:
        return users[users['username'] == username]['role'].values[0]
    return None

def add_user(username, password, role):
    users = load_csv(USER_FILE, ["username", "password", "role"])
    if username in users['username'].values:
        return False
    users = pd.concat([users, pd.DataFrame({"username":[username], "password":[hash_password(password)], "role":[role]})], ignore_index=True)
    save_csv(users, USER_FILE)
    return True

def update_password(username, new_password):
    users = load_csv(USER_FILE, ["username", "password", "role"])
    if username in users['username'].values:
        users.loc[users['username']==username, 'password'] = hash_password(new_password)
        save_csv(users, USER_FILE)
        return True
    return False

def upload_assignment(username, file):
    save_path = os.path.join(UPLOAD_FOLDER, f"{username}_{file.name}")
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    assignments = load_csv(ASSIGNMENT_FILE, ["username", "filename"])
    assignments = pd.concat([assignments, pd.DataFrame({"username":[username], "filename":[file.name]})], ignore_index=True)
    save_csv(assignments, ASSIGNMENT_FILE)
    return True

# ------------------ STREAMLIT APP ------------------
st.set_page_config(page_title="AI Department Portal", page_icon="🖥️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #EDE7F6; }
    .css-18e3th9 { background-color: #7E57C2; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'login' not in st.session_state:
    st.session_state['login'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# --- LOGIN ---
if not st.session_state['login']:
    st.title("AI Department Portal Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state['login'] = True
            st.session_state['username'] = username
            st.session_state['role'] = get_role(username)
            st.rerun()  # ✅ fixed
        else:
            st.error("Invalid username or password!")

# --- LOGOUT ---
if st.session_state['login']:
    st.sidebar.write(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['login'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.rerun()  # ✅ fixed

# --- DASHBOARDS ---
if st.session_state['login']:
    role = st.session_state['role']
    username = st.session_state['username']

    # ------------------ ADMIN ------------------
    if role == 'admin':
        st.subheader("Admin Dashboard")
        tab1, tab2, tab3, tab4 = st.tabs(["Users", "Courses", "News", "Assignments"])

        with tab1:  # Users
            users = load_csv(USER_FILE, ["username","password","role"])
            st.write(users)
            st.write("Add New User")
            new_user = st.text_input("Username", key="admin_newuser")
            new_pass = st.text_input("Password", type="password", key="admin_newpass")
            new_role = st.selectbox("Role", ["student","teacher","admin"], key="admin_newrole")
            if st.button("Add User", key="admin_add_user"):
                if add_user(new_user,new_pass,new_role):
                    st.success("User Added Successfully")
                else:
                    st.error("Username exists")

        with tab2:  # Courses
            courses = load_csv(COURSE_FILE, ["course_code","course_name","teacher"])
            st.write(courses)
            st.write("Add Course")
            code = st.text_input("Course Code", key="course_code")
            cname = st.text_input("Course Name", key="course_name")
            teacher = st.text_input("Teacher Username", key="course_teacher")
            if st.button("Add Course", key="add_course"):
                courses = pd.concat([courses, pd.DataFrame({"course_code":[code],"course_name":[cname],"teacher":[teacher]})], ignore_index=True)
                save_csv(courses, COURSE_FILE)
                st.success("Course Added")

        with tab3:  # News
            news = load_csv(NEWS_FILE, ["title","description"])
            st.write(news)
            st.write("Add News")
            ntitle = st.text_input("Title", key="news_title")
            ndesc = st.text_area("Description", key="news_desc")
            if st.button("Add News", key="add_news"):
                news = pd.concat([news, pd.DataFrame({"title":[ntitle],"description":[ndesc]})], ignore_index=True)
                save_csv(news, NEWS_FILE)
                st.success("News Added")

        with tab4:  # Assignments
            assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
            st.write(assignments)

    # ------------------ TEACHER ------------------
    elif role == 'teacher':
        st.subheader("Teacher Dashboard")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Profile","Assignments","Marks","Attendance","News"])

        with tab1:  # Profile
            st.write("Username:", username)
            st.write("Role:", role)

        with tab2:  # Assignments
            assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
            st.write(assignments)
            st.subheader("Upload Assignment")
            uploaded_file = st.file_uploader("Choose file", type=["pdf","docx","txt"], key="teacher_file")
            if st.button("Upload Assignment", key="teacher_upload"):
                if uploaded_file:
                    upload_assignment(username, uploaded_file)
                    st.success("Assignment Uploaded")

        with tab3:  # Marks
            marks = load_csv(MARKS_FILE, ["roll_no","course_code","marks"])
            st.write(marks)
            rno = st.text_input("Roll No", key="marks_rno")
            ccode = st.text_input("Course Code", key="marks_course")
            m = st.number_input("Marks", min_value=0, max_value=100, key="marks_val")
            if st.button("Add/Update Marks", key="marks_add"):
                marks = marks[~((marks['roll_no']==rno) & (marks['course_code']==ccode))]
                marks = pd.concat([marks, pd.DataFrame({"roll_no":[rno],"course_code":[ccode],"marks":[m]})], ignore_index=True)
                save_csv(marks, MARKS_FILE)
                st.success("Marks Updated")

        with tab4:  # Attendance
            attendance = load_csv(ATTENDANCE_FILE, ["roll_no","course_code","attendance"])
            st.write(attendance)
            rno_a = st.text_input("Roll No", key="att_rno")
            ccode_a = st.text_input("Course Code", key="att_course")
            att_val = st.number_input("Attendance %", min_value=0, max_value=100, key="att_val")
            if st.button("Update Attendance", key="att_update"):
                attendance = attendance[~((attendance['roll_no']==rno_a) & (attendance['course_code']==ccode_a))]
                attendance = pd.concat([attendance, pd.DataFrame({"roll_no":[rno_a],"course_code":[ccode_a],"attendance":[att_val]})], ignore_index=True)
                save_csv(attendance, ATTENDANCE_FILE)
                st.success("Attendance Updated")

        with tab5:  # News
            news = load_csv(NEWS_FILE, ["title","description"])
            st.write(news)

    # ------------------ STUDENT ------------------
    elif role == 'student':
        st.subheader("Student Dashboard")
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
            ["Profile","Assignments","Courses","Marks","Attendance","Feedback","News","Change Password"]
        )

        with tab1:
            st.write("Username:", username)
            st.write("Role:", role)

        with tab2:  # Assignments
            uploaded_file = st.file_uploader("Upload Assignment", type=["pdf","docx","txt"], key="student_file")
            if st.button("Upload Assignment", key="student_upload"):
                if uploaded_file:
                    upload_assignment(username, uploaded_file)
                    st.success("Assignment Uploaded")
            assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
            st.write(assignments[assignments['username']==username])

        with tab3:  # Courses
            courses = load_csv(COURSE_FILE, ["course_code","course_name","teacher"])
            st.write(courses)

        with tab4:  # Marks
            marks = load_csv(MARKS_FILE, ["roll_no","course_code","marks"])
            st.write(marks[marks['roll_no']==username])

        with tab5:  # Attendance
            attendance = load_csv(ATTENDANCE_FILE, ["roll_no","course_code","attendance"])
            st.write(attendance[attendance['roll_no']==username])

        with tab6:  # Feedback
            feedback = load_csv(FEEDBACK_FILE, ["roll_no","feedback"])
            fb_text = st.text_area("Submit Feedback")
            if st.button("Submit Feedback", key="fb_submit"):
                feedback = pd.concat([feedback, pd.DataFrame({"roll_no":[username],"feedback":[fb_text]})], ignore_index=True)
                save_csv(feedback, FEEDBACK_FILE)
                st.success("Feedback Submitted")
            st.write(feedback[feedback['roll_no']==username])

        with tab7:  # News
            news = load_csv(NEWS_FILE, ["title","description"])
            st.write(news)

        with tab8:  # Change Password
            old_pw = st.text_input("Old Password", type="password", key="student_old_pw")
            new_pw = st.text_input("New Password", type="password", key="student_new_pw")
            if st.button("Change Password", key="student_pw_change"):
                if authenticate(username, old_pw):
                    update_password(username, new_pw)
                    st.success("Password Changed")
                else:
                    st.error("Old Password Incorrect")

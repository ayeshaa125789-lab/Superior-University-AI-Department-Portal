import streamlit as st
import pandas as pd
import os
import hashlib

# ------------------ FILE PATHS ------------------
USER_FILE = "users.csv"
ASSIGNMENT_FILE = "assignments.csv"
COURSE_FILE = "courses.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"
FEEDBACK_FILE = "feedback.csv"
NEWS_FILE = "news.csv"
UPLOAD_FOLDER = "uploads"

# ------------------ SETUP FOLDERS ------------------
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ------------------ HELPER FUNCTIONS ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_csv(file, default_df=None):
    if os.path.exists(file):
        return pd.read_csv(file)
    elif default_df is not None:
        default_df.to_csv(file, index=False)
        return default_df
    else:
        return pd.DataFrame()

def save_csv(df, file):
    df.to_csv(file, index=False)

# ------------------ USERS ------------------
def load_users():
    default_df = pd.DataFrame([{"username":"admin","password":hash_password("admin123"),"role":"admin"}])
    return load_csv(USER_FILE, default_df)

def save_users(df):
    save_csv(df, USER_FILE)

def authenticate(username, password):
    users = load_users()
    hashed_pw = hash_password(password)
    return not users[(users['username']==username)&(users['password']==hashed_pw)].empty

def get_role(username):
    users = load_users()
    return users[users['username']==username]['role'].values[0]

def add_user(username, password, role):
    users = load_users()
    if username in users['username'].values:
        return False
    users = pd.concat([users, pd.DataFrame([{"username":username,"password":hash_password(password),"role":role}])],ignore_index=True)
    save_users(users)
    return True

def update_password(username, new_password):
    users = load_users()
    users.loc[users['username']==username,'password']=hash_password(new_password)
    save_users(users)

# ------------------ ASSIGNMENTS ------------------
def load_assignments():
    return load_csv(ASSIGNMENT_FILE, pd.DataFrame(columns=["username","filename"]))

def save_assignments(df):
    save_csv(df, ASSIGNMENT_FILE)

def upload_assignment(username, file):
    save_path = os.path.join(UPLOAD_FOLDER,f"{username}_{file.name}")
    with open(save_path,"wb") as f:
        f.write(file.getbuffer())
    df = load_assignments()
    df = pd.concat([df, pd.DataFrame([{"username":username,"filename":file.name}])],ignore_index=True)
    save_assignments(df)

# ------------------ COURSES ------------------
def load_courses():
    return load_csv(COURSE_FILE, pd.DataFrame(columns=["course_id","course_name"]))

def save_courses(df):
    save_csv(df, COURSE_FILE)

def add_course(course_id, course_name):
    df = load_courses()
    if course_id in df['course_id'].values:
        return False
    df = pd.concat([df, pd.DataFrame([{"course_id":course_id,"course_name":course_name}])],ignore_index=True)
    save_courses(df)
    return True

# ------------------ MARKS ------------------
def load_marks():
    return load_csv(MARKS_FILE, pd.DataFrame(columns=["roll_no","course_id","marks"]))

def save_marks(df):
    save_csv(df, MARKS_FILE)

def add_marks(roll_no, course_id, marks):
    df = load_marks()
    df = pd.concat([df, pd.DataFrame([{"roll_no":roll_no,"course_id":course_id,"marks":marks}])],ignore_index=True)
    save_marks(df)

# ------------------ ATTENDANCE ------------------
def load_attendance():
    return load_csv(ATTENDANCE_FILE, pd.DataFrame(columns=["roll_no","course_id","attendance"]))

def save_attendance(df):
    save_csv(df, ATTENDANCE_FILE)

def add_attendance(roll_no, course_id, attendance):
    df = load_attendance()
    df = pd.concat([df, pd.DataFrame([{"roll_no":roll_no,"course_id":course_id,"attendance":attendance}])],ignore_index=True)
    save_attendance(df)

# ------------------ FEEDBACK ------------------
def load_feedback():
    return load_csv(FEEDBACK_FILE, pd.DataFrame(columns=["username","feedback"]))

def save_feedback(df):
    save_csv(df, FEEDBACK_FILE)

def add_feedback(username, feedback):
    df = load_feedback()
    df = pd.concat([df, pd.DataFrame([{"username":username,"feedback":feedback}])],ignore_index=True)
    save_feedback(df)

# ------------------ NEWS ------------------
def load_news():
    return load_csv(NEWS_FILE, pd.DataFrame(columns=["title","description"]))

def save_news(df):
    save_csv(df, NEWS_FILE)

def add_news(title, description):
    df = load_news()
    df = pd.concat([df, pd.DataFrame([{"title":title,"description":description}])],ignore_index=True)
    save_news(df)

# ------------------ STREAMLIT APP ------------------
st.set_page_config(page_title="AI Department Portal", page_icon="🖥️", layout="wide")
st.markdown("""
<style>
body {background-color: #e6e0f8;}
h1, h2, h3, h4, h5, h6 {color: #4b0082;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'login' not in st.session_state:
    st.session_state['login']=False
if 'username' not in st.session_state:
    st.session_state['username']=""
if 'role' not in st.session_state:
    st.session_state['role']=""

# --- LOGIN ---
if not st.session_state['login']:
    st.title("🖥️ AI Department Portal Login")
    username=st.text_input("Username")
    password=st.text_input("Password",type="password")
    if st.button("Login"):
        if authenticate(username,password):
            st.session_state['login']=True
            st.session_state['username']=username
            st.session_state['role']=get_role(username)
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid username or password!")

# --- LOGOUT ---
if st.session_state['login']:
    st.sidebar.write(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['login']=False
        st.session_state['username']=""
        st.session_state['role']=""

# --- ADMIN DASHBOARD ---
if st.session_state['login'] and st.session_state['role']=="admin":
    st.header("Admin Dashboard")
    users = load_users()
    courses = load_courses()
    
    tabs = st.tabs(["Users","Courses","Assignments","Marks","Attendance","Feedback","News"])
    
    with tabs[0]:
        st.subheader("Manage Users")
        st.write(users)
        st.markdown("**Add User**")
        uname=st.text_input("Username (Roll No for student)",key="a_uname")
        pwd=st.text_input("Password",type="password",key="a_pwd")
        role=st.selectbox("Role",["student","teacher"],key="a_role")
        if st.button("Add User",key="add_u_btn"):
            if add_user(uname,pwd,role):
                st.success("User added!")
            else:
                st.error("User exists!")
        del_user=st.selectbox("Delete User",users['username'].tolist(),key="d_user")
        if st.button("Delete User",key="del_u_btn"):
            users=users[users['username']!=del_user]
            save_users(users)
            st.success("Deleted!")

    with tabs[1]:
        st.subheader("Manage Courses")
        st.write(courses)
        cid=st.text_input("Course ID",key="cid")
        cname=st.text_input("Course Name",key="cname")
        if st.button("Add Course",key="add_course_btn"):
            if add_course(cid,cname):
                st.success("Course added!")
            else:
                st.error("Course exists!")

    with tabs[2]:
        st.subheader("Assignments")
        assignments=load_assignments()
        st.write(assignments)

    with tabs[3]:
        st.subheader("Marks")
        marks=load_marks()
        st.write(marks)
    
    with tabs[4]:
        st.subheader("Attendance")
        attendance=load_attendance()
        st.write(attendance)

    with tabs[5]:
        st.subheader("Feedback")
        feedback=load_feedback()
        st.write(feedback)
    
    with tabs[6]:
        st.subheader("News")
        news=load_news()
        st.write(news)
        title=st.text_input("Title",key="n_title")
        desc=st.text_area("Description",key="n_desc")
        if st.button("Add News",key="add_news_btn"):
            add_news(title,desc)
            st.success("News added!")

# --- TEACHER DASHBOARD ---
if st.session_state['login'] and st.session_state['role']=="teacher":
    st.header("Teacher Dashboard")
    st.subheader("Assignments")
    assignments=load_assignments()
    st.write(assignments)
    
    st.subheader("Marks")
    marks=load_marks()
    st.write(marks)
    
    st.subheader("Attendance")
    attendance=load_attendance()
    st.write(attendance)
    
    st.subheader("Feedback")
    feedback=load_feedback()
    st.write(feedback)
    
    st.subheader("News")
    news=load_news()
    st.write(news)

# --- STUDENT DASHBOARD ---
if st.session_state['login'] and st.session_state['role']=="student":
    st.header("Student Dashboard")
    st.subheader("Profile")
    st.write("Username:",st.session_state['username'])
    
    st.subheader("Change Password")
    old_pw=st.text_input("Old Password",type="password")
    new_pw=st.text_input("New Password",type="password")
    if st.button("Update Password"):
        if authenticate(st.session_state['username'],old_pw):
            update_password(st.session_state['username'],new_pw)
            st.success("Password updated!")
        else:
            st.error("Old password incorrect!")

    st.subheader("Assignments")
    assignments=load_assignments()
    user_assignments=assignments[assignments['username']==st.session_state['username']]
    st.write(user_assignments)
    uploaded_file=st.file_uploader("Upload Assignment")
    if st.button("Submit Assignment"):
        if uploaded_file:
            upload_assignment(st.session_state['username'],uploaded_file)
            st.success("Submitted!")

    st.subheader("Marks")
    marks=load_marks()
    user_marks=marks[marks['roll_no']==st.session_state['username']]
    st.write(user_marks)
    
    st.subheader("Attendance")
    attendance=load_attendance()
    user_att=attendance[attendance['roll_no']==st.session_state['username']]
    st.write(user_att)
    
    st.subheader("Feedback")
    feedback=load_feedback()
    user_feedback=feedback[feedback['username']==st.session_state['username']]
    st.write(user_feedback)
    
    st.subheader("News")
    news=load_news()
    st.write(news)

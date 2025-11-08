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
    user = users[(users["username"]==username) & (users["password"]==hashed_pw)]
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

# ------------------ INITIAL ADMIN SETUP ------------------
users = load_csv(USER_FILE, ["username","password","role"])
if "admin" not in users["username"].values:
    users = pd.concat([users,pd.DataFrame({"username":["admin"],
                                           "password":[hash_password("admin123")],
                                           "role":["admin"]})], ignore_index=True)
    save_csv(users, USER_FILE)

# ------------------ STREAMLIT SETUP ------------------
st.set_page_config(page_title="AI Department Portal", layout="wide")

# Purple theme styling
st.markdown("""
<style>
.stApp {background-color: #F3E5F5;}
h1, h2, h3, h4 {color: #4A148C;}
.stButton>button {background-color: #6A1B9A; color: white; border-radius: 6px; padding: 8px 18px; border: none; font-weight: 500;}
.stDataFrame {border: 1px solid #CE93D8;}
input, textarea {border: 1px solid #BA68C8 !important; border-radius: 4px !important;}
</style>
""", unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if 'login' not in st.session_state:
    st.session_state['login'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# ------------------ MAIN APP ------------------
def main():
    if not st.session_state['login']:
        st.title("AI Department Portal")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username,password):
                st.session_state['login'] = True
                st.session_state['username'] = username
                st.session_state['role'] = get_role(username)
            else:
                st.error("Invalid username or password")
        return  # stop here until login

    # Sidebar Logout
    st.sidebar.write(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['login'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.experimental_rerun = None  # just reset state, no rerun needed
        return

    # Dashboard
    username = st.session_state['username']
    role = st.session_state['role']

    if role=="admin":
        st.header("Admin Dashboard")
        users_df = load_csv(USER_FILE, ["username","password","role"])
        courses = load_csv(COURSE_FILE, ["course_code","course_name","teacher"])
        assignments = load_csv(ASSIGNMENT_FILE, ["username","filename"])
        news = load_csv(NEWS_FILE, ["title","description"])

        st.subheader("Manage Users")
        st.dataframe(users_df)
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

main()

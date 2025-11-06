# main.py
# Superior University - AI Dept Portal (Full-featured)
# Single-file Streamlit app

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

# ------------------------------
# Page config
# ------------------------------
st.set_page_config(page_title="Superior University — AI Dept Portal",
                   page_icon="💜", layout="wide")

# ------------------------------
# CSS / Theme
# ------------------------------
st.markdown("""
<style>
.header { display:flex; align-items:center; justify-content:center; gap:20px;
    padding:18px; background: linear-gradient(90deg, #6A0DAD, #8E43E7);
    color: white; border-radius: 8px; margin-bottom: 18px; }
.portal-title { font-size:28px; font-weight:700; margin:0; }
.card { background: #fff; border-radius: 12px; padding: 14px; box-shadow: 0 6px 18px rgba(94,23,235,0.06); }
.metric { background: linear-gradient(180deg, rgba(106,13,173,0.06), rgba(106,13,173,0.02));
    border-radius:10px; padding:12px; text-align:center; }
.stButton>button { background-color: #6A0DAD !important; color:white !important;
    border-radius:8px !important; padding:6px 14px !important; }
.small-muted { color:#666; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Files / Data
# ------------------------------
DATA_DIR = Path(".")
USERS_CSV = DATA_DIR / "users.csv"
STUDENTS_CSV = DATA_DIR / "students.csv"
COURSES_CSV = DATA_DIR / "courses.csv"
FEEDBACK_CSV = DATA_DIR / "feedback.csv"
NEWS_CSV = DATA_DIR / "news.csv"
RESULTS_CSV = DATA_DIR / "results.csv"
LOGO_NAME = "df0a13dd-ce21-40c2-8ca7-a0eb0e2096c6.png"

def ensure(path: Path, columns):
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)

ensure(USERS_CSV, ["username","display_name","password_hash","role","email","created_at"])
ensure(STUDENTS_CSV, ["name","roll","semester","email"])
ensure(COURSES_CSV, ["course_name","course_code","instructor"])
ensure(FEEDBACK_CSV, ["username","name","course","message","rating","created_at"])
ensure(NEWS_CSV, ["title","content","created_at"])
ensure(RESULTS_CSV, ["roll","semester","course_code","marks","grade"])

# ------------------------------
# Auth helpers
# ------------------------------
def hash_pw(pw:str): return hashlib.sha256(pw.encode("utf-8")).hexdigest()
def load_users(): return pd.read_csv(USERS_CSV)
def save_users(df): df.to_csv(USERS_CSV, index=False)
def user_exists(username:str): return username in load_users()['username'].astype(str).values
def create_user(username, display_name, password, role, email=""):
    df = load_users()
    now = datetime.now(timezone.utc).isoformat()
    new = pd.DataFrame([[username, display_name, hash_pw(password), role, email, now]], columns=df.columns)
    df = pd.concat([df,new], ignore_index=True)
    save_users(df)

def verify_user(username, password):
    df = load_users()
    row = df[df['username'].astype(str)==str(username)]
    if row.empty: return None
    if row.iloc[0]['password_hash'] == hash_pw(password):
        return {"username": row.iloc[0]['username'],
                "display_name": row.iloc[0]['display_name'],
                "role": row.iloc[0]['role'],
                "email": row.iloc[0].get('email', "")}
    return None

# ------------------------------
# Default admin / teacher
# ------------------------------
if not user_exists("admin"):
    create_user("admin","Head Teacher","admin123","Admin")

# ------------------------------
# Session state
# ------------------------------
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False,"username": None,"display_name": None,"role": None}
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True

def toggle_sidebar():
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible

# ------------------------------
# Header
# ------------------------------
logo_path = Path(LOGO_NAME)
col_l, col_c, col_r = st.columns([1,6,1])
with col_c:
    st.markdown(f"""
    <div class="header">
        {'<img src="'+LOGO_NAME+'" width="64">' if logo_path.exists() else ''}
        <div style="text-align:left;">
            <div class="portal-title">Superior University — AI Dept Portal</div>
            <div class="small-muted">Secure dashboard • Students • Courses • Feedback • News • Results</div>
        </div>
    </div>
    """,unsafe_allow_html=True)

# ------------------------------
# Sidebar
# ------------------------------
if st.session_state.sidebar_visible:
    with st.sidebar:
        st.button("⬅ Hide Sidebar", on_click=toggle_sidebar)
        st.markdown("### Account")
        if not st.session_state.auth["logged_in"]:
            auth_tab = st.radio("Choose",("Login","Sign Up"))
            if auth_tab=="Login":
                li_user = st.text_input("Username")
                li_pw = st.text_input("Password",type="password")
                if st.button("Login"):
                    res = verify_user(li_user.strip(), li_pw)
                    if res:
                        st.session_state.auth = {"logged_in": True,"username":res['username'],
                                                 "display_name":res['display_name'],"role":res['role']}
                        st.success(f"Welcome {res['display_name']} ({res['role']})")
                        st.experimental_rerun()
                    else: st.error("Invalid username or password.")
            else:
                st.write("Student account creation only (Admin set manually)")
                su_name = st.text_input("Full name")
                su_username = st.text_input("Username")
                su_email = st.text_input("Email (optional)")
                su_pw = st.text_input("Password",type="password")
                su_pw2 = st.text_input("Confirm password",type="password")
                if st.button("Sign up"):
                    if not (su_name and su_username and su_pw and su_pw2):
                        st.warning("Fill all required fields")
                    elif su_pw != su_pw2:
                        st.warning("Passwords do not match")
                    elif user_exists(su_username.strip()):
                        st.warning("Username exists")
                    else:
                        create_user(su_username.strip(), su_name.strip(), su_pw.strip(),"Student",su_email.strip())
                        st.success("Account created. Ask admin to assign semester")
        else:
            st.write(f"**{st.session_state.auth['display_name']}**")
            st.write(f"Role: `{st.session_state.auth['role']}`")
            if st.button("Logout"):
                st.session_state.auth = {"logged_in": False,"username": None,"display_name": None,"role": None}
                st.experimental_rerun()

        st.markdown("---")
        st.markdown("### Navigation")
        if st.session_state.auth["logged_in"]:
            role = st.session_state.auth["role"].lower()
            if role=="admin":
                nav = st.radio("Go to", ["Dashboard","Students","Courses","Feedback","News","Users","Results"])
            else:
                nav = st.radio("Go to", ["Home","My Profile","Courses","Submit Feedback","Announcements","Results"])
        else:
            nav = st.radio("Preview", ["Home","Announcements"])
        st.session_state.nav = nav
else:
    if st.button("➡ Show Sidebar"): toggle_sidebar()

# ------------------------------
# Utility CSV read
# ------------------------------
def read_csv(path): 
    try: return pd.read_csv(path)
    except: return pd.DataFrame()

# ------------------------------
# Main content
# ------------------------------
nav = st.session_state.get("nav","Home")

# Admin Dashboard
if st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower()=="admin" and nav=="Dashboard":
    st.markdown("## 📊 Admin Dashboard")
    students = read_csv(STUDENTS_CSV)
    courses = read_csv(COURSES_CSV)
    feedback = read_csv(FEEDBACK_CSV)
    news = read_csv(NEWS_CSV)

    c1,c2,c3 = st.columns(3)
    c1.markdown(f"<div class='metric'><h3>{len(students)}</h3><div class='small-muted'>Students</div></div>",unsafe_allow_html=True)
    c2.markdown(f"<div class='metric'><h3>{len(courses)}</h3><div class='small-muted'>Courses</div></div>",unsafe_allow_html=True)
    c3.markdown(f"<div class='metric'><h3>{len(feedback)}</h3><div class='small-muted'>Feedback</div></div>",unsafe_allow_html=True)

    st.markdown("### Recent Feedback")
    st.dataframe(feedback.sort_values("created_at",ascending=False).head(8) if not feedback.empty else pd.DataFrame())
    st.markdown("### Latest News")
    st.dataframe(news.sort_values("created_at",ascending=False).head(6) if not news.empty else pd.DataFrame())

# Admin manage Students
elif st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower()=="admin" and nav=="Students":
    st.markdown("## 👥 Manage Students")
    with st.expander("Add Student"):
        s_name = st.text_input("Student name")
        s_roll = st.text_input("Roll")
        s_sem = st.selectbox("Semester", ["1st","3rd"])
        s_email = st.text_input("Email")
        if st.button("Add Student"):
            df = read_csv(STUDENTS_CSV)
            if str(s_roll) in df['roll'].astype(str).values:
                st.warning("Roll exists")
            else:
                df = pd.concat([df,pd.DataFrame([[s_name,s_roll,s_sem,s_email]],columns=df.columns)],ignore_index=True)
                df.to_csv(STUDENTS_CSV,index=False)
                st.success("Student added")
    st.markdown("### All Students")
    st.dataframe(read_csv(STUDENTS_CSV))

# Admin manage Courses
elif st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower()=="admin" and nav=="Courses":
    st.markdown("## 📚 Manage Courses")
    with st.expander("Add Course"):
        c_name = st.text_input("Course name")
        c_code = st.text_input("Course code")
        c_instr = st.text_input("Instructor")
        if st.button("Add Course"):
            df = read_csv(COURSES_CSV)
            if str(c_code) in df['course_code'].astype(str).values:
                st.warning("Course code exists")
            else:
                df = pd.concat([df,pd.DataFrame([[c_name,c_code,c_instr]],columns=df.columns)],ignore_index=True)
                df.to_csv(COURSES_CSV,index=False)
                st.success("Course added")
    st.markdown("### All Courses")
    st.dataframe(read_csv(COURSES_CSV))

# Admin Feedback
elif st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower()=="admin" and nav=="Feedback":
    st.markdown("## 💬 Feedback")
    df = read_csv(FEEDBACK_CSV)
    st.dataframe(df.sort_values("created_at",ascending=False) if not df.empty else pd.DataFrame())

# Admin News
elif st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower()=="admin" and nav=="News":
    st.markdown("## 📰 Post News")
    n_title = st.text_input("Title")
    n_content = st.text_area("Content")
    if st.button("Publish News"):
        df = read_csv(NEWS_CSV)
        df = pd.concat([df,pd.DataFrame([[n_title,n_content,datetime.now(timezone.utc).isoformat()]],columns=df.columns)],ignore_index=True)
        df.to_csv(NEWS_CSV,index=False)
        st.success("News published")
    st.markdown("### All News")
    st.dataframe(read_csv(NEWS_CSV).sort_values("created_at",ascending=False))

# Admin Users
elif st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower()=="admin" and nav=="Users":
    st.markdown("## 🔐 Users")
    users = read_csv(USERS_CSV)
    st.dataframe(users[['username','display_name','role','email','created_at']])

# Results (both roles)
elif nav=="Results" or nav=="results":
    st.markdown("## 📄 Results")
    df = read_csv(RESULTS_CSV)
    if st.session_state.auth["role"].lower()=="student":
        roll = st.session_state.auth['username']
        sem_students = read_csv(STUDENTS_CSV)
        row = sem_students[sem_students['roll'].astype(str)==roll]
        if not row.empty:
            sem = row.iloc[0]['semester']
            df = df[df['semester']==sem]
        else: df = pd.DataFrame()
    st.dataframe(df if not df.empty else pd.DataFrame({"Info":["No results found"]}))

# Student Dashboard
elif st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower()=="student":
    role = st.session_state.auth['role'].lower()
    if nav=="Home":
        st.markdown("## 🏠 Student Home")
        st.info("Welcome! Use sidebar to navigate courses, results, feedback, announcements.")
    elif nav=="My Profile":
        st.markdown("## 🧾 My Profile")
        users = read_csv(USERS_CSV)
        row = users[users['username']==st.session_state.auth['username']]
        if not row.empty:
            r = row.iloc[0]
            st.write(f"**Username:** {r['username']}")
            st.write(f"**Name:** {r['display_name']}")
            st.write(f"**Role:** {r['role']}")
            if r['email']: st.write(f"**Email:** {r['email']}")
            st.write(f"**Joined:** {r['created_at']}")
    elif nav=="Courses":
        st.markdown("## 📘 Courses")
        st.dataframe(read_csv(COURSES_CSV))
    elif nav=="Submit Feedback":
        st.markdown("## ✉️ Submit Feedback")
        name = st.session_state.auth['display_name']
        course = st.text_input("Course (optional)")
        message = st.text_area("Message")
        rating = st.slider("Rating (1-5)",1,5)
        if st.button("Submit Feedback"):
            if name and message:
                df = read_csv(FEEDBACK_CSV)
                df = pd.concat([df,pd.DataFrame([[st.session_state.auth['username'],name,course,message,rating,datetime.now(timezone.utc).isoformat()]],columns=df.columns)],ignore_index=True)
                df.to_csv(FEEDBACK_CSV,index=False)
                st.success("Feedback submitted")
            else: st.warning("Fill message")

# Announcements
elif nav in ("Announcements","News","Home","Preview"):
    st.markdown("## 📰 Announcements")
    df = read_csv(NEWS_CSV)
    if df.empty: st.info("No announcements yet.")
    else:
        for _,r in df.sort_values("created_at",ascending=False).iterrows():
            st.markdown(f"**{r['title']}**")
            st.write(r['content'])
            st.caption(r['created_at'])
            st.write("---")

# ------------------------------
# Footer
# ------------------------------
st.markdown("---")
st.caption("Built for Superior University • Purple Superior theme • Single-file app (main.py)")

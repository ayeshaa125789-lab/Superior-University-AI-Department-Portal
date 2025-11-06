# main.py
# Superior University - AI Department Portal
# Semester 1 & 3 only, limited student role, teacher/admin controlled

import streamlit as st
import pandas as pd
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(page_title="Superior University — AI Dept Portal",  layout="wide")

# -------------------------------
# Files / Data
# -------------------------------
DATA_DIR = Path(".")
USERS_CSV = DATA_DIR / "users.csv"         # Teachers/Admins
STUDENTS_CSV = DATA_DIR / "students.csv"
COURSES_CSV = DATA_DIR / "courses.csv"
FEEDBACK_CSV = DATA_DIR / "feedback.csv"
NEWS_CSV = DATA_DIR / "news.csv"

def ensure(path: Path, columns):
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False)

ensure(USERS_CSV, ["username", "display_name", "password_hash", "role", "email", "created_at"])
ensure(STUDENTS_CSV, ["name", "roll", "semester", "email"])
ensure(COURSES_CSV, ["course_name", "course_code", "instructor"])
ensure(FEEDBACK_CSV, ["username", "name", "course", "message", "rating", "created_at"])
ensure(NEWS_CSV, ["title", "content", "created_at"])

# -------------------------------
# Authentication
# -------------------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def load_users():
    return pd.read_csv(USERS_CSV)

def save_users(df):
    df.to_csv(USERS_CSV, index=False)

def user_exists(username: str) -> bool:
    df = load_users()
    return username in df['username'].astype(str).values

def create_user(username: str, display_name: str, password: str, role: str, email: str = ""):
    df = load_users()
    now = datetime.now(timezone.utc).isoformat()
    new = pd.DataFrame([[username, display_name, hash_pw(password), role, email, now]], columns=df.columns)
    df = pd.concat([df, new], ignore_index=True)
    save_users(df)

def verify_user(username: str, password: str):
    df = load_users()
    row = df[df['username'].astype(str) == str(username)]
    if row.empty:
        return None
    if row.iloc[0]['password_hash'] == hash_pw(password):
        return {
            "username": row.iloc[0]['username'],
            "display_name": row.iloc[0]['display_name'],
            "role": row.iloc[0]['role'],
            "email": row.iloc[0].get('email', "")
        }
    return None

# -------------------------------
# Create default admin/teacher if not exists
# -------------------------------
if not user_exists("admin"):
    create_user("admin", "Administrator", "admin123", "Admin", "")

# -------------------------------
# Session state
# -------------------------------
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None}

if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True

def toggle_sidebar():
    st.session_state.sidebar_visible = not st.session_state.sidebar_visible

# -------------------------------
# Sidebar
# -------------------------------
if st.session_state.sidebar_visible:
    with st.sidebar:
        st.button("⬅ Hide Sidebar", on_click=toggle_sidebar)
        st.markdown("### Account")
        if not st.session_state.auth["logged_in"]:
            # Only student login (no signup for admin)
            li_user = st.text_input("Username", key="li_user")
            li_pw = st.text_input("Password", type="password", key="li_pw")
            if st.button("Login", key="login_btn"):
                res = verify_user(li_user.strip(), li_pw)
                if res:
                    st.session_state.auth = {"logged_in": True, "username": res['username'],
                                             "display_name": res['display_name'], "role": res['role']}
                    st.success(f"Welcome {res['display_name']} ({res['role']})")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        else:
            st.write(f"**{st.session_state.auth['display_name']}**")
            st.write(f"Role: `{st.session_state.auth['role']}`")
            if st.button("Logout"):
                st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None}
                st.rerun()

        st.markdown("---")
        st.markdown("### Navigation")
        if st.session_state.auth["logged_in"]:
            role = st.session_state.auth["role"].lower()
            if role == "admin" or role == "teacher":
                nav = st.radio("Go to", ["Dashboard", "Students", "Courses", "Feedback", "News", "Users"])
            else:
                # Only Semester 1 & 3 students
                nav = st.radio("Go to", ["Home", "My Profile", "Courses", "Submit Feedback", "Announcements"])
        else:
            nav = st.radio("Preview", ["Home", "Announcements"])
        st.session_state.nav = nav
else:
    if st.button("➡ Show Sidebar"):
        toggle_sidebar()

# -------------------------------
# Utilities
# -------------------------------
def read_csv(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

# -------------------------------
# Main content area
# -------------------------------
nav = st.session_state.get("nav", "Home")

# Admin / Teacher Dashboard
if st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower() in ["admin", "teacher"]:
    if nav == "Dashboard":
        st.markdown("## 📊 Dashboard")
        students = read_csv(STUDENTS_CSV)
        courses = read_csv(COURSES_CSV)
        feedback = read_csv(FEEDBACK_CSV)
        news = read_csv(NEWS_CSV)

        c1, c2, c3 = st.columns(3)
        c1.metric("Students", len(students))
        c2.metric("Courses", len(courses))
        c3.metric("Feedback", len(feedback))

        st.markdown("### Recent Feedback")
        if not feedback.empty:
            st.dataframe(feedback.sort_values("created_at", ascending=False).head(8))
        else:
            st.info("No feedback yet.")

        st.markdown("### Latest News")
        if not news.empty:
            st.dataframe(news.sort_values("created_at", ascending=False).head(6))
        else:
            st.info("No news posted.")

# Students only (Semester 1 & 3)
elif st.session_state.auth["logged_in"] and st.session_state.auth["role"].lower() == "student":
    # Filter semester
    students = read_csv(STUDENTS_CSV)
    user_row = students[students['roll'].astype(str) == st.session_state.auth["username"]]
    semester = user_row.iloc[0]['semester'] if not user_row.empty else None
    if semester not in ["1", "3"]:
        st.warning("Access limited to Semester 1 and 3 students.")
    else:
        if nav == "Home":
            st.markdown("## 🏠 Home")
            st.info(f"Welcome, Semester {semester} student!")
        elif nav == "My Profile":
            st.markdown("## 🧾 My Profile")
            st.write(f"**Name:** {st.session_state.auth['display_name']}")
            st.write(f"**Roll:** {st.session_state.auth['username']}")
            st.write(f"**Semester:** {semester}")
        elif nav == "Courses":
            st.markdown("## 📘 Courses")
            df = read_csv(COURSES_CSV)
            st.dataframe(df)
        elif nav == "Submit Feedback":
            st.markdown("## ✉️ Submit Feedback")
            course = st.text_input("Course (optional)")
            message = st.text_area("Message")
            rating = st.slider("Rating (1-5)", 1, 5)
            if st.button("Submit"):
                if message:
                    df = read_csv(FEEDBACK_CSV)
                    df = pd.concat([df, pd.DataFrame([[st.session_state.auth['username'],
                                                      st.session_state.auth['display_name'],
                                                      course, message, rating,
                                                      datetime.now(timezone.utc).isoformat()]],
                                                    columns=df.columns)], ignore_index=True)
                    df.to_csv(FEEDBACK_CSV, index=False)
                    st.success("Feedback submitted.")
                else:
                    st.warning("Enter a message.")
        elif nav == "Announcements":
            st.markdown("## 📰 Announcements")
            news = read_csv(NEWS_CSV)
            for _, r in news.sort_values("created_at", ascending=False).iterrows():
                st.markdown(f"**{r['title']}**")
                st.write(r['content'])
                st.caption(r['created_at'])

# Preview for non-logged users
else:
    st.markdown("## 📰 Announcements")
    news = read_csv(NEWS_CSV)
    if news.empty:
        st.info("No announcements yet.")
    else:
        for _, r in news.sort_values("created_at", ascending=False).iterrows():
            st.markdown(f"**{r['title']}**")
            st.write(r['content'])
            st.caption(r['created_at'])

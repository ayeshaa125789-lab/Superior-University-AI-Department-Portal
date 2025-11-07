# main.py
# Superior University — AI Department Portal (JSON backend)
# Single-file Streamlit app (save as main.py)

import streamlit as st
import json
import os
from pathlib import Path
import hashlib
from datetime import date, datetime
import pandas as pd

st.set_page_config(page_title="AI Department Portal | Superior University", layout="wide")

# -----------------------
# File paths (JSON storage)
# -----------------------
DATA_DIR = Path(".")
USERS_FILE = DATA_DIR / "users.json"          # stores all users (admin/teacher/student)
STUDENTS_FILE = DATA_DIR / "students.json"    # student details (roll, name, semester)
TEACHERS_FILE = DATA_DIR / "teachers.json"
COURSES_FILE = DATA_DIR / "courses.json"
ATT_FILE = DATA_DIR / "attendance.json"
MARKS_FILE = DATA_DIR / "marks.json"
ANN_FILE = DATA_DIR / "announcements.json"
FB_FILE = DATA_DIR / "feedback.json"

# -----------------------
# Utilities: JSON load/save & hashing
# -----------------------
def ensure_file(path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=2))

def load_json(path):
    ensure_file(path, [])
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

# Ensure files exist with sensible defaults
ensure_file(USERS_FILE, [
    # default admin (username=admin, password=admin123)
    {"username": "admin", "display_name": "Administrator", "password_hash": hash_pw("admin123"), "role": "admin", "semester": None}
])
ensure_file(STUDENTS_FILE, [])
ensure_file(TEACHERS_FILE, [])
ensure_file(COURSES_FILE, [])
ensure_file(ATT_FILE, [])
ensure_file(MARKS_FILE, [])
ensure_file(ANN_FILE, [])
ensure_file(FB_FILE, [])

# -----------------------
# Helper functions (users)
# -----------------------
def find_user(username):
    users = load_json(USERS_FILE)
    for u in users:
        if u["username"] == username:
            return u
    return None

def create_user(username, display_name, password, role, semester=None):
    users = load_json(USERS_FILE)
    if find_user(username):
        return False
    users.append({
        "username": username,
        "display_name": display_name,
        "password_hash": hash_pw(password),
        "role": role,
        "semester": semester
    })
    save_json(USERS_FILE, users)
    return True

def update_user_password(username, new_password):
    users = load_json(USERS_FILE)
    changed = False
    for u in users:
        if u["username"] == username:
            u["password_hash"] = hash_pw(new_password)
            changed = True
            break
    if changed:
        save_json(USERS_FILE, users)
    return changed

# -----------------------
# Login logic
# -----------------------
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None, "semester": None}

def login_user(username, password):
    u = find_user(username)
    if not u:
        return None
    if hash_pw(password) == u["password_hash"]:
        return u
    return None

# -----------------------
# Basic styling
# -----------------------
st.markdown(
    """<style>
    body { background-color:#040406; color: #e8e8e8; }
    .title { text-align:center; color:#bb86fc; font-size:30px; font-weight:700; margin-bottom:0.1rem; }
    .subtitle { text-align:center; color:#a97df0; margin-top:0; margin-bottom:10px; font-size:14px; }
    .card { background: linear-gradient(135deg,#6a0dad,#9b59b6); padding:18px; border-radius:12px; color:white; text-align:center; }
    .stButton>button { background: linear-gradient(90deg,#8e2de2,#4a00e0); color:white; border-radius:8px; padding:8px 12px; }
    </style>""", unsafe_allow_html=True)

st.markdown('<div class="title">AI Department Portal | Superior University</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Faculty & Student Dashboard — Semesters 1–8</div>', unsafe_allow_html=True)

# -----------------------
# Show login only when not logged in
# -----------------------
if not st.session_state.auth["logged_in"]:
    login_col1, login_col2, login_col3 = st.columns([1,2,1])
    with login_col2:
        st.subheader("Login (username + password)")
        username = st.text_input("Username (admin / teacher username / student roll no)", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="login_btn"):
            res = login_user(username.strip(), password.strip())
            if res:
                st.session_state.auth = {
                    "logged_in": True,
                    "username": res["username"],
                    "display_name": res["display_name"],
                    "role": res["role"],
                    "semester": res.get("semester", None)
                }
                st.success(f"Welcome {res['display_name']} — {res['role'].capitalize()}")
                st.experimental_rerun()  # rerun so login widgets disappear
            else:
                st.error("Invalid username or password")
    st.stop()

# -----------------------
# Logged in: build sidebar + main layout
# -----------------------
role = st.session_state.auth["role"]
username = st.session_state.auth["username"]
display_name = st.session_state.auth["display_name"]
semester = st.session_state.auth.get("semester", None)

left, main = st.columns([1, 4])
with left:
    st.markdown(f"### {display_name}")
    st.write(f"**Role:** {role.capitalize()}")
    st.markdown("---")
    if role == "admin":
        menu = ["Dashboard", "Manage Teachers", "Manage Students", "Courses", "Attendance", "Marks", "Announcements", "Feedback", "Change Password", "Logout"]
    elif role == "teacher":
        menu = ["Dashboard", "My Courses", "Attendance", "Marks", "Announcements", "Change Password", "Logout"]
    else:
        menu = ["Dashboard", "My Profile", "My Attendance", "My Marks", "Announcements", "Feedback", "Change Password", "Logout"]
    choice = st.radio("Navigate", menu, index=0, key="nav_radio")

    st.markdown("---")
    if st.button("Logout", key="logout_btn"):
        st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None, "semester": None}
        st.experimental_rerun()

# -----------------------
# Small helpers to read/write domain JSONs
# -----------------------
def load_students():
    return load_json(STUDENTS_FILE)

def save_students(data):
    save_json(STUDENTS_FILE, data)

def load_teachers():
    return load_json(TEACHERS_FILE)

def save_teachers(data):
    save_json(TEACHERS_FILE, data)

def load_courses():
    return load_json(COURSES_FILE)

def save_courses(data):
    save_json(COURSES_FILE, data)

def load_attendance():
    return load_json(ATT_FILE)

def save_attendance(data):
    save_json(ATT_FILE, data)

def load_marks():
    return load_json(MARKS_FILE)

def save_marks(data):
    save_json(MARKS_FILE, data)

def load_ann():
    return load_json(ANN_FILE)

def save_ann(data):
    save_json(ANN_FILE, data)

def load_feedback():
    return load_json(FB_FILE)

def save_feedback(data):
    save_json(FB_FILE, data)

# -----------------------
# Dashboard card helper
# -----------------------
def show_cards():
    s = load_students()
    c = load_courses()
    a = load_ann()
    m = load_marks()
    col1, col2, col3, col4 = main.columns(4)
    with col1:
        st.markdown(f"<div class='card'><h4>Total Students</h4><h2>{len(s)}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><h4>Total Courses</h4><h2>{len(c)}</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><h4>Announcements</h4><h2>{len(a)}</h2></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='card'><h4>Marks</h4><h2>{len(m)}</h2></div>", unsafe_allow_html=True)
    main.markdown("---")

# -----------------------
# ADMIN features
# -----------------------
if role == "admin" and choice == "Manage Teachers":
    main.header("Manage Teachers")
    col1, col2 = main.columns(2)
    with col1:
        main.subheader("Add Teacher")
        t_un = main.text_input("Teacher username", key="t_un")
        t_name = main.text_input("Teacher display name", key="t_name")
        t_pw = main.text_input("Teacher password", type="password", key="t_pw")
        if main.button("Create Teacher", key="create_teacher"):
            if not (t_un and t_name and t_pw):
                main.warning("Fill all fields.")
            else:
                ok = create_user(t_un, t_name, t_pw, "teacher")
                if ok:
                    teachers = load_teachers()
                    teachers.append({"username": t_un, "name": t_name})
                    save_teachers(teachers)
                    main.success("Teacher created.")
                else:
                    main.error("Username already exists.")
    with col2:
        main.subheader("All Teachers")
        teachers = load_teachers()
        if teachers:
            main.dataframe(pd.DataFrame(teachers))
        else:
            main.info("No teachers yet.")

if role == "admin" and choice == "Manage Students":
    main.header("Manage Students")
    c1, c2 = main.columns(2)
    with c1:
        main.subheader("Add Student")
        s_roll = main.text_input("Roll (will be username)", key="s_roll")
        s_name = main.text_input("Student full name", key="s_name")
        s_sem = main.selectbox("Semester", list(range(1, 9)), index=0, key="s_sem")
        s_pw = main.text_input("Password (temporary)", type="password", key="s_pw")
        if main.button("Create Student", key="create_student"):
            if not (s_roll and s_name and s_pw):
                main.warning("Fill required fields.")
            else:
                ok = create_user(s_roll, s_name, s_pw, "student", semester=s_sem)
                if ok:
                    students = load_students()
                    students.append({"roll_no": s_roll, "name": s_name, "semester": s_sem})
                    save_students(students)
                    main.success("Student added.")
                else:
                    main.error("Roll/username already exists.")
    with c2:
        main.subheader("All Students")
        st.dataframe(pd.DataFrame(load_students()))

if role == "admin" and choice == "Courses":
    main.header("Courses")
    courses = load_courses()
    c1, c2 = main.columns(2)
    with c1:
        cname = main.text_input("Course name", key="course_name")
    with c2:
        csem = main.selectbox("Course semester", list(range(1,9)), key="course_sem")
    tlist = load_teachers()
    toptions = ["Unassigned"] + [t["username"] + " - " + t["name"] for t in tlist]
    assign = main.selectbox("Assign teacher", toptions, key="course_assign")
    if main.button("Add Course", key="add_course"):
        teacher_username = None
        if assign != "Unassigned":
            teacher_username = assign.split(" - ")[0]
        courses.append({"name": cname, "semester": csem, "teacher": teacher_username})
        save_courses(courses)
        main.success("Course added.")
    main.subheader("All Courses")
    if courses:
        main.dataframe(pd.DataFrame(courses))
    else:
        main.info("No courses yet.")

if role == "admin" and choice == "Attendance":
    main.header("Attendance — Admin (mark for any course)")
    courses = load_courses()
    if not courses:
        main.info("Add courses first.")
    else:
        sel_course = main.selectbox("Select course", [f"{i['name']} (sem {i['semester']})" for i in courses], key="admin_att_course")
        # find course dict
        course_obj = next((c for c in courses if f"{c['name']} (sem {c['semester']})" == sel_course), None)
        att_date = main.date_input("Date", value=date.today(), key="admin_att_date")
        studs = [s for s in load_students() if s["semester"] == course_obj["semester"]]
        main.write("Check present students (unchecked = absent):")
        present = []
        for s in studs:
            k = f"att_admin_{course_obj['name']}_{s['roll_no']}"
            if main.checkbox(f"{s['name']} ({s['roll_no']})", key=k):
                present.append(s['roll_no'])
        if main.button("Save Attendance", key="admin_att_save"):
            records = load_attendance()
            for s in studs:
                status = "Present" if s["roll_no"] in present else "Absent"
                records.append({"roll_no": s["roll_no"], "course": course_obj["name"], "date": att_date.isoformat(), "status": status})
            save_attendance(records)
            main.success("Saved attendance.")

if role == "admin" and choice == "Marks":
    main.header("Marks — Admin")
    studs = load_students()
    courses = load_courses()
    if not courses or not studs:
        main.info("Add courses and students first.")
    else:
        sel_course = main.selectbox("Select course", [c["name"] for c in courses], key="admin_mark_course")
        sel_roll = main.selectbox("Select student (roll)", [s["roll_no"] for s in studs], key="admin_mark_roll")
        marks_val = main.number_input("Marks (0-100)", min_value=0.0, max_value=100.0, key="admin_mark_val")
        grade = main.text_input("Grade (A, B+, ...)", key="admin_mark_grade")
        if main.button("Save Mark", key="admin_mark_save"):
            m = load_marks()
            m.append({"roll_no": sel_roll, "course": sel_course, "marks": marks_val, "grade": grade})
            save_marks(m)
            main.success("Mark saved.")

if role == "admin" and choice == "Announcements":
    main.header("Post Announcement")
    msg = main.text_area("Message", key="admin_ann_msg")
    if main.button("Post Announcement", key="admin_ann_post"):
        anns = load_ann()
        anns.append({"message": msg, "author": display_name, "created_at": datetime.now().isoformat()})
        save_ann(anns)
        main.success("Announcement posted.")
    main.subheader("All Announcements")
    main.dataframe(pd.DataFrame(load_ann())[::-1])

if role == "admin" and choice == "Feedback":
    main.header("Student Feedback")
    fb = load_feedback()
    if fb:
        main.dataframe(pd.DataFrame(fb)[::-1])
    else:
        main.info("No feedback yet.")

# -----------------------
# TEACHER features
# -----------------------
if role == "teacher" and choice == "My Courses":
    main.header("My Courses")
    courses = load_courses()
    my = [c for c in courses if c.get("teacher") == username]
    if my:
        main.dataframe(pd.DataFrame(my))
    else:
        main.info("No courses assigned to you yet.")

if role == "teacher" and choice == "Attendance":
    main.header("Attendance — Teacher")
    courses = [c for c in load_courses() if c.get("teacher") == username]
    if not courses:
        main.info("No assigned courses.")
    else:
        sel_course = main.selectbox("Select course", [c["name"] for c in courses], key="teach_att_course")
        course_obj = next(c for c in courses if c["name"] == sel_course)
        att_date = main.date_input("Date", date.today(), key="teach_att_date")
        studs = [s for s in load_students() if s["semester"] == course_obj["semester"]]
        main.write("Check present students:")
        present = []
        for s in studs:
            k = f"att_teacher_{course_obj['name']}_{s['roll_no']}"
            if main.checkbox(f"{s['name']} ({s['roll_no']})", key=k):
                present.append(s['roll_no'])
        if main.button("Save Attendance (teacher)", key="teach_att_save"):
            records = load_attendance()
            for s in studs:
                status = "Present" if s["roll_no"] in present else "Absent"
                records.append({"roll_no": s["roll_no"], "course": course_obj["name"], "date": att_date.isoformat(), "status": status})
            save_attendance(records)
            main.success("Attendance saved.")

if role == "teacher" and choice == "Marks":
    main.header("Add Marks — Teacher")
    courses = [c for c in load_courses() if c.get("teacher") == username]
    if not courses:
        main.info("No assigned courses.")
    else:
        sel_course = main.selectbox("Select course", [c["name"] for c in courses], key="teach_mark_course")
        studs = [s for s in load_students() if s["semester"] == next(c for c in courses if c["name"]==sel_course)["semester"]]
        sel_roll = main.selectbox("Select student", [s["roll_no"] for s in studs], key="teach_mark_roll")
        marks_val = main.number_input("Marks", 0.0, 100.0, key="teach_mark_val")
        grade = main.text_input("Grade", key="teach_mark_grade")
        if main.button("Save Mark (teacher)", key="teach_mark_save"):
            m = load_marks()
            m.append({"roll_no": sel_roll, "course": sel_course, "marks": marks_val, "grade": grade})
            save_marks(m)
            main.success("Saved mark.")

# -----------------------
# STUDENT features
# -----------------------
if role == "student" and choice == "Dashboard":
    main.header("Student Dashboard")
    s = next((x for x in load_students() if x["roll_no"] == username), None)
    if not s:
        main.info("Student record missing. Contact admin.")
    else:
        sem = s["semester"]
        tot_courses = len([c for c in load_courses() if c["semester"] == sem])
        ann_count = len(load_ann())
        col1, col2 = main.columns(2)
        with col1:
            st.markdown(f"<div class='card'><h4>Semester</h4><h2>{sem}</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='card'><h4>Courses</h4><h2>{tot_courses}</h2></div>", unsafe_allow_html=True)
        main.markdown("---")

if role == "student" and choice == "My Profile":
    main.header("My Profile")
    s = next((x for x in load_students() if x["roll_no"] == username), None)
    if s:
        main.write(f"**Name:** {s['name']}")
        main.write(f"**Roll:** {s['roll_no']}")
        main.write(f"**Semester:** {s['semester']}")
    else:
        main.info("Profile missing.")

if role == "student" and choice == "My Attendance":
    main.header("My Attendance")
    all_att = load_attendance()
    my_att = [a for a in all_att if a["roll_no"] == username]
    if not my_att:
        main.info("No attendance records yet.")
    else:
        df = pd.DataFrame(my_att)
        main.dataframe(df)

if role == "student" and choice == "My Marks":
    main.header("My Marks")
    all_marks = load_marks()
    my_marks = [m for m in all_marks if m["roll_no"] == username]
    if not my_marks:
        main.info("No marks yet.")
    else:
        main.dataframe(pd.DataFrame(my_marks))

if choice == "Announcements":
    main.header("Announcements")
    anns = load_ann()
    if not anns:
        main.info("No announcements.")
    else:
        for a in reversed(anns):
            main.markdown(f"**{a.get('author','Admin')}** — {a.get('created_at','')}")
            main.info(a["message"])

if role == "student" and choice == "Feedback":
    main.header("Send Feedback")
    msg = main.text_area("Your message", key="fb_msg")
    if main.button("Send Feedback", key="fb_send"):
        fb = load_feedback()
        fb.append({"roll_no": username, "message": msg, "created_at": datetime.now().isoformat()})
        save_feedback(fb)
        main.success("Feedback sent.")

# -----------------------
# Change password (all roles)
# -----------------------
if choice == "Change Password":
    main.header("Change Password")
    cur_pw = main.text_input("Current password", type="password", key="chg_cur")
    new_pw = main.text_input("New password", type="password", key="chg_new")
    new_pw2 = main.text_input("Confirm new password", type="password", key="chg_new2")
    if main.button("Change Password Now", key="chg_save"):
        u = find_user(username)
        if not u:
            main.error("User record missing.")
        elif hash_pw(cur_pw) != u["password_hash"]:
            main.error("Current password incorrect.")
        elif new_pw != new_pw2:
            main.error("New passwords do not match.")
        else:
            update_user_password(username, new_pw)
            main.success("Password changed successfully.")

# -----------------------
# Logout handled above (button in sidebar)
# -----------------------

# ai_department_portal.py
# Superior University — AI Department Portal (SQLite backend)
# Single-file Streamlit app

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime, date

# -----------------------
# Helpers: hashing, DB
# -----------------------
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

DB_FILE = "portal.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # users: username unique (for students roll number used as username), display_name, password_hash, role
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        display_name TEXT,
        password_hash TEXT,
        role TEXT
    )
    """)
    # students: roll_no PRIMARY KEY, name, semester
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        roll_no TEXT PRIMARY KEY,
        name TEXT,
        semester INTEGER
    )
    """)
    # teachers: username references users.username
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        username TEXT PRIMARY KEY,
        name TEXT
    )
    """)
    # semesters (1..8)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS semesters (
        id INTEGER PRIMARY KEY,
        name TEXT
    )
    """)
    # courses: id, name, semester, teacher_username (nullable)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        semester INTEGER,
        teacher_username TEXT
    )
    """)
    # attendance: id, roll_no, course_id, date, status ('Present'/'Absent')
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT,
        course_id INTEGER,
        date TEXT,
        status TEXT
    )
    """)
    # marks: id, roll_no, course_id, marks, grade, remarks
    cur.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT,
        course_id INTEGER,
        marks REAL,
        grade TEXT,
        remarks TEXT
    )
    """)
    # announcements
    cur.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        author TEXT,
        created_at TEXT
    )
    """)
    # feedback
    cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT,
        message TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    # Seed semesters 1..8 if not present
    cur.execute("SELECT COUNT(*) FROM semesters")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        for i in range(1, 9):
            cur.execute("INSERT INTO semesters (id, name) VALUES (?, ?)", (i, f"Semester {i}"))
        conn.commit()
    # Create default admin if not exists
    cur.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not cur.fetchone():
        pw_hash = hash_pw("admin123")
        cur.execute("INSERT INTO users (username, display_name, password_hash, role) VALUES (?, ?, ?, ?)",
                    ("admin", "Administrator", pw_hash, "admin"))
        conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# -----------------------
# Utility DB functions
# -----------------------
def query_df(sql, params=()):
    conn = get_db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()

# -----------------------
# Streamlit UI: styling
# -----------------------
st.set_page_config(page_title="AI Department Portal | Superior University", layout="wide")
st.markdown("""
<style>
body { background-color: #0b0b0b; color: #e8e8e8; }
.header { text-align:center; padding:8px 0; }
.title { color: #bb86fc; font-size:28px; font-weight:700; }
.subtitle { color: #a97df0; font-size:14px; margin-bottom:12px; }
.card { background: linear-gradient(135deg,#6a0dad,#9b59b6); color:white; padding:18px; border-radius:14px;
       box-shadow: 0 6px 18px rgba(155,89,182,0.12); text-align:center; }
.small-muted { color:#bdbdbd; font-size:12px; }
.left-pane { background-color:#0f0f0f; padding:12px; border-right:1px solid #222; min-height:520px; }
.sidebar-item { padding:10px 6px; border-radius:8px; margin-bottom:6px; }
.sidebar-item:hover { background: rgba(106,13,173,0.08); }
.btn { background: linear-gradient(90deg,#8e2de2,#4a00e0); color:white; border:none; padding:8px 14px; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><div class="title">AI Department Portal | Superior University</div>'
            '<div class="subtitle">Faculty & Student Dashboard — Semesters 1 to 8</div></div>', unsafe_allow_html=True)

# -----------------------
# Authentication
# -----------------------
if "auth" not in st.session_state:
    st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None}

def login_user(username: str, password: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, display_name, password_hash, role FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        stored_hash = row[2]
        if hash_pw(password) == stored_hash:
            return {"username": row[0], "display_name": row[1], "role": row[3]}
    return None

# Login form (only shown when not logged in)
if not st.session_state.auth["logged_in"]:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.subheader("Login")
        username = st.text_input("Username (admin or teacher username or student roll number)")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            res = login_user(username.strip(), password.strip())
            if res:
                st.session_state.auth = {"logged_in": True,
                                         "username": res["username"],
                                         "display_name": res["display_name"],
                                         "role": res["role"]}
                st.success(f"Welcome {res['display_name']} — {res['role'].capitalize()}")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

# -----------------------
# Sidebar navigation (always visible after login)
# -----------------------
role = st.session_state.auth["role"]
user = st.session_state.auth["username"]
display_name = st.session_state.auth["display_name"]

left, main = st.columns([1, 4])

with left:
    st.markdown(f"### Welcome, {display_name}")
    st.markdown(f"**Role:** {role.capitalize()}")
    st.markdown("---")
    # Sidebar items depend on role
    if role == "admin":
        menu = ["Dashboard", "Manage Teachers", "Manage Students", "Semesters & Courses",
                "Attendance", "Marks", "Announcements", "Feedback", "Change Password", "Logout"]
    elif role == "teacher":
        menu = ["Dashboard", "My Courses", "Attendance", "Marks", "Announcements", "Change Password", "Logout"]
    else:
        menu = ["Dashboard", "My Profile", "My Attendance", "My Marks", "Announcements", "Feedback", "Change Password", "Logout"]

    choice = st.radio("Navigate", menu, index=0)

    st.markdown("---")
    if st.button("Logout"):
        st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None}
        st.experimental_rerun()

# -----------------------
# Helper UI pieces
# -----------------------
def show_dashboard_cards():
    students_df = query_df("SELECT * FROM students")
    courses_df = query_df("SELECT * FROM courses")
    ann_df = query_df("SELECT * FROM announcements")
    marks_df = query_df("SELECT * FROM marks")
    att_df = query_df("SELECT * FROM attendance")
    col1, col2, col3, col4 = main.columns(4)
    with col1:
        st.markdown(f"<div class='card'><h3>Total Students</h3><h2>{len(students_df)}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><h3>Total Courses</h3><h2>{len(courses_df)}</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><h3>Announcements</h3><h2>{len(ann_df)}</h2></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='card'><h3>Total Marks Records</h3><h2>{len(marks_df)}</h2></div>", unsafe_allow_html=True)
    main.markdown("----")

# -----------------------
# ADMIN: Manage Teachers
# -----------------------
if role == "admin" and choice == "Manage Teachers":
    main.header("Manage Teachers")
    colA, colB = main.columns(2)
    with colA:
        main.subheader("Add Teacher")
        t_username = main.text_input("Teacher username", key="t_user")
        t_name = main.text_input("Teacher full name", key="t_name")
        t_pw = main.text_input("Teacher password", type="password", key="t_pw")
        if main.button("Create Teacher"):
            if not (t_username and t_name and t_pw):
                main.warning("Fill all fields.")
            else:
                # create users entry and teachers table
                try:
                    execute("INSERT INTO users (username, display_name, password_hash, role) VALUES (?, ?, ?, ?)",
                            (t_username, t_name, hash_pw(t_pw), "teacher"))
                    execute("INSERT INTO teachers (username, name) VALUES (?, ?)", (t_username, t_name))
                    main.success("Teacher created.")
                except Exception as e:
                    main.error("Could not create teacher — maybe username exists.")
    with colB:
        main.subheader("All Teachers")
        t_df = query_df("SELECT u.username, t.name FROM users u JOIN teachers t ON u.username = t.username")
        main.dataframe(t_df)

# -----------------------
# ADMIN: Manage Students
# -----------------------
if role == "admin" and choice == "Manage Students":
    main.header("Manage Students")
    c1, c2 = main.columns(2)
    with c1:
        main.subheader("Add Student")
        s_roll = main.text_input("Roll number", key="s_roll")
        s_name = main.text_input("Full name", key="s_name")
        s_sem = main.selectbox("Semester", list(range(1, 9)), index=0, key="s_sem")
        s_pw = main.text_input("Password (temporary)", type="password", key="s_pw")
        if main.button("Create Student"):
            if not (s_roll and s_name and s_pw):
                main.warning("Fill required fields.")
            else:
                try:
                    execute("INSERT INTO users (username, display_name, password_hash, role) VALUES (?, ?, ?, ?)",
                            (s_roll, s_name, hash_pw(s_pw), "student"))
                    execute("INSERT INTO students (roll_no, name, semester) VALUES (?, ?, ?)",
                            (s_roll, s_name, s_sem))
                    main.success("Student added.")
                except Exception as e:
                    main.error("Could not add student (roll may already exist).")
    with c2:
        main.subheader("All Students")
        s_df = query_df("SELECT * FROM students")
        main.dataframe(s_df)

# -----------------------
# ADMIN: Semesters & Courses
# -----------------------
if role == "admin" and choice == "Semesters & Courses":
    main.header("Semesters & Courses")
    # show semesters
    sems = query_df("SELECT * FROM semesters")
    main.subheader("Semesters")
    main.dataframe(sems)
    main.subheader("Add Course")
    cc1, cc2 = main.columns(2)
    with cc1:
        cname = main.text_input("Course name", key="cname")
    with cc2:
        csem = main.selectbox("Course semester", list(range(1, 9)), key="csem")
    tusers = query_df("SELECT username, display_name FROM users WHERE role='teacher'")
    teacher_options = ["Unassigned"] + [f"{r['username']} - {r['display_name']}" for _, r in tusers.iterrows()]
    cteacher = main.selectbox("Assign teacher (optional)", teacher_options, key="ct")
    if main.button("Create Course"):
        teacher_user = None
        if cteacher != "Unassigned":
            teacher_user = cteacher.split(" - ")[0]
        execute("INSERT INTO courses (name, semester, teacher_username) VALUES (?, ?, ?)",
                (cname, csem, teacher_user))
        main.success("Course created.")
    main.subheader("All Courses")
    courses_df = query_df("SELECT c.id, c.name, c.semester, c.teacher_username, u.display_name as teacher_name FROM courses c LEFT JOIN users u ON c.teacher_username = u.username")
    main.dataframe(courses_df)

# -----------------------
# ADMIN: Attendance overview & marking (admin can also mark)
# -----------------------
if role == "admin" and choice == "Attendance":
    main.header("Attendance — Admin Panel")
    courses_df = query_df("SELECT id, name, semester FROM courses")
    if courses_df.empty:
        main.info("No courses yet.")
    else:
        selected = main.selectbox("Select course", courses_df["name"].tolist())
        course_row = courses_df[courses_df["name"] == selected].iloc[0]
        course_id = int(course_row["id"])
        # date selector
        att_date = main.date_input("Attendance date", value=date.today())
        students_in_sem = query_df("SELECT * FROM students WHERE semester = ?", (course_row["semester"],))
        if students_in_sem.empty:
            main.info("No students found for this semester.")
        else:
            main.write("Mark Present (check box) — unchecked = Absent")
            present = []
            for idx, s in students_in_sem.iterrows():
                chk = main.checkbox(f"{s['name']} ({s['roll_no']})", key=f"att_{s['roll_no']}")
                if chk:
                    present.append(s['roll_no'])
            if main.button("Save Attendance"):
                # save each student status
                for idx, s in students_in_sem.iterrows():
                    status = "Present" if s['roll_no'] in present else "Absent"
                    execute("INSERT INTO attendance (roll_no, course_id, date, status) VALUES (?, ?, ?, ?)",
                            (s['roll_no'], course_id, att_date.isoformat(), status))
                main.success("Attendance saved for date " + att_date.isoformat())

# -----------------------
# ADMIN: Marks
# -----------------------
if role == "admin" and choice == "Marks":
    main.header("Marks — Admin Panel")
    students_df = query_df("SELECT roll_no, name FROM students")
    courses_df = query_df("SELECT id, name FROM courses")
    if courses_df.empty:
        main.info("No courses to add marks for.")
    else:
        sel_course = main.selectbox("Select course", courses_df["name"].tolist())
        course_id = int(courses_df[courses_df["name"] == sel_course]["id"].iloc[0])
        sel_roll = main.selectbox("Select student", students_df["roll_no"].tolist())
        marks_val = main.number_input("Marks (0-100)", min_value=0.0, max_value=100.0, value=0.0)
        grade = main.text_input("Grade (e.g., A, B+)", "")
        remarks = main.text_input("Remarks (optional)", "")
        if main.button("Save Marks"):
            execute("INSERT INTO marks (roll_no, course_id, marks, grade, remarks) VALUES (?, ?, ?, ?, ?)",
                    (sel_roll, course_id, marks_val, grade, remarks))
            main.success("Marks saved.")

# -----------------------
# ADMIN: Announcements
# -----------------------
if role == "admin" and choice == "Announcements":
    main.header("Post Announcement")
    msg = main.text_area("Announcement message")
    if main.button("Post Announcement"):
        execute("INSERT INTO announcements (message, author, created_at) VALUES (?, ?, ?)",
                (msg, display_name, datetime.now().isoformat()))
        main.success("Announcement posted.")
    main.subheader("All Announcements")
    ann = query_df("SELECT * FROM announcements ORDER BY created_at DESC")
    main.dataframe(ann)

# -----------------------
# ADMIN: Feedback
# -----------------------
if role == "admin" and choice == "Feedback":
    main.header("Student Feedback")
    fb = query_df("SELECT * FROM feedback ORDER BY created_at DESC")
    main.dataframe(fb)

# -----------------------
# TEACHER: My Courses & Attendance & Marks
# -----------------------
if role == "teacher" and choice == "My Courses":
    main.header("My Courses")
    my_courses = query_df("SELECT id, name, semester FROM courses WHERE teacher_username = ?", (user,))
    main.dataframe(my_courses)

if role == "teacher" and choice == "Attendance":
    main.header("Mark Attendance (Teacher)")
    my_courses = query_df("SELECT id, name, semester FROM courses WHERE teacher_username = ?", (user,))
    if my_courses.empty:
        main.info("No courses assigned to you.")
    else:
        sel = main.selectbox("Select course", my_courses["name"].tolist())
        course_row = my_courses[my_courses["name"] == sel].iloc[0]
        course_id = int(course_row["id"])
        att_date = main.date_input("Date", date.today())
        studs = query_df("SELECT * FROM students WHERE semester = ?", (course_row["semester"],))
        if studs.empty:
            main.info("No students for this semester.")
        else:
            main.write("Check students who are present:")
            present = []
            for idx, s in studs.iterrows():
                cb = main.checkbox(f"{s['name']} ({s['roll_no']})", key=f"tatt_{s['roll_no']}")
                if cb:
                    present.append(s['roll_no'])
            if main.button("Save Attendance for Course"):
                for idx, s in studs.iterrows():
                    status = "Present" if s['roll_no'] in present else "Absent"
                    execute("INSERT INTO attendance (roll_no, course_id, date, status) VALUES (?, ?, ?, ?)",
                            (s['roll_no'], course_id, att_date.isoformat(), status))
                main.success("Attendance saved.")

if role == "teacher" and choice == "Marks":
    main.header("Add Marks (Teacher)")
    my_courses = query_df("SELECT id, name, semester FROM courses WHERE teacher_username = ?", (user,))
    if my_courses.empty:
        main.info("No courses assigned.")
    else:
        sel_course = main.selectbox("Select course", my_courses["name"].tolist())
        course_id = int(query_df("SELECT id FROM courses WHERE name = ?", (sel_course,))["id"].iloc[0])
        studs = query_df("SELECT roll_no, name FROM students WHERE semester = ?", (query_df("SELECT semester FROM courses WHERE id = ?", (course_id,))["semester"].iloc[0],))
        if studs.empty:
            main.info("No students in semester.")
        else:
            sel_roll = main.selectbox("Select student", studs["roll_no"].tolist())
            marks_val = main.number_input("Marks", 0.0, 100.0, 0.0)
            grade = main.text_input("Grade")
            remarks = main.text_input("Remarks")
            if main.button("Save Marks for student"):
                execute("INSERT INTO marks (roll_no, course_id, marks, grade, remarks) VALUES (?, ?, ?, ?, ?)",
                        (sel_roll, course_id, marks_val, grade, remarks))
                main.success("Marks saved.")

# -----------------------
# STUDENT: Dashboard, Attendance, Marks, Profile
# -----------------------
if role == "student" and choice == "Dashboard":
    main.header("Student Dashboard")
    # show student stats
    s_roll = user
    s_row = query_df("SELECT * FROM students WHERE roll_no = ?", (s_roll,))
    if s_row.empty:
        main.info("Student record not found. Contact admin.")
    else:
        s_sem = int(s_row["semester"].iloc[0])
        # counts
        tot_courses = len(query_df("SELECT * FROM courses WHERE semester = ?", (s_sem,)))
        tot_ann = len(query_df("SELECT * FROM announcements"))
        main_col1, main_col2 = main.columns([2,3])
        with main_col1:
            st.markdown(f"<div class='card'><h3>Enrolled Semester</h3><h2>Semester {s_sem}</h2></div>", unsafe_allow_html=True)
        with main_col2:
            st.markdown(f"<div class='card'><h3>My Courses</h3><h2>{tot_courses}</h2></div>", unsafe_allow_html=True)
        main.markdown("----")

if role == "student" and choice == "My Profile":
    main.header("My Profile")
    r = query_df("SELECT * FROM students WHERE roll_no = ?", (user,))
    if r.empty:
        main.info("Profile missing.")
    else:
        rec = r.iloc[0]
        main.write(f"**Name:** {rec['name']}")
        main.write(f"**Roll:** {rec['roll_no']}")
        main.write(f"**Semester:** {rec['semester']}")

if role == "student" and choice == "My Attendance":
    main.header("My Attendance")
    df = query_df("SELECT a.date, c.name AS course, a.status FROM attendance a JOIN courses c ON a.course_id = c.id WHERE a.roll_no = ? ORDER BY a.date DESC", (user,))
    if df.empty:
        main.info("No attendance records.")
    else:
        # show percentage per course
        stats = {}
        for _, row in df.iterrows():
            course = row["course"]
            stats.setdefault(course, {"present":0, "total":0})
            stats[course]["total"] += 1
            if row["status"] == "Present":
                stats[course]["present"] += 1
        # display table
        rows = []
        for course, v in stats.items():
            pct = (v["present"] / v["total"] * 100) if v["total"] else 0
            rows.append({"Course": course, "Present": v["present"], "Total": v["total"], "Attendance %": f"{pct:.1f}%"})
        main.dataframe(pd.DataFrame(rows))

if role == "student" and choice == "My Marks":
    main.header("My Marks")
    df = query_df("SELECT m.marks, m.grade, m.remarks, c.name AS course FROM marks m JOIN courses c ON m.course_id = c.id WHERE m.roll_no = ?", (user,))
    if df.empty:
        main.info("No marks yet.")
    else:
        main.dataframe(df)

# -----------------------
# ANNOUNCEMENTS (all roles)
# -----------------------
if choice == "Announcements":
    main.header("Announcements")
    ann = query_df("SELECT message, author, created_at FROM announcements ORDER BY created_at DESC")
    if ann.empty:
        main.info("No announcements.")
    else:
        for _, r in ann.iterrows():
            main.markdown(f"**{r['author']}** — {r['created_at']}")
            main.info(r['message'])

# -----------------------
# FEEDBACK (students) & Admin view
# -----------------------
if role == "student" and choice == "Feedback":
    main.header("Send Feedback to Admin")
    msg = main.text_area("Your message")
    if main.button("Send Feedback"):
        execute("INSERT INTO feedback (roll_no, message, created_at) VALUES (?, ?, ?)", (user, msg, datetime.now().isoformat()))
        main.success("Feedback sent to admin.")

# -----------------------
# Change password (all roles)
# -----------------------
if choice == "Change Password":
    main.header("Change Password")
    old_pw = main.text_input("Current password", type="password")
    new_pw = main.text_input("New password", type="password")
    new_pw2 = main.text_input("Confirm new password", type="password")
    if main.button("Change Password Now"):
        # verify current
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (user,))
        row = cur.fetchone()
        conn.close()
        if not row:
            main.error("User record not found.")
        elif hash_pw(old_pw) != row[0]:
            main.error("Current password incorrect.")
        elif new_pw != new_pw2:
            main.error("New passwords do not match.")
        else:
            execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_pw(new_pw), user))
            main.success("Password changed successfully.")

# -----------------------
# Logout via radio option
# -----------------------
if choice == "Logout":
    st.session_state.auth = {"logged_in": False, "username": None, "display_name": None, "role": None}
    st.experimental_rerun()

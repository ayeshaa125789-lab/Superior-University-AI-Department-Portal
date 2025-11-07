import streamlit as st
import sqlite3
import hashlib

# --------------------------- DATABASE SETUP ---------------------------
conn = sqlite3.connect('portal.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    name TEXT,
    password TEXT,
    role TEXT,
    semester TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course TEXT,
    date TEXT,
    status TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course TEXT,
    marks INTEGER,
    total INTEGER
)''')

c.execute('''CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    message TEXT
)''')
conn.commit()

# --------------------------- UTILITY FUNCTIONS ---------------------------
def make_hashes(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_hashes(password, hashed):
    return make_hashes(password) == hashed

def add_user(username, name, password, role, semester=""):
    c.execute('INSERT INTO users (username, name, password, role, semester) VALUES (?,?,?,?,?)',
              (username, name, make_hashes(password), role, semester))
    conn.commit()

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    data = c.fetchone()
    if data and check_hashes(password, data[3]):
        return data
    return None

# --------------------------- INITIAL ADMIN ---------------------------
c.execute("SELECT * FROM users WHERE role='admin'")
if not c.fetchone():
    add_user("admin", "Administrator", "admin123", "admin")
    conn.commit()

# --------------------------- DASHBOARDS ---------------------------
def admin_dashboard():
    st.title("🎓 Superior University - AI Department Portal (Admin Dashboard)")

    menu = ["Add Student", "Add Teacher", "Add Course", "Mark Attendance",
            "Add Results", "Announcements", "View Feedback"]
    choice = st.sidebar.radio("Select Option", menu)

    if choice == "Add Student":
        st.subheader("➕ Add New Student")
        name = st.text_input("Full Name")
        roll = st.text_input("Roll No")
        sem = st.selectbox("Semester", [str(i) for i in range(1, 9)])
        pw = st.text_input("Password", type="password")
        if st.button("Add Student"):
            try:
                add_user(roll, name, pw, "student", sem)
                st.success(f"Student {name} added successfully!")
            except:
                st.error("Roll number already exists!")

    elif choice == "Add Teacher":
        st.subheader("👨‍🏫 Add Teacher")
        name = st.text_input("Teacher Name")
        uname = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Add Teacher"):
            try:
                add_user(uname, name, pw, "teacher")
                st.success(f"Teacher {name} added successfully!")
            except:
                st.error("Username already exists!")

    elif choice == "Mark Attendance":
        st.subheader("📋 Mark Attendance")
        c.execute("SELECT username, name FROM users WHERE role='student'")
        students = c.fetchall()
        for s in students:
            status = st.selectbox(f"{s[1]} ({s[0]})", ["Present", "Absent"], key=s[0])
            if st.button(f"Save {s[0]}", key=s[0] + "_btn"):
                c.execute("INSERT INTO attendance (student, course, date, status) VALUES (?,?,DATE('now'),?)",
                          (s[0], "AI Fundamentals", status))
                conn.commit()
                st.success(f"Attendance saved for {s[1]}")

    elif choice == "Add Results":
        st.subheader("📊 Add Results")
        c.execute("SELECT username, name FROM users WHERE role='student'")
        students = c.fetchall()
        for s in students:
            marks = st.number_input(f"{s[1]} ({s[0]}) - Marks", 0, 100, key=s[0] + "_marks")
            total = st.number_input(f"{s[1]} ({s[0]}) - Total", 0, 100, 100, key=s[0] + "_total")
            if st.button(f"Save Result {s[0]}", key=s[0] + "_save"):
                c.execute("INSERT INTO results (student, course, marks, total) VALUES (?,?,?,?)",
                          (s[0], "AI Fundamentals", marks, total))
                conn.commit()
                st.success(f"Result saved for {s[1]}")

    elif choice == "Announcements":
        st.subheader("📢 Make Announcement")
        msg = st.text_area("Announcement Message")
        if st.button("Post"):
            c.execute("INSERT INTO announcements (message) VALUES (?)", (msg,))
            conn.commit()
            st.success("Announcement posted successfully!")

    elif choice == "View Feedback":
        st.subheader("💬 Student Feedback")
        c.execute("SELECT * FROM feedback")
        rows = c.fetchall()
        if rows:
            for f in rows:
                st.info(f"{f[1]}: {f[2]}")
        else:
            st.warning("No feedback yet.")

def student_dashboard(user):
    st.title(f"👩‍🎓 Welcome, {user[2]} ({user[1]})")
    st.subheader(f"Semester: {user[5]}")

    tabs = st.tabs(["📢 Announcements", "📊 Results", "📋 Attendance", "💬 Feedback"])

    with tabs[0]:
        c.execute("SELECT * FROM announcements")
        for a in c.fetchall():
            st.info(a[1])

    with tabs[1]:
        c.execute("SELECT course, marks, total FROM results WHERE student=?", (user[1],))
        res = c.fetchall()
        if res:
            for r in res:
                st.write(f"{r[0]}: {r[1]}/{r[2]}")
        else:
            st.warning("No results uploaded yet.")

    with tabs[2]:
        c.execute("SELECT course, date, status FROM attendance WHERE student=?", (user[1],))
        att = c.fetchall()
        if att:
            for a in att:
                st.write(f"{a[1]} - {a[0]}: {a[2]}")
        else:
            st.warning("No attendance records yet.")

    with tabs[3]:
        fb = st.text_area("Enter your feedback")
        if st.button("Submit Feedback"):
            c.execute("INSERT INTO feedback (student, message) VALUES (?,?)", (user[1], fb))
            conn.commit()
            st.success("Feedback sent successfully!")

def teacher_dashboard(user):
    st.title(f"👨‍🏫 Welcome, {user[2]}")
    st.subheader("You can mark attendance and upload results")

# --------------------------- MAIN LOGIN ---------------------------
def main():
    st.set_page_config(page_title="AI Department Portal", page_icon="🎓", layout="wide")
    st.markdown("<h2 style='text-align:center;color:#B26BFF;'>🎓 Superior University - AI Department Portal</h2>", unsafe_allow_html=True)

    menu = ["Login"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        username = st.text_input("Username / Roll No")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Invalid credentials! Try again.")

    if "user" in st.session_state:
        role = st.session_state["user"][4]
        if role == "admin":
            admin_dashboard()
        elif role == "student":
            student_dashboard(st.session_state["user"])
        elif role == "teacher":
            teacher_dashboard(st.session_state["user"])
        st.sidebar.button("Logout", on_click=lambda: st.session_state.pop("user") or st.rerun())

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import os

# --- CSV Files ---
USER_FILE = "users.csv"
COURSE_FILE = "courses.csv"
ATTENDANCE_FILE = "attendance.csv"
RESULTS_FILE = "results.csv"

# --- Initialize CSVs if they don't exist ---
def init_csv():
    if not os.path.exists(USER_FILE):
        users = pd.DataFrame(columns=["username","roll_no","password","role","semester"])
        users = users.append({"username":"admin","roll_no":"","password":"123","role":"admin","semester":""}, ignore_index=True)
        users.to_csv(USER_FILE,index=False)

    if not os.path.exists(COURSE_FILE):
        courses = pd.DataFrame(columns=["course_name","semester"])
        courses.to_csv(COURSE_FILE,index=False)

    if not os.path.exists(ATTENDANCE_FILE):
        attendance = pd.DataFrame(columns=["student_username","course_name","attended","total"])
        attendance.to_csv(ATTENDANCE_FILE,index=False)

    if not os.path.exists(RESULTS_FILE):
        results = pd.DataFrame(columns=["student_username","course_name","marks"])
        results.to_csv(RESULTS_FILE,index=False)

# --- Load CSVs ---
def load_users():
    return pd.read_csv(USER_FILE)

def load_courses():
    return pd.read_csv(COURSE_FILE)

def load_attendance():
    return pd.read_csv(ATTENDANCE_FILE)

def load_results():
    return pd.read_csv(RESULTS_FILE)

# --- Save CSVs ---
def save_users(df):
    df.to_csv(USER_FILE,index=False)

def save_courses(df):
    df.to_csv(COURSE_FILE,index=False)

def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE,index=False)

def save_results(df):
    df.to_csv(RESULTS_FILE,index=False)

# --- Admin Dashboard ---
def admin_dashboard(username):
    st.markdown("<h2 style='color:purple;'>Admin Dashboard</h2>", unsafe_allow_html=True)
    menu = ["Add Student","View Students","Add Course","View Courses","Mark Attendance","Add Results","View Results","Announcements","View Feedback"]
    choice = st.sidebar.selectbox("Select Option", menu)

    users = load_users()
    courses = load_courses()
    attendance = load_attendance()
    results = load_results()

    if choice == "Add Student":
        st.subheader("Add Student")
        with st.form("add_student", clear_on_submit=True):
            uname = st.text_input("Username")
            roll = st.text_input("Roll Number")
            pwd = st.text_input("Password", type="password")
            sem = st.selectbox("Semester", list(range(1,9)))
            submitted = st.form_submit_button("Add Student")
            if submitted:
                if uname in users["username"].values:
                    st.warning("Username already exists!")
                else:
                    new = {"username":uname,"roll_no":roll,"password":pwd,"role":"student","semester":sem}
                    users = users.append(new, ignore_index=True)
                    save_users(users)
                    st.success(f"Student {uname} added successfully!")

    elif choice == "View Students":
        st.subheader("All Students")
        st.dataframe(users[users["role"]=="student"])

    elif choice == "Add Course":
        st.subheader("Add Course")
        with st.form("add_course", clear_on_submit=True):
            cname = st.text_input("Course Name")
            sem = st.selectbox("Semester", list(range(1,9)))
            submitted = st.form_submit_button("Add Course")
            if submitted:
                if cname in courses["course_name"].values:
                    st.warning("Course already exists!")
                else:
                    courses = courses.append({"course_name":cname,"semester":sem}, ignore_index=True)
                    save_courses(courses)
                    st.success(f"Course {cname} added for Semester {sem}")

    elif choice == "View Courses":
        st.subheader("All Courses")
        st.dataframe(courses)

    elif choice == "Mark Attendance":
        st.subheader("Mark Attendance")
        sem = st.selectbox("Select Semester", list(range(1,9)), key="att_sem")
        sem_students = users[(users["role"]=="student") & (users["semester"]==sem)]
        sem_courses = courses[courses["semester"]==sem]
        if not sem_students.empty and not sem_courses.empty:
            st.text("Select Student and Course to mark attendance")
            student = st.selectbox("Student", sem_students["username"], key="att_student")
            course = st.selectbox("Course", sem_courses["course_name"], key="att_course")
            attended = st.number_input("Attended Classes", min_value=0, step=1)
            total = st.number_input("Total Classes", min_value=0, step=1)
            if st.button("Submit Attendance"):
                attendance = attendance.append({"student_username":student,"course_name":course,"attended":attended,"total":total}, ignore_index=True)
                save_attendance(attendance)
                st.success("Attendance added successfully!")
        else:
            st.warning("No students or courses in this semester.")

    elif choice == "Add Results":
        st.subheader("Add Results")
        sem = st.selectbox("Select Semester", list(range(1,9)), key="res_sem")
        sem_students = users[(users["role"]=="student") & (users["semester"]==sem)]
        sem_courses = courses[courses["semester"]==sem]
        if not sem_students.empty and not sem_courses.empty:
            student = st.selectbox("Student", sem_students["username"], key="res_student")
            course = st.selectbox("Course", sem_courses["course_name"], key="res_course")
            marks = st.number_input("Marks", min_value=0, step=1)
            if st.button("Submit Marks"):
                results = results.append({"student_username":student,"course_name":course,"marks":marks}, ignore_index=True)
                save_results(results)
                st.success("Results added successfully!")
        else:
            st.warning("No students or courses in this semester.")

    elif choice == "View Results":
        st.subheader("All Results")
        st.dataframe(results)

    else:
        st.info("Feature coming soon!")

# --- Student Dashboard ---
def student_dashboard(username):
    st.markdown("<h2 style='color:purple;'>Student Dashboard</h2>", unsafe_allow_html=True)
    users = load_users()
    courses = load_courses()
    attendance = load_attendance()
    results = load_results()

    user = users[users["username"]==username].iloc[0]
    st.text(f"Name: {username}")
    st.text(f"Roll Number: {user['roll_no']}")
    st.text(f"Semester: {user['semester']}")

    st.subheader("Courses")
    sem_courses = courses[courses["semester"]==user["semester"]]
    st.dataframe(sem_courses)

    st.subheader("Attendance")
    sem_attendance = attendance[attendance["student_username"]==username]
    st.dataframe(sem_attendance)

    st.subheader("Results")
    sem_results = results[results["student_username"]==username]
    st.dataframe(sem_results)

    # Change password
    st.subheader("Change Password")
    new_pwd = st.text_input("New Password", type="password", key="newpwd")
    if st.button("Update Password"):
        users.loc[users["username"]==username,"password"] = new_pwd
        save_users(users)
        st.success("Password updated successfully!")

# --- Login Page ---
def main():
    st.set_page_config(page_title="Superior University AI Department", layout="wide")
    st.markdown("<h1 style='color:purple;'>Superior University AI Department Portal</h1>", unsafe_allow_html=True)
    init_csv()
    users = load_users()

    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        user = users[(users["username"]==username) & (users["password"]==password)]
        if not user.empty:
            role = user.iloc[0]["role"]
            st.session_state["logged_in_user"] = username
            if role == "admin":
                admin_dashboard(username)
            else:
                student_dashboard(username)
        else:
            st.error("Invalid credentials or user not registered.")

if __name__ == "__main__":
    main()

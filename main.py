import streamlit as st
import pandas as pd
import os

# ---------- Data Storage ----------
DATA_FILE = "students_data.csv"
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["roll_no", "name", "semester", "password"])
    df.to_csv(DATA_FILE, index=False)

# ---------- Functions ----------
def load_students():
    return pd.read_csv(DATA_FILE)

def save_students(df):
    df.to_csv(DATA_FILE, index=False)

# ---------- Admin Section ----------
def admin_dashboard():
    st.title("🎓 Superior University - AI Department Portal (Admin)")
    st.sidebar.header("Admin Options")

    menu = st.sidebar.radio("Select Option", [
        "Add Student",
        "View Students",
        "Add Course",
        "Mark Attendance",
        "Add Results",
        "Announcements",
        "View Feedback"
    ])

    if menu == "Add Student":
        st.subheader("Add New Student")
        roll = st.text_input("Enter Roll No", key="add_roll")
        name = st.text_input("Enter Name", key="add_name")
        sem = st.selectbox("Select Semester", [f"Semester {i}" for i in range(1, 9)], key="add_sem")
        password = st.text_input("Set Password", type="password", key="add_pass")

        if st.button("Save Student"):
            df = load_students()
            if roll in df["roll_no"].values:
                st.warning("⚠️ Student with this Roll No already exists.")
            else:
                new_row = pd.DataFrame([[roll, name, sem, password]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True)
                save_students(df)
                st.success(f"✅ Student '{name}' added successfully!")

    elif menu == "View Students":
        st.subheader("All Students")
        df = load_students()
        st.dataframe(df)

    elif menu == "Add Course":
        st.subheader("Add Courses (Per Semester)")
        sem = st.selectbox("Select Semester", [f"Semester {i}" for i in range(1, 9)], key="course_sem")
        course_name = st.text_input("Course Name", key="course_name")
        if st.button("Add Course"):
            st.success(f"✅ Course '{course_name}' added for {sem}!")

    elif menu == "Mark Attendance":
        st.subheader("Mark Attendance (AI Department)")
        df = load_students()
        sem = st.selectbox("Select Semester", sorted(df["semester"].unique()), key="att_sem")
        filtered = df[df["semester"] == sem]
        for _, row in filtered.iterrows():
            st.checkbox(f"{row['roll_no']} - {row['name']}", key=f"att_{row['roll_no']}")
        st.button("Submit Attendance")

    elif menu == "Add Results":
        st.subheader("Add Results for Students")
        df = load_students()
        roll = st.text_input("Enter Roll No", key="res_roll")
        marks = st.number_input("Enter Marks", min_value=0, max_value=100, key="res_marks")
        if st.button("Save Result"):
            st.success(f"✅ Marks for {roll} saved successfully!")

    elif menu == "Announcements":
        st.subheader("Make an Announcement")
        msg = st.text_area("Write Announcement")
        if st.button("Post Announcement"):
            st.success("✅ Announcement posted!")

    elif menu == "View Feedback":
        st.subheader("Student Feedbacks")
        st.info("📬 No feedback yet.")


# ---------- Student Section ----------
def student_dashboard(student):
    st.title("🎓 Superior University - AI Department (Student Dashboard)")
    st.write(f"Welcome, **{student['name']} ({student['roll_no']})** — {student['semester']}")

    tabs = ["Attendance", "Results", "Courses", "Announcements", "Feedback"]
    choice = st.sidebar.radio("Select Option", tabs, key="stud_opt")

    if choice == "Attendance":
        st.subheader("📋 Attendance Record")
        st.info("Your attendance record will appear here.")

    elif choice == "Results":
        st.subheader("📘 Result Details")
        st.info("Your results will be shown here.")

    elif choice == "Courses":
        st.subheader("📚 Registered Courses")
        st.info("Courses added by teachers/admin will appear here.")

    elif choice == "Announcements":
        st.subheader("📢 Latest Announcements")
        st.info("Stay tuned for new announcements.")

    elif choice == "Feedback":
        st.subheader("📝 Give Feedback")
        fb = st.text_area("Enter your feedback")
        if st.button("Submit Feedback"):
            st.success("✅ Feedback submitted successfully!")

# ---------- Login ----------
def main():
    st.markdown(
        """
        <h1 style='text-align:center; color:#6a0dad;'>Superior University - AI Department Portal</h1>
        """, unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.session_state.user = None

    if not st.session_state.logged_in:
        st.sidebar.subheader("🔐 Login")
        user_type = st.sidebar.selectbox("Login as", ["Admin", "Student"])
        username = st.sidebar.text_input("Username / Roll No", key="login_user")
        password = st.sidebar.text_input("Password", type="password", key="login_pass")

        if st.sidebar.button("Login"):
            if user_type == "Admin" and username == "admin" and password == "123":
                st.session_state.logged_in = True
                st.session_state.user_type = "Admin"
                st.success("✅ Admin Login Successful!")
            elif user_type == "Student":
                df = load_students()
                user = df[(df["roll_no"] == username) & (df["password"] == password)]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_type = "Student"
                    st.session_state.user = user.iloc[0].to_dict()
                    st.success("✅ Student Login Successful!")
                else:
                    st.error("❌ Invalid Roll No or Password.")
            else:
                st.error("❌ Invalid Credentials.")
    else:
        if st.session_state.user_type == "Admin":
            admin_dashboard()
        elif st.session_state.user_type == "Student":
            student_dashboard(st.session_state.user)

        st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())


# ---------- Run App ----------
if __name__ == "__main__":
    main()

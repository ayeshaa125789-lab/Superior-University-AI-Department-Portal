import streamlit as st
import pandas as pd
import os

# --- SETTINGS ---
st.set_page_config(page_title="Superior University AI Department", layout="wide")

# --- COLORS ---
PRIMARY_COLOR = "#4B0082"  # purple
BG_COLOR = "#000000"       # black
st.markdown(f"""
    <style>
    .main {{ background-color: {BG_COLOR}; color: white; }}
    .stButton>button {{ background-color: {PRIMARY_COLOR}; color: white; }}
    .stTextInput>div>div>input {{ background-color: #1c1c1c; color: white; }}
    </style>
""", unsafe_allow_html=True)

# --- DATA FILES ---
USERS_FILE = "users.csv"      # stores admin & student data
RESULTS_FILE = "results.csv"
ATTEND_FILE = "attendance.csv"

# --- UTILITY FUNCTIONS ---
def load_data(file, cols):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame(columns=cols)

def save_data(df, file):
    df.to_csv(file, index=False)

# --- INITIAL DATA ---
users = load_data(USERS_FILE, ["username", "roll_no", "password", "role"])
results = load_data(RESULTS_FILE, ["roll_no", "course", "marks"])
attendance = load_data(ATTEND_FILE, ["roll_no", "course", "attendance"])

# --- LOGIN ---
st.title("Superior University AI Department Portal")

if "login_success" not in st.session_state:
    st.session_state.login_success = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.login_success:
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login", key="login_btn"):
        user_row = users[(users["username"]==username) & (users["password"]==password)]
        if not user_row.empty:
            st.session_state.login_success = True
            st.session_state.current_user = user_row.iloc[0]
            st.experimental_rerun()  # refresh to show dashboard
        else:
            st.error("Invalid credentials or user not registered.")

# --- DASHBOARD ---
if st.session_state.login_success:
    user = st.session_state.current_user
    st.markdown(f"<h2>Welcome, {user['username']} ({user['role']})</h2>", unsafe_allow_html=True)

    if user["role"] == "admin":
        st.subheader("Admin Dashboard")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Add Student", key="add_student"):
                with st.form("add_student_form"):
                    name = st.text_input("Student Name", key="as_name")
                    roll = st.text_input("Roll Number", key="as_roll")
                    pwd = st.text_input("Password", type="password", key="as_pwd")
                    semester = st.selectbox("Semester", [1,2,3,4,5,6,7,8], key="as_sem")
                    submit = st.form_submit_button("Add Student")
                    if submit:
                        if ((users["username"]==name) & (users["roll_no"]==roll)).any():
                            st.error("Student already exists!")
                        else:
                            users.loc[len(users)] = [name, roll, pwd, "student"]
                            save_data(users, USERS_FILE)
                            st.success(f"Student {name} added successfully!")

            if st.button("View Students", key="view_students"):
                st.dataframe(users[users["role"]=="student"])

        with col2:
            if st.button("Add Course", key="add_course"):
                st.info("Course feature coming soon.")

            if st.button("View Courses", key="view_courses"):
                st.info("Course feature coming soon.")

        if st.button("Mark Attendance", key="mark_attendance"):
            st.info("Attendance feature coming soon.")

        if st.button("Add Results", key="add_results"):
            st.info("Results feature coming soon.")

        if st.button("View Results", key="view_results"):
            st.info("Results feature coming soon.")

    else:
        st.subheader("Student Dashboard")
        st.markdown(f"**Roll Number:** {user['roll_no']}")

        # Show results
        st.markdown("### Results")
        my_results = results[results["roll_no"]==user["roll_no"]]
        if my_results.empty:
            st.info("No results yet.")
        else:
            st.dataframe(my_results)

        # Show attendance
        st.markdown("### Attendance")
        my_attend = attendance[attendance["roll_no"]==user["roll_no"]]
        if my_attend.empty:
            st.info("No attendance recorded yet.")
        else:
            st.dataframe(my_attend)

        # Change password
        st.markdown("### Change Password")
        new_pwd = st.text_input("New Password", type="password", key="change_pwd")
        if st.button("Update Password", key="update_pwd"):
            users.loc[users["username"]==user["username"], "password"] = new_pwd
            save_data(users, USERS_FILE)
            st.success("Password updated successfully!")

    if st.button("Logout", key="logout"):
        st.session_state.login_success = False
        st.session_state.current_user = None
        st.experimental_rerun()

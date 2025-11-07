import streamlit as st
import json
import os

# ---------- Helper Functions ----------

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {"admin": {"password": "admin123", "role": "admin"}, "students": {}}

def save_users(data):
    with open("users.json", "w") as file:
        json.dump(data, file, indent=4)

# ---------- Load Users ----------
users = load_users()

# ---------- Login Section ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

if not st.session_state.logged_in:
    st.title("🎓 Superior University AI Department Portal")

    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == users["admin"]["password"]:
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.session_state.username = username
            st.success("✅ Logged in as Admin!")
            st.rerun()
        elif username in users["students"] and password == users["students"][username]["password"]:
            st.session_state.logged_in = True
            st.session_state.role = "student"
            st.session_state.username = username
            st.success(f"✅ Welcome {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ---------- Admin Dashboard ----------
elif st.session_state.logged_in and st.session_state.role == "admin":
    st.title("👨‍💼 Admin Dashboard")

    menu = st.sidebar.selectbox("Select Action", ["Add Student", "View All Students", "Logout"])

    if menu == "Add Student":
        st.subheader("Add New Student")
        new_username = st.text_input("Username")
        new_rollno = st.text_input("Roll Number")
        new_password = st.text_input("Password", type="password")

        if st.button("Add Student"):
            if new_username and new_rollno and new_password:
                if new_username not in users["students"]:
                    users["students"][new_username] = {
                        "rollno": new_rollno,
                        "password": new_password
                    }
                    save_users(users)
                    st.success(f"🎉 Student '{new_username}' added successfully!")
                else:
                    st.warning("⚠️ Username already exists!")
            else:
                st.warning("Please fill in all fields!")

    elif menu == "View All Students":
        st.subheader("📋 Registered Students")
        if users["students"]:
            for uname, info in users["students"].items():
                st.write(f"**Name:** {uname} | **Roll No:** {info['rollno']}")
        else:
            st.info("No students added yet.")

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

# ---------- Student Dashboard ----------
elif st.session_state.logged_in and st.session_state.role == "student":
    st.title("🎓 Student Dashboard")
    st.write(f"Welcome, **{st.session_state.username}**!")

    st.subheader("Change Password")
    new_pass = st.text_input("Enter New Password", type="password")
    if st.button("Update Password"):
        users["students"][st.session_state.username]["password"] = new_pass
        save_users(users)
        st.success("🔐 Password updated successfully!")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

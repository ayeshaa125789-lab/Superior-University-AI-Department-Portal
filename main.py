import streamlit as st
import pandas as pd
import os
import hashlib

# ------------------ FILE PATHS ------------------
USER_FILE = "users.csv"
ASSIGNMENT_FILE = "assignments.csv"
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ------------------ HELPER FUNCTIONS ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        df = pd.DataFrame(columns=["username", "password", "role"])
        df.to_csv(USER_FILE, index=False)
        return df

def save_users(df):
    df.to_csv(USER_FILE, index=False)

def authenticate(username, password):
    users = load_users()
    hashed_pw = hash_password(password)
    user = users[(users['username'] == username) & (users['password'] == hashed_pw)]
    return not user.empty

def get_role(username):
    users = load_users()
    return users[users['username'] == username]['role'].values[0]

def add_user(username, password, role):
    users = load_users()
    if username in users['username'].values:
        return False
    users = pd.concat([users, pd.DataFrame({"username":[username], "password":[hash_password(password)], "role":[role]})], ignore_index=True)
    save_users(users)
    return True

def delete_user(username):
    users = load_users()
    if username in users['username'].values:
        users = users[users['username'] != username]
        save_users(users)
        return True
    return False

def update_password(username, new_password):
    users = load_users()
    if username in users['username'].values:
        users.loc[users['username'] == username, 'password'] = hash_password(new_password)
        save_users(users)
        return True
    return False

# ------------------ ASSIGNMENT FUNCTIONS ------------------
def load_assignments():
    if os.path.exists(ASSIGNMENT_FILE):
        return pd.read_csv(ASSIGNMENT_FILE)
    else:
        df = pd.DataFrame(columns=["username","filename"])
        df.to_csv(ASSIGNMENT_FILE, index=False)
        return df

def save_assignments(df):
    df.to_csv(ASSIGNMENT_FILE, index=False)

def upload_assignment(username, file):
    save_path = os.path.join(UPLOAD_FOLDER, f"{username}_{file.name}")
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    df = load_assignments()
    df = pd.concat([df, pd.DataFrame({"username":[username],"filename":[file.name]})], ignore_index=True)
    save_assignments(df)
    return True

# ------------------ STREAMLIT APP ------------------
st.set_page_config(page_title="AI Department Portal", page_icon="🖥️", layout="wide")
st.title("🖥️ AI Department Portal")

# --- SESSION STATE ---
if 'login' not in st.session_state:
    st.session_state['login'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# --- LOGIN ---
if not st.session_state['login']:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state['login'] = True
            st.session_state['username'] = username
            st.session_state['role'] = get_role(username)
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid username or password!")

# --- LOGOUT ---
if st.session_state['login']:
    st.sidebar.write(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")
    if st.sidebar.button("Logout"):
        st.session_state['login'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.experimental_rerun()

# --- ADMIN DASHBOARD ---
if st.session_state['login'] and st.session_state['role'] == 'admin':
    st.subheader("Admin Dashboard")
    users_df = load_users()
    
    tab1, tab2, tab3 = st.tabs(["View Users", "Add User", "Delete User"])
    
    # --- View Users ---
    with tab1:
        st.write(users_df)
    
    # --- Add User ---
    with tab2:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        role_option = st.selectbox("Role", ["student", "teacher", "admin"])
        if st.button("Add User"):
            if add_user(new_username, new_password, role_option):
                st.success(f"User '{new_username}' added successfully!")
            else:
                st.error("Username already exists!")
    
    # --- Delete User ---
    with tab3:
        del_username = st.selectbox("Select User to Delete", users_df['username'].tolist())
        if st.button("Delete User"):
            if del_username == st.session_state['username']:
                st.error("You cannot delete yourself!")
            elif delete_user(del_username):
                st.success(f"User '{del_username}' deleted successfully!")
            else:
                st.error("Error deleting user!")

# --- STUDENT/TEACHER DASHBOARD ---
if st.session_state['login'] and st.session_state['role'] in ['student', 'teacher']:
    st.subheader(f"{st.session_state['role'].capitalize()} Dashboard")
    st.write(f"Welcome, {st.session_state['username']}!")
    
    tab1, tab2, tab3 = st.tabs(["Profile", "Change Password", "Assignments"])
    
    # --- Profile ---
    with tab1:
        st.write("Username:", st.session_state['username'])
        st.write("Role:", st.session_state['role'])
    
    # --- Change Password ---
    with tab2:
        old_pw = st.text_input("Old Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            if authenticate(st.session_state['username'], old_pw):
                update_password(st.session_state['username'], new_pw)
                st.success("Password updated successfully!")
            else:
                st.error("Old password is incorrect!")
    
    # --- Assignments ---
    with tab3:
        st.subheader("Upload Assignment")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf","docx","txt"])
        if st.button("Upload"):
            if uploaded_file:
                upload_assignment(st.session_state['username'], uploaded_file)
                st.success(f"{uploaded_file.name} uploaded successfully!")
            else:
                st.error("Please select a file to upload.")
        
        st.subheader("View All Assignments (Teacher Only)")
        if st.session_state['role'] == 'teacher':
            assignments_df = load_assignments()
            if not assignments_df.empty:
                st.write(assignments_df)
            else:
                st.info("No assignments uploaded yet.")

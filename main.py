import streamlit as st
import pandas as pd
import gspread # Google Sheets library
from datetime import datetime
import json
import time

# --- Configuration & Secrets ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "supersecretpassword123" 
STUDENT_DEFAULT_PASSWORD = "password" 

# Secrets se URLs load karein (Ensure these are set in Streamlit Cloud Secrets)
try:
    STUDENTS_SHEET_URL = st.secrets["students_sheet_url"]
    COURSES_SHEET_URL = st.secrets["courses_sheet_url"]
    NEWS_SHEET_URL = st.secrets["news_sheet_url"]
    FEEDBACK_SHEET_URL = st.secrets["feedback_sheet_url"]
    
    # Check if credentials are available
    if "gcp_service_account" not in st.secrets:
        st.error("GCP Service Account credentials not found in Streamlit Secrets.")
        st.stop()
        
except KeyError as e:
    st.error(f"Configuration error: Missing secret key {e}. Please configure Streamlit Secrets.")
    st.stop()
except Exception as e:
    st.error(f"Initialization error: {e}")
    st.stop()

# --- Connection and Data Management Functions (Permanent Storage) ---

@st.cache_resource(ttl=3600) # Cache connection for 1 hour
def connect_to_sheets():
    """Establishes connection to Google Sheets using service account credentials."""
    try:
        credentials = st.secrets["gcp_service_account"]
        # Use gspread to authorize with the service account JSON
        gc = gspread.service_account_from_dict(credentials)
        return gc
    except Exception as e:
        st.error(f"Error connecting to Google Sheets. Check your secrets.toml: {e}")
        return None

def load_data(sheet_url):
    """Loads data from a specified Google Sheet as a list of dictionaries."""
    gc = connect_to_sheets()
    if gc is None: return []

    try:
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.sheet1
        data = worksheet.get_all_records()
        return data
    except gspread.exceptions.APIError as e:
        st.error(f"Google Sheets API Error (Check sharing permissions for the service account email): {e}")
        return []
    except Exception as e:
        st.error(f"Could not load data from sheet {sheet_url}: {e}")
        return []

def save_data(sheet_url, data, headers):
    """Saves entire data back to the Google Sheet (Clears and replaces)."""
    gc = connect_to_sheets()
    if gc is None: return False
    
    # Convert list of dicts to list of lists (Google Sheets format)
    rows_to_save = [headers] + [list(d.get(h, '') for h in headers) for d in data]

    try:
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.sheet1
        
        # Clear existing content before writing new data
        worksheet.clear() 
        
        # Write all rows
        worksheet.append_rows(rows_to_save)
        
        # Invalidate the cache to ensure next load gets fresh data
        load_data.clear() 
        return True
    except Exception as e:
        st.error(f"Could not save data to sheet {sheet_url}: {e}")
        return False

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

# --- Utility & Styling ---
def logout():
    keys_to_delete = ['logged_in', 'role', 'username', 'page']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['page'] = 'login'
    time.sleep(0.5) # Give time for session state update before rerun
    st.experimental_rerun()

def get_sheet_data_and_headers(sheet_url):
    data = load_data(sheet_url)
    if data:
        # Headers are keys of the first dictionary
        headers = list(data[0].keys())
    elif sheet_url == STUDENTS_SHEET_URL:
        headers = ["username", "password", "name", "date_joined"]
    elif sheet_url == COURSES_SHEET_URL:
        headers = ["title", "code", "description", "date_added"]
    elif sheet_url == NEWS_SHEET_URL:
        headers = ["id", "title", "content", "date", "posted_by"]
    elif sheet_url == FEEDBACK_SHEET_URL:
        headers = ["id", "student_username", "title", "message", "date", "status"]
    else:
        headers = []
        
    return data, headers

# Custom Styling (Purple Modern Theme)
st.markdown(
    """
    <style>
    .stApp { background-color: #f4f3ff; color: #333333; }
    .css-1d391kg, .css-1dp5q0n { background-color: #7B2CBF; color: white; }
    h1, h2, h3 { color: #5A189A; }
    .stButton>button { background-color: #7B2CBF; color: white !important; border-radius: 8px; font-weight: bold; transition: background-color 0.3s; }
    .stButton>button:hover { background-color: #5A189A; }
    .stAlert, .stDataFrame, .stTable { border: 1px solid #7B2CBF; border-radius: 10px; padding: 10px; box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1); margin-bottom: 15px; }
    .dashboard-image { border-radius: 15px; width: 100%; max-height: 250px; object-fit: cover; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Feature Implementation ---

## 1. Authentication
def login_page():
    st.title("🔑 Portal Login")
    
    students, _ = get_sheet_data_and_headers(STUDENTS_SHEET_URL)

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            # Check Admin login
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'admin'
                st.session_state['username'] = username
                st.success("Admin login successful!")
                st.session_state['page'] = 'dashboard'
                st.experimental_rerun()
                return

            # Check Student login
            student_match = next((s for s in students if s.get('username') == username and s.get('password') == password), None)
            
            if student_match:
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'student'
                st.session_state['username'] = username
                st.success("Student login successful!")
                st.session_state['page'] = 'dashboard'
                st.experimental_rerun()
                return
            
            st.error("Invalid username or password.")

def signup_page():
    st.title("📝 Student Signup")
    students, student_headers = get_sheet_data_and_headers(STUDENTS_SHEET_URL)

    with st.form("signup_form"):
        new_username = st.text_input("New Student Username (e.g., roll_123)")
        # Admin must provide the initial default password to the student
        initial_password = st.text_input(f"Admin Provided Password (Must be: {STUDENT_DEFAULT_PASSWORD})", type="password")
        
        submitted = st.form_submit_button("Sign Up")

        if submitted:
            if not new_username or not initial_password:
                st.error("Please fill in all fields.")
            elif initial_password != STUDENT_DEFAULT_PASSWORD:
                st.error(f"Initial password must be '{STUDENT_DEFAULT_PASSWORD}'. Please ask Admin.")
            elif any(s.get('username') == new_username for s in students):
                st.error("Username already exists. Please choose another one.")
            else:
                students.append({
                    "username": new_username,
                    "password": initial_password, 
                    "name": "New Student", 
                    "date_joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                if save_data(STUDENTS_SHEET_URL, students, student_headers):
                    st.success(f"Student '{new_username}' registered successfully! You can now log in.")
                else:
                    st.error("Failed to save student data.")


## 2. Dashboard
def display_dashboard():
    st.markdown("---")
    st.markdown(f"## 👋 Welcome back, **{st.session_state['username'].title()}**!")
    st.markdown(f"### Role: {st.session_state['role'].upper()}")
    
    # Placeholder for a purple abstract image
    st.markdown('<img src="https://images.unsplash.com/photo-1579227114347-15d08fc37aa7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1587&q=80" class="dashboard-image" alt="Abstract Purple Dashboard Image">', unsafe_allow_html=True)
    st.markdown("---")
    
    if st.session_state['role'] == 'admin':
        admin_dashboard()
    elif st.session_state['role'] == 'student':
        student_dashboard()

def admin_dashboard():
    students, _ = get_sheet_data_and_headers(STUDENTS_SHEET_URL)
    courses, _ = get_sheet_data_and_headers(COURSES_SHEET_URL)
    news, _ = get_sheet_data_and_headers(NEWS_SHEET_URL)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students", len(students))
    col2.metric("Total Courses", len(courses))
    col3.metric("Total News Posts", len(news))
    
    st.subheader("📰 Latest News Summary")
    latest_news = news[-1]['title'] if news else "No news posted."
    st.info(f"**Latest Post:** {latest_news}")
    
    if st.button("Go to Admin Panel", key="admin_panel_btn"):
        st.session_state['page'] = 'admin_panel'
        st.experimental_rerun()

def student_dashboard():
    news, _ = get_sheet_data_and_headers(NEWS_SHEET_URL)
    
    st.subheader("📢 Portal News Feed")
    if news:
        # Ensure 'date' is present and valid for sorting
        news_valid = [item for item in news if item.get('date')]
        try:
            # Sort by date descending
            news_valid.sort(key=lambda x: datetime.strptime(str(x['date']), "%Y-%m-%d %H:%M:%S"), reverse=True)
        except:
            # Fallback if date format is inconsistent
            pass
        
        latest_news = news_valid[:3] # Show last 3 news items
        for item in latest_news:
            st.info(f"**{item.get('title', 'No Title')}** - ({item.get('date', 'Unknown Date').split()[0]})\n\n{item.get('content', 'No Content')[:100]}...") # Truncate content
    else:
        st.info("No news updates at the moment.")
    
    if st.button("Submit Feedback", key="submit_feedback_btn"):
        st.session_state['page'] = 'feedback_submit'
        st.experimental_rerun()

## 3. Course Management (Admin Only)
def course_management():
    st.title("📚 Course Management")
    courses, course_headers = get_sheet_data_and_headers(COURSES_SHEET_URL)

    st.subheader("➕ Add New Course")
    with st.form("add_course_form"):
        title = st.text_input("Course Title")
        code = st.text_input("Course Code (e.g., CS101)").upper()
        description = st.text_area("Description")
        submitted = st.form_submit_button("Add Course")
        
        if submitted:
            if not title or not code:
                st.error("Title and Code are required.")
            elif any(c.get('code') == code for c in courses):
                st.error(f"Course code {code} already exists.")
            else:
                courses.append({
                    "title": title,
                    "code": code,
                    "description": description,
                    "date_added": datetime.now().strftime("%Y-%m-%d")
                })
                if save_data(COURSES_SHEET_URL, courses, course_headers):
                    st.success(f"Course '{title}' added successfully!")
                st.experimental_rerun()

    st.subheader("❌ Existing Courses (Delete)")
    if courses:
        course_df = pd.DataFrame(courses)
        st.dataframe(course_df[['code', 'title', 'description', 'date_added']])
        
        course_to_delete = st.selectbox("Select Course Code to Delete", [""] + [c['code'] for c in courses if c.get('code')])
        if st.button("Delete Selected Course", key="delete_course_btn") and course_to_delete:
            new_courses = [c for c in courses if c.get('code') != course_to_delete]
            if save_data(COURSES_SHEET_URL, new_courses, course_headers):
                st.success(f"Course '{course_to_delete}' deleted.")
            st.experimental_rerun()
    else:
        st.info("No courses currently available.")

## 4. News Management (Admin adds, Student views)
def news_management():
    news_items, news_headers = get_sheet_data_and_headers(NEWS_SHEET_URL)

    if st.session_state['role'] == 'admin':
        st.title("📰 News/Announcement Management")
        st.subheader("➕ Add New News Item")
        
        # Determine next ID based on existing data
        max_id = max([int(item.get('id', 0)) for item in news_items]) if news_items else 0
        
        with st.form("add_news_form"):
            title = st.text_input("News Title")
            content = st.text_area("Content")
            submitted = st.form_submit_button("Post News")
            
            if submitted:
                if not title or not content:
                    st.error("Title and Content are required.")
                else:
                    news_items.append({
                        "id": max_id + 1,
                        "title": title,
                        "content": content,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "posted_by": st.session_state['username']
                    })
                    if save_data(NEWS_SHEET_URL, news_items, news_headers):
                        st.success(f"News '{title}' posted successfully!")
                    st.experimental_rerun()

    else: # Student View
        st.title("📰 Latest News & Announcements")

    st.subheader("📢 All News Feed")
    if news_items:
        # Ensure 'date' is present and valid for sorting
        news_valid = [item for item in news_items if item.get('date')]
        try:
            # Sort by date descending
            news_valid.sort(key=lambda x: datetime.strptime(str(x['date']), "%Y-%m-%d %H:%M:%S"), reverse=True)
        except:
            pass # Use unsorted list if date format is inconsistent
        
        for item in news_valid:
            st.markdown(f"**{item.get('title', 'No Title')}** - *{item.get('date', 'Unknown Date')}*")
            st.write(item.get('content', ''))
            st.markdown("---")
    else:
        st.info("No news posted yet.")

## 5. Feedback
def feedback_submit():
    st.title("💬 Submit Feedback")
    feedback, feedback_headers = get_sheet_data_and_headers(FEEDBACK_SHEET_URL)
    
    # Determine next ID
    max_id = max([int(item.get('id', 0)) for item in feedback]) if feedback else 0

    with st.form("feedback_form"):
        title = st.text_input("Feedback Title")
        message = st.text_area("Your Message")
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            if not title or not message:
                st.error("Please fill in both fields.")
            else:
                feedback.append({
                    "id": max_id + 1,
                    "student_username": st.session_state['username'],
                    "title": title,
                    "message": message,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "New"
                })
                if save_data(FEEDBACK_SHEET_URL, feedback, feedback_headers):
                    st.success("Thank you! Your feedback has been submitted to the Admin.")
                st.experimental_rerun()

def feedback_view():
    st.title("📥 View Student Feedback")
    feedback, feedback_headers = get_sheet_data_and_headers(FEEDBACK_SHEET_URL)
    
    if feedback:
        df = pd.DataFrame(feedback)
        # Display feedback sorted by status (New first) and then date
        df['status_sort'] = df['status'].apply(lambda x: 0 if x == 'New' else 1)
        df = df.sort_values(by=['status_sort', 'date'], ascending=[True, False]).drop(columns=['status_sort'])
        
        st.dataframe(df[['id', 'date', 'student_username', 'title', 'message', 'status']])
        
        st.subheader("Mark Feedback as Read")
        feedback_ids = [str(f['id']) for f in feedback if f.get('status') == 'New']
        id_to_mark = st.selectbox("Select ID to Mark as Read", [""] + feedback_ids)
        
        if st.button("Mark as Read") and id_to_mark:
            feedback_id = int(id_to_mark)
            found = False
            for f in feedback:
                if f.get('id') == feedback_id:
                    f['status'] = 'Read'
                    found = True
                    break
            if found:
                if save_data(FEEDBACK_SHEET_URL, feedback, feedback_headers):
                    st.success(f"Feedback ID {id_to_mark} marked as Read.")
                st.experimental_rerun()
            else:
                st.error("Feedback ID not found.")
    else:
        st.info("No feedback submissions yet.")

## 6. Admin Panel (Delete Students)
def admin_panel():
    st.title("⚙️ Admin Panel")
    
    # Quick Links
    st.header("Admin Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📚 Manage Courses", use_container_width=True):
            st.session_state['page'] = 'course_management'
            st.experimental_rerun()
    with col2:
        if st.button("📰 Manage News", use_container_width=True):
            st.session_state['page'] = 'news_management'
            st.experimental_rerun()
    with col3:
        if st.button("📥 View Feedback", use_container_width=True):
            st.session_state['page'] = 'feedback_view'
            st.experimental_rerun()
    
    st.markdown("---")
    
    st.subheader("❌ Delete Students")
    students, student_headers = get_sheet_data_and_headers(STUDENTS_SHEET_URL)
    
    if students:
        student_df = pd.DataFrame(students)
        st.dataframe(student_df[['username', 'name', 'date_joined']])
        
        student_usernames = [s['username'] for s in students if s.get('username') and s['username'] != ADMIN_USERNAME]
        student_to_delete = st.selectbox("Select Student Username to Delete", [""] + student_usernames)
        
        if st.button("Delete Selected Student", key="delete_student_btn") and student_to_delete:
            new_students = [s for s in students if s.get('username') != student_to_delete]
            
            if save_data(STUDENTS_SHEET_URL, new_students, student_headers):
                st.success(f"Student '{student_to_delete}' deleted successfully.")
            st.experimental_rerun()
    else:
        st.info("No students registered yet.")

# --- Main Application Logic ---
def main_app():
    
    st.sidebar.title("📚 Portal Navigation")
    
    # --- Navigation Handling (Logged In vs. Logged Out) ---
    if st.session_state['logged_in']:
        # Logged-in Navigation
        st.sidebar.button("🏠 Dashboard", on_click=lambda: st.session_state.update(page='dashboard'), use_container_width=True)
        
        if st.session_state['role'] == 'admin':
            st.sidebar.markdown("### Admin Controls")
            st.sidebar.button("⚙️ Admin Panel", on_click=lambda: st.session_state.update(page='admin_panel'), use_container_width=True)
            st.sidebar.button("📚 Course Management", on_click=lambda: st.session_state.update(page='course_management'), use_container_width=True)
            st.sidebar.button("📰 News Management", on_click=lambda: st.session_state.update(page='news_management'), use_container_width=True)
            st.sidebar.button("📥 View Feedback", on_click=lambda: st.session_state.update(page='feedback_view'), use_container_width=True)
            
        elif st.session_state['role'] == 'student':
            st.sidebar.markdown("### Student Access")
            st.sidebar.button("📰 View News", on_click=lambda: st.session_state.update(page='news_management'), use_container_width=True)
            st.sidebar.button("💬 Submit Feedback", on_click=lambda: st.session_state.update(page='feedback_submit'), use_container_width=True)
        
        st.sidebar.markdown("---")
        st.sidebar.button("🚪 Logout", on_click=logout, use_container_width=True)
        
        # --- Page Router ---
        if st.session_state['page'] == 'dashboard':
            display_dashboard()
        elif st.session_state['page'] == 'admin_panel' and st.session_state['role'] == 'admin':
            admin_panel()
        elif st.session_state['page'] == 'course_management' and st.session_state['role'] == 'admin':
            course_management()
        elif st.session_state['page'] == 'news_management':
            news_management() 
        elif st.session_state['page'] == 'feedback_submit' and st.session_state['role'] == 'student':
            feedback_submit()
        elif st.session_state['page'] == 'feedback_view' and st.session_state['role'] == 'admin':
            feedback_view()
        else:
            # Fallback for unauthorized/missing page
            st.error("403: Access Denied. Redirecting to Dashboard.")
            st.session_state['page'] = 'dashboard'
            st.experimental_rerun()
            
    else:
        # Not Logged-in Navigation (Login/Signup options)
        st.sidebar.button("🔑 Login", on_click=lambda: st.session_state.update(page='login'), use_container_width=True)
        st.sidebar.button("📝 Student Signup", on_click=lambda: st.session_state.update(page='signup'), use_container_width=True)

        if st.session_state['page'] == 'login': 
            login_page()
        elif st.session_state['page'] == 'signup':
            signup_page()
        elif st.session_state['page'] == 'dashboard':
            login_page() # Redirect dashboard view to login if not logged in

if __name__ == '__main__':
    main_app()

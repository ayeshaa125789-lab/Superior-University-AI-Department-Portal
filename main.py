import streamlit as st
import pandas as pd
import os

# -------------------- FILES --------------------
student_file = "students.csv"
course_file = "courses.csv"
feedback_file = "feedback.csv"
news_file = "news.csv"
users_file = "users.csv"

# -------------------- INITIAL SETUP --------------------
for file in [student_file, course_file, feedback_file, news_file, users_file]:
    if not os.path.exists(file):
        if "student" in file:
            pd.DataFrame(columns=["Name", "Roll No", "Semester", "Email"]).to_csv(file, index=False)
        elif "course" in file:
            pd.DataFrame(columns=["Course Name", "Code", "Instructor"]).to_csv(file, index=False)
        elif "feedback" in file:
            pd.DataFrame(columns=["Name", "Message", "Rating"]).to_csv(file, index=False)
        elif "news" in file:
            pd.DataFrame(columns=["Title", "Details"]).to_csv(file, index=False)
        elif "users" in file:
            pd.DataFrame([
                ["admin", "1234", "Admin"],
                ["student", "1234", "Student"]
            ], columns=["Username", "Password", "Role"]).to_csv(file, index=False)

# -------------------- PAGE SETUP --------------------
st.set_page_config(page_title="AI Department Portal", layout="wide")
st.markdown("""
    <style>
    body { background-color: #f8f5ff; }
    .stApp { background-color: #f3eaff; }
    .main-title {
        text-align: center;
        color: #6A0DAD;
        font-size: 38px;
        font-weight: 700;
    }
    .section-title {
        color: #6A0DAD;
        font-size: 24px;
        font-weight: bold;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🎓 Superior University - AI Department Portal</div>", unsafe_allow_html=True)

# -------------------- LOGIN SYSTEM --------------------
st.sidebar.title("🔐 Login Panel")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

users = pd.read_csv(users_file)

if st.sidebar.button("Login"):
    user = users[(users["Username"] == username) & (users["Password"] == password)]
    if not user.empty:
        role = user.iloc[0]["Role"]
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state["role"] = role
        st.sidebar.success(f"✅ Logged in as {role}")
    else:
        st.sidebar.error("❌ Invalid username or password")

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Please log in from the sidebar to continue.")
    st.stop()

# -------------------- MENU BASED ON ROLE --------------------
if st.session_state["role"] == "Admin":
    menu = st.sidebar.radio(
        "Admin Menu",
        ["🏠 Home", "👨‍🎓 Add Student", "📘 Add Course", "📰 Add News", "📊 View Data"]
    )

else:
    menu = st.sidebar.radio(
        "Student Menu",
        ["🏠 Home", "📝 Feedback", "📰 View News"]
    )

# -------------------- HOME --------------------
if menu == "🏠 Home":
    st.markdown("<div class='section-title'>Welcome!</div>", unsafe_allow_html=True)
    if st.session_state["role"] == "Admin":
        st.write("Hello Admin! Manage your department data efficiently.")
    else:
        st.write("Welcome Student! Check news or share your feedback.")
    st.image("https://img.freepik.com/free-vector/artificial-intelligence-illustration_23-2149232800.jpg", use_container_width=True)

# -------------------- ADD STUDENT --------------------
if menu == "👨‍🎓 Add Student" and st.session_state["role"] == "Admin":
    st.markdown("<div class='section-title'>Add New Student</div>", unsafe_allow_html=True)
    name = st.text_input("Name")
    roll = st.text_input("Roll No")
    sem = st.selectbox("Semester", ["1st", "3rd"])
    email = st.text_input("Email")

    if st.button("Add Student"):
        if name and roll and email:
            df = pd.read_csv(student_file)
            df.loc[len(df)] = [name, roll, sem, email]
            df.to_csv(student_file, index=False)
            st.success("✅ Student added successfully!")
        else:
            st.warning("⚠️ Please fill all fields!")

# -------------------- ADD COURSE --------------------
if menu == "📘 Add Course" and st.session_state["role"] == "Admin":
    st.markdown("<div class='section-title'>Add New Course</div>", unsafe_allow_html=True)
    cname = st.text_input("Course Name")
    ccode = st.text_input("Course Code")
    instructor = st.text_input("Instructor")

    if st.button("Add Course"):
        if cname and ccode and instructor:
            df = pd.read_csv(course_file)
            df.loc[len(df)] = [cname, ccode, instructor]
            df.to_csv(course_file, index=False)
            st.success("✅ Course added successfully!")
        else:
            st.warning("⚠️ Please fill all fields!")

# -------------------- ADD NEWS --------------------
if menu == "📰 Add News" and st.session_state["role"] == "Admin":
    st.markdown("<div class='section-title'>Post News / Announcement</div>", unsafe_allow_html=True)
    ntitle = st.text_input("News Title")
    ndetail = st.text_area("News Details")

    if st.button("Post News"):
        if ntitle and ndetail:
            df = pd.read_csv(news_file)
            df.loc[len(df)] = [ntitle, ndetail]
            df.to_csv(news_file, index=False)
            st.success("🗞️ News added successfully!")
        else:
            st.warning("⚠️ Please fill both fields!")

# -------------------- VIEW DATA --------------------
if menu == "📊 View Data" and st.session_state["role"] == "Admin":
    st.markdown("<div class='section-title'>View Department Data</div>", unsafe_allow_html=True)
    data_type = st.selectbox("Choose Data", ["Students", "Courses", "Feedback", "News"])
    if data_type == "Students":
        st.dataframe(pd.read_csv(student_file))
    elif data_type == "Courses":
        st.dataframe(pd.read_csv(course_file))
    elif data_type == "Feedback":
        st.dataframe(pd.read_csv(feedback_file))
    elif data_type == "News":
        st.dataframe(pd.read_csv(news_file))

# -------------------- STUDENT FEEDBACK --------------------
if menu == "📝 Feedback" and st.session_state["role"] == "Student":
    st.markdown("<div class='section-title'>Submit Your Feedback</div>", unsafe_allow_html=True)
    name = st.text_input("Your Name")
    msg = st.text_area("Your Feedback")
    rating = st.slider("Rating (1-5)", 1, 5)
    if st.button("Submit"):
        if name and msg:
            df = pd.read_csv(feedback_file)
            df.loc[len(df)] = [name, msg, rating]
            df.to_csv(feedback_file, index=False)
            st.success("✅ Feedback submitted successfully!")
        else:
            st.warning("⚠️ Please fill all fields!")

# -------------------- STUDENT VIEW NEWS --------------------
if menu == "📰 View News" and st.session_state["role"] == "Student":
    st.markdown("<div class='section-title'>Latest News & Announcements</div>", unsafe_allow_html=True)
    df = pd.read_csv(news_file)
    if len(df) == 0:
        st.info("No news available yet.")
    else:
        for i, row in df.iterrows():
            st.markdown(f"### 🗞️ {row['Title']}")
            st.write(row['Details'])
            st.write("---")

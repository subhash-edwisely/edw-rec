import streamlit as st
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from src.models.student import StudentProfile
from src.models.course import Course
from src.services.course_pool import CoursePoolGenerator
from src.services.validator import Validator
from src.services.llm_service import LLMService
from src.services.recommendation_history import RecommendationHistory

# Page config
st.set_page_config(
    page_title="FFCS Course Recommender",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if 'student_data' not in st.session_state:
    st.session_state.student_data = None
if 'courses_data' not in st.session_state:
    st.session_state.courses_data = None
if 'selected_student_id' not in st.session_state:
    st.session_state.selected_student_id = None
if 'all_students' not in st.session_state:
    st.session_state.all_students = None
if 'selected_courses' not in st.session_state:
    st.session_state.selected_courses = set()
if 'deselected_courses' not in st.session_state:
    st.session_state.deselected_courses = set()
if 'custom_selection' not in st.session_state:
    st.session_state.custom_selection = []
if 'slot_assignments' not in st.session_state:
    st.session_state.slot_assignments = {}
if 'min_credits' not in st.session_state:
    st.session_state.min_credits = 12
if 'max_credits' not in st.session_state:
    st.session_state.max_credits = 24
if 'show_final_pool' not in st.session_state:
    st.session_state.show_final_pool = False

# Load data functions
@st.cache_data
def load_all_students():
    """Load all students from student.json"""
    with open('data/student.json', 'r') as f:
        data = json.load(f)
    return data.get('students', [])

@st.cache_data
def load_courses_data():
    """Load all courses from courses.json"""
    with open('data/courses.json', 'r') as f:
        data = json.load(f)
    return [Course.from_dict(c) for c in data['courses']]

def get_student_by_id(student_id: str):
    """Get student profile by ID"""
    if st.session_state.all_students is None:
        return None
    
    for student_dict in st.session_state.all_students:
        if student_dict['student_id'] == student_id:
            return StudentProfile.from_dict(student_dict)
    return None

# Initialize data
try:
    # Load all students
    if st.session_state.all_students is None:
        st.session_state.all_students = load_all_students()
    
    # Load courses
    if st.session_state.courses_data is None:
        st.session_state.courses_data = load_courses_data()
    
    # Check if we have students
    if not st.session_state.all_students:
        st.error("No students found in data/student.json")
        st.stop()
        
except FileNotFoundError as e:
    st.error(f"Data file not found: {e}")
    st.info("Please ensure 'data/student.json' and 'data/courses.json' exist in the project directory.")
    st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Student Selector (Top of page if no student selected)
if st.session_state.student_data is None or st.session_state.selected_student_id is None:
    st.title("🎓 FFCS Course Recommender")
    st.subheader("👤 Select a Student")
    
    # Create student options
    student_options = {}
    for student in st.session_state.all_students:
        display_name = f"{student['name']} ({student['student_id']}) - Semester {student['current_semester']}"
        student_options[display_name] = student['student_id']
    
    # Student selector
    selected_display = st.selectbox(
        "Choose a student to view their profile and get recommendations:",
        options=list(student_options.keys()),
        index=0,
        help="Select a student from the list"
    )
    
    if st.button("Load Student Profile", type="primary", use_container_width=True):
        selected_id = student_options[selected_display]
        st.session_state.selected_student_id = selected_id
        st.session_state.student_data = get_student_by_id(selected_id)
        
        # Reset course selections when switching students
        st.session_state.selected_courses = set()
        st.session_state.deselected_courses = set()
        st.session_state.custom_selection = []
        st.session_state.slot_assignments = {}
        st.session_state.show_final_pool = False
        
        st.success(f"✅ Loaded profile for {st.session_state.student_data.name}")
        st.rerun()
    
    st.markdown("---")
    
    # Show preview of all students
    st.subheader("📊 Available Students")
    for student in st.session_state.all_students:
        with st.expander(f"{student['name']} - {student['student_id']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Semester:** {student['current_semester']}/8")
                st.write(f"**Year:** {student['current_year']}")
            with col2:
                st.write(f"**GPA:** {student['gpa']:.2f}/10")
                st.write(f"**Credits:** {student['total_credits_earned']}/160")
            with col3:
                st.write(f"**Interests:** {', '.join(student['interests'][:2])}")
                st.write(f"**Workload:** {student['workload_preference']}")
    
    st.stop()

# Initialize services (only after student is loaded)
course_pool_gen = CoursePoolGenerator(st.session_state.courses_data)
validator = Validator(st.session_state.min_credits, st.session_state.max_credits)
llm_service = LLMService()
history_manager = RecommendationHistory()

# Sidebar
st.sidebar.title("🎓 FFCS Recommender")
st.sidebar.markdown("---")

# Student switcher in sidebar
st.sidebar.subheader("👤 Current Student")
st.sidebar.write(f"**{st.session_state.student_data.name}**")
st.sidebar.write(f"ID: {st.session_state.student_data.student_id}")

if st.sidebar.button("🔄 Switch Student", use_container_width=True):
    st.session_state.student_data = None
    st.session_state.selected_student_id = None
    st.rerun()

st.sidebar.markdown("---")

# Credit limits
st.sidebar.subheader("⚙️ Credit Limits")
min_credits = st.sidebar.number_input(
    "Min Credits",
    min_value=12,
    max_value=24,
    value=st.session_state.min_credits,
    step=1,
    help="Minimum credits required per semester"
)
max_credits = st.sidebar.number_input(
    "Max Credits",
    min_value=12,
    max_value=24,
    value=st.session_state.max_credits,
    step=1,
    help="Maximum credits allowed per semester"
)

if min_credits != st.session_state.min_credits or max_credits != st.session_state.max_credits:
    st.session_state.min_credits = min_credits
    st.session_state.max_credits = max_credits
    validator.set_credit_limits(min_credits, max_credits)
    st.sidebar.success("✅ Limits updated!")

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["👤 Student Profile", "📚 Course Catalog", "🎯 Recommendations"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Student info
st.sidebar.markdown("### 📊 Student Info")
st.sidebar.write(f"**Name:** {st.session_state.student_data.name}")
st.sidebar.write(f"**ID:** {st.session_state.student_data.student_id}")
st.sidebar.write(f"**Semester:** {st.session_state.student_data.current_semester}/8")
st.sidebar.write(f"**GPA:** {st.session_state.student_data.gpa}/10")

progress = st.session_state.student_data.total_credits_earned / 160
st.sidebar.write(f"**Credits:** {st.session_state.student_data.total_credits_earned}/160")
st.sidebar.progress(progress)

# Failed courses
failed = st.session_state.student_data.get_failed_courses()
if failed:
    st.sidebar.error(f"**⚠️ Failed:** {len(failed)} course(s)")

st.sidebar.markdown("---")
st.sidebar.caption("VIT FFCS Course Recommendation System")

# Render pages
if page == "👤 Student Profile":
    from src.ui.profile import render_profile_page
    render_profile_page(st.session_state.student_data)

elif page == "📚 Course Catalog":
    from src.ui.catalog import render_catalog_page
    render_catalog_page(
        st.session_state.courses_data,
        st.session_state.student_data,
        course_pool_gen
    )

elif page == "🎯 Recommendations":
    from src.ui.recommendations import render_recommendations_page
    render_recommendations_page(
        st.session_state.student_data,
        st.session_state.courses_data,
        course_pool_gen,
        validator,
        llm_service,
        history_manager
    )
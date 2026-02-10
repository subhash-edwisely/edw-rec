import streamlit as st
import pandas as pd
from src.models.student import StudentProfile

def render_profile_page(student: StudentProfile):
    """Render the student profile page"""
    
    st.title("👤 Student Profile")
    
    # Basic Information (READ-ONLY)
    st.header("Basic Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Student ID", student.student_id)
        st.metric("Name", student.name)
    
    with col2:
        st.metric("Current Semester", student.current_semester)
        st.metric("Current Year", student.current_year)
    
    with col3:
        st.metric("GPA", f"{student.gpa:.2f}")
        progress = student.total_credits_earned / 160
        st.metric("Credits", f"{student.total_credits_earned}/160")
        st.progress(progress)
    
    st.markdown("---")
    
    # Editable Preferences
    st.header("📝 Editable Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Interests")
        
        # Option 1: Free text area (recommended)
        interests_text = st.text_area(
            "Enter your interests (one per line or comma-separated)",
            value="\n".join(student.interests) if student.interests else "",
            height=150,
            placeholder="Example:\nMachine Learning\nWeb Development\nCloud Computing\nBlockchain",
            help="Type your academic and career interests. These will influence course recommendations."
        )
        
        # Parse interests from text
        if interests_text.strip():
            # Support both newline and comma separation
            if '\n' in interests_text:
                interests = [i.strip() for i in interests_text.split('\n') if i.strip()]
            else:
                interests = [i.strip() for i in interests_text.split(',') if i.strip()]
        else:
            interests = []
        
        # Show parsed interests count
        if interests:
            st.caption(f"✅ {len(interests)} interest(s) detected")
            with st.expander("Preview interests"):
                for idx, interest in enumerate(interests, 1):
                    st.write(f"{idx}. {interest}")
        
        # Optional: Show common suggestions
        with st.expander("💡 Common Interest Suggestions"):
            st.caption("")
            suggestions = [
                "Artificial Intelligence", "Machine Learning", "Deep Learning",
                "Web Development", "Mobile Development", "Game Development",
                "Data Science", "Data Analytics", "Big Data",
                "Cybersecurity", "Ethical Hacking", "Network Security",
                "Cloud Computing", "DevOps", "Kubernetes",
                "Blockchain", "Cryptocurrency",
                "IoT", "Embedded Systems", "Robotics",
                "Computer Vision", "Natural Language Processing",
                "AR/VR","Quantum Computing"
            ]
            
            # Display in a grid
            cols = st.columns(3)
            for idx, suggestion in enumerate(suggestions):
                col_idx = idx % 3
                with cols[col_idx]:
                    if st.button(f"+ {suggestion}", key=f"suggest_{idx}", use_container_width=True):
                        # This is just for display - user needs to manually add
                        # st.toast(f"Copy: {suggestion}", icon="📋")
                        pass
    
    with col2:
        st.subheader("⚙️ Workload Preference")
        workload = st.select_slider(
            "Workload Preference",
            options=["low", "medium", "high"],
            value=student.workload_preference,
            help="Low = lighter semesters, High = more credits per semester",
            label_visibility="collapsed"
        )
        
        # Workload explanation
        workload_info = {
            "low": "📘 **Light workload**: 16-20 credits/semester. More time for each course, better work-life balance.",
            "medium": "📗 **Moderate workload**: 20-24 credits/semester. Balanced approach, standard progression.",
            "high": "📕 **Heavy workload**: 24-27 credits/semester. Fast-track graduation, intensive study required."
        }
        st.info(workload_info.get(workload, ""))
    
    # Save button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("💾 Save Preferences", type="primary", use_container_width=True):
            if not interests:
                st.warning("⚠️ No interests detected. Add at least one interest for better recommendations.")
            else:
                student.interests = interests
                student.workload_preference = workload
                st.success("✅ Preferences saved! Recommendations will reflect these changes.")
                st.balloons()
                st.rerun()
    
    st.markdown("---")
    
    # Semester-wise Results (READ-ONLY)
    st.header("📊 Academic History (Read-Only)")
    st.info("Grade data cannot be edited. Contact registrar for corrections.")
    
    # Get currently pending failed courses
    currently_failed = set(student.get_failed_courses())
    
    for sem_result in student.semester_results:
        with st.expander(f"📅 Semester {sem_result.semester}", expanded=False):
            # Create DataFrame
            courses_data = []
            for course in sem_result.courses:
                # Annotate status
                if course.status == 'failed' and course.course_code not in currently_failed:
                    status_icon = "✅ Cleared"
                elif course.status == 'failed':
                    status_icon = "❌ Failed"
                else:
                    status_icon = "✓ Passed"
                
                courses_data.append({
                    "Course Code": course.course_code,
                    "Grade": course.grade,
                    "Credits": course.credits,
                    "Status": status_icon
                })
            
            df = pd.DataFrame(courses_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Semester stats
            total_credits = sum(c.credits for c in sem_result.courses)
            passed_credits = sum(c.credits for c in sem_result.courses if c.status == 'passed')
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Credits", total_credits)
            col2.metric("Passed Credits", passed_credits)
            col3.metric("Courses", len(sem_result.courses))
    
    st.markdown("---")
    
    # Failed Courses Summary
    failed_courses = student.get_failed_courses()
    if failed_courses:
        st.header("⚠️ Failed Courses (Priority: Clear These)")
        st.error(f"**{len(failed_courses)} failed course(s):** {', '.join(failed_courses)}")
        st.warning("These courses will be prioritized in recommendations and must be cleared for graduation.")
    else:
        st.success("✅ No failed courses! Great job!")
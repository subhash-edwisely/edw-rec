import streamlit as st
import pandas as pd
from typing import List
from src.models.course import Course
from src.models.student import StudentProfile
from src.services.course_pool import CoursePoolGenerator

def render_catalog_page(all_courses: List[Course], student: StudentProfile, 
                       course_pool_gen: CoursePoolGenerator):
    """Render the course catalog page"""
    
    st.title("📚 Course Catalog")
    
    # Generate available pool
    available_courses = course_pool_gen.generate_pool(
        student,
        st.session_state.selected_courses,
        st.session_state.deselected_courses
    )
    
    st.info(f"Showing {len(available_courses)} available courses for Year {student.current_year}, Semester {student.current_semester}")
    
    st.markdown("---")
    
    # Filters
    st.subheader("🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        type_filter = st.multiselect(
            "Course Type",
            ["FC", "DLES", "DC", "DE", "OE"],
            default=["DC", "DE", "OE"],
            help="FC=Foundation, DC=Discipline Core, DE=Discipline Elective, OE=Open Elective"
        )
    
    with col2:
        year_filter = st.multiselect(
            "Year Level",
            [1, 2, 3, 4],
            default=[student.current_year]
        )
    
    with col3:
        difficulty_filter = st.slider(
            "Max Difficulty",
            min_value=1,
            max_value=7,
            value=7
        )
    
    with col4:
        search = st.text_input("🔎 Search Course", "", placeholder="Code or name...")
    
    # Filter courses
    filtered_courses = []
    for course in available_courses:
        if course.type not in type_filter:
            continue
        if course.year_level not in year_filter:
            continue
        if course.difficulty > difficulty_filter:
            continue
        if search and search.lower() not in course.name.lower() and search.lower() not in course.course_code.lower():
            continue
        filtered_courses.append(course)
    
    st.markdown("---")
    
    # Bulk Actions
    st.subheader("⚡ Bulk Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Select All Filtered", use_container_width=True):
            for course in filtered_courses:
                st.session_state.selected_courses.add(course.course_code)
                st.session_state.deselected_courses.discard(course.course_code)
            st.success(f"Selected {len(filtered_courses)} courses")
            st.rerun()
    
    with col2:
        if st.button("❌ Deselect All Filtered", use_container_width=True):
            for course in filtered_courses:
                st.session_state.deselected_courses.add(course.course_code)
                st.session_state.selected_courses.discard(course.course_code)
            st.success(f"Deselected {len(filtered_courses)} courses")
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset All Selections", use_container_width=True):
            st.session_state.selected_courses = set()
            st.session_state.deselected_courses = set()
            st.success("All selections cleared")
            st.rerun()
    
    with col4:
        if st.button("📋 Show Final Pool", use_container_width=True):
            st.session_state.show_final_pool = True
    
    st.markdown("---")
    
    # Display courses with inline selection
    st.subheader(f"Available Courses ({len(filtered_courses)})")
    
    if filtered_courses:
        # Create table data with selection checkboxes
        table_data = []
        for course in filtered_courses:
            is_selected = course.course_code in st.session_state.selected_courses
            is_deselected = course.course_code in st.session_state.deselected_courses
            
            if is_selected:
                status = "✅ Selected"
            elif is_deselected:
                status = "❌ Excluded"
            else:
                status = "⚪ Available"
            
            table_data.append({
                "Status": status,
                "Code": course.course_code,
                "Name": course.name,
                "Credits": course.credits,
                "Type": course.type,
                "Year": course.year_level,
                "Difficulty": "⭐" * course.difficulty,
                "Prerequisites": ", ".join(course.prerequisites) if course.prerequisites else "None",
                "Slots": len(course.slots)
            })
        
        df = pd.DataFrame(table_data)
        
        st.dataframe(
            df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Individual course selection
        st.subheader("📖 Individual Course Selection")
        
        selected_code = st.selectbox(
            "Select a course to view details and toggle:",
            [""] + [c.course_code for c in filtered_courses],
            format_func=lambda x: f"{x} - {next((c.name for c in filtered_courses if c.course_code == x), '')}" if x else "-- Select a course --"
        )
        
        if selected_code:
            course = next(c for c in filtered_courses if c.course_code == selected_code)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### {course.course_code}: {course.name}")
                st.write(f"**Type:** {course.type} | **Credits:** {course.credits} | **Year Level:** {course.year_level}")
                st.write(f"**Difficulty:** {'⭐' * course.difficulty}")
                
                if course.prerequisites:
                    st.write(f"**Prerequisites:** {', '.join(course.prerequisites)}")
                else:
                    st.write("**Prerequisites:** None")
                
                st.write(f"**Available Slots:** {', '.join(course.slots)}")
            
            with col2:
                st.markdown("#### Actions")
                
                is_selected = course.course_code in st.session_state.selected_courses
                is_deselected = course.course_code in st.session_state.deselected_courses
                
                if is_selected:
                    if st.button("✅ Selected (Click to remove)", key=f"toggle_{course.course_code}", use_container_width=True):
                        st.session_state.selected_courses.remove(course.course_code)
                        st.rerun()
                elif is_deselected:
                    if st.button("❌ Excluded (Click to reset)", key=f"toggle_{course.course_code}", use_container_width=True):
                        st.session_state.deselected_courses.remove(course.course_code)
                        st.rerun()
                else:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Select", key=f"select_{course.course_code}", use_container_width=True):
                            st.session_state.selected_courses.add(course.course_code)
                            st.session_state.deselected_courses.discard(course.course_code)
                            st.rerun()
                    with col_b:
                        if st.button("❌ Exclude", key=f"exclude_{course.course_code}", use_container_width=True):
                            st.session_state.deselected_courses.add(course.course_code)
                            st.session_state.selected_courses.discard(course.course_code)
                            st.rerun()
    else:
        st.info("No courses match the current filters.")
    
    st.markdown("---")
    
    # Final Course Pool Display
    if st.session_state.get('show_final_pool', False) or st.session_state.selected_courses or st.session_state.deselected_courses:
        st.subheader("📋 Final Course Pool for This Semester")
        
        final_pool = course_pool_gen.generate_pool(
            student,
            st.session_state.selected_courses,
            st.session_state.deselected_courses
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.selected_courses:
                st.success(f"**✅ Manually Selected ({len(st.session_state.selected_courses)}):**")
                st.write(", ".join(sorted(st.session_state.selected_courses)))
        
        with col2:
            if st.session_state.deselected_courses:
                st.error(f"**❌ Manually Excluded ({len(st.session_state.deselected_courses)}):**")
                st.write(", ".join(sorted(st.session_state.deselected_courses)))
        
        st.info(f"**Total courses in final pool: {len(final_pool)}**")
        
        # Show final pool table
        final_table = []
        for course in final_pool:
            final_table.append({
                "Code": course.course_code,
                "Name": course.name,
                "Credits": course.credits,
                "Type": course.type,
                "Difficulty": "⭐" * course.difficulty
            })
        
        if final_table:
            st.dataframe(pd.DataFrame(final_table), use_container_width=True, hide_index=True)
        
        st.success("✅ This pool will be used for generating recommendations.")
import streamlit as st
import pandas as pd
from typing import List, Dict
from src.models.course import Course
from src.models.student import StudentProfile
from src.services.course_pool import CoursePoolGenerator
from src.services.validator import Validator
from src.services.llm_service import LLMService

def render_recommendations_page(student: StudentProfile, all_courses: List[Course],
                                course_pool_gen: CoursePoolGenerator,
                                validator: Validator, llm_service: LLMService,
                                history_manager=None):
    """Render the recommendations page"""
    
    st.title("🎯 Course Recommendations")
    
    # Tabs
    tabs = st.tabs([
        f"📅 Semester {student.current_semester} (Current)",
        "🔮 Future Projections",
        "🛠️ Custom Set Builder",
        "📜 History"
    ])
    
    # Tab 1: Current Semester
    with tabs[0]:
        render_current_semester_recommendations(
            student, all_courses, course_pool_gen, validator, llm_service, history_manager
        )
    
    # Tab 2: Future Projections
    with tabs[1]:
        render_future_projections(
            student, all_courses, course_pool_gen, validator, llm_service
        )
    
    # Tab 3: Custom Set Builder
    with tabs[2]:
        render_custom_set_builder(student, all_courses, course_pool_gen, validator, llm_service)
    
    # Tab 4: History
    with tabs[3]:
        if history_manager:
            render_history_tab(student, history_manager)
        else:
            st.info("History tracking not available")

def render_current_semester_recommendations(student: StudentProfile, all_courses: List[Course],
                                           course_pool_gen: CoursePoolGenerator,
                                           validator: Validator, llm_service: LLMService,
                                           history_manager=None):
    """Render current semester recommendations"""
    
    st.subheader(f"Recommendations for Semester {student.current_semester}")
    
    # Generate button
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔮 Generate Recommendations", key="gen_current", type="primary", use_container_width=True):
            with st.spinner("Analyzing your profile and generating personalized recommendations..."):
                # Get available courses
                available_courses = course_pool_gen.generate_pool(
                    student,
                    st.session_state.selected_courses,
                    st.session_state.deselected_courses
                )
                
                # Generate recommendations
                recommendations = llm_service.generate_recommendations(
                    student=student,
                    available_courses=available_courses,
                    min_credits=st.session_state.min_credits,
                    max_credits=st.session_state.max_credits,
                    future_semester=False
                )
                
                st.session_state['current_recommendations'] = recommendations
                
                # Save to history
                if history_manager:
                    preferences = {
                        'min_credits': st.session_state.min_credits,
                        'max_credits': st.session_state.max_credits,
                        'selected_courses': st.session_state.selected_courses,
                        'deselected_courses': st.session_state.deselected_courses
                    }
                    history_manager.save_recommendation(
                        student, preferences, recommendations, student.current_semester
                    )
                
                st.success("✅ Recommendations generated and saved to history!")
    
    with col2:
        st.metric("Pool Size", len(course_pool_gen.generate_pool(
            student,
            st.session_state.selected_courses,
            st.session_state.deselected_courses
        )))
    
    # Display recommendations
    if 'current_recommendations' in st.session_state:
        recommendations = st.session_state['current_recommendations']
        
        if 'recommendations' in recommendations and len(recommendations['recommendations']) > 0:
            st.markdown("---")
            st.subheader("📊 Ranked Recommendations")
            
            for rec in recommendations['recommendations']:
                render_recommendation_card(
                    rec, all_courses, student, validator, 
                    is_current=True, semester=student.current_semester
                )
        else:
            st.error("❌ No recommendations generated. Try adjusting your course pool or credit limits.")
    else:
        st.info("👆 Click 'Generate Recommendations' to get AI-powered course suggestions.")

def render_future_projections(student: StudentProfile, all_courses: List[Course],
                              course_pool_gen: CoursePoolGenerator,
                              validator: Validator, llm_service: LLMService):
    """Render future semester projections with cascading logic"""
    
    st.subheader("🔮 Future Semester Projections")
    
    # Check if current recommendations exist
    if 'current_recommendations' not in st.session_state or 'recommendations' not in st.session_state['current_recommendations']:
        st.warning("⚠️ Please generate current semester recommendations first.")
        return
    
    current_recs = st.session_state['current_recommendations']['recommendations']
    
    st.info(f"📊 Cascading projections: Each future semester assumes all previous recommendations are completed.")
    
    # For each current recommendation, show cascading future path
    for i, current_rec in enumerate(current_recs):
        with st.expander(f"🔮 Complete Path for Strategy: {current_rec.get('strategy_name', f'Recommendation #{current_rec['rank']}')} ", expanded=(i==0)):
            st.markdown(f"**Current Semester {student.current_semester} Strategy:** {current_rec['reasoning']}")
            st.markdown(f"**Current Courses:** {', '.join(current_rec['courses'])} ({current_rec['total_credits']} credits)")
            
            st.markdown("---")
            
            # Generate cascading projections
            max_future_sems = min(3, 8 - student.current_semester)
            
            if max_future_sems == 0:
                st.info("You're in the final semester!")
                continue
            
            future_tabs = []
            for j in range(max_future_sems):
                target_sem = student.current_semester + j + 1
                future_tabs.append(f"Semester {target_sem}")
            
            tabs = st.tabs(future_tabs)
            
            # Store projections for cascading
            projection_chain = []
            
            for j, tab in enumerate(tabs):
                with tab:
                    target_sem = student.current_semester + j + 1
                    
                    # Generate button
                    if st.button(f"Generate Projection for Sem {target_sem}", 
                               key=f"gen_cascade_{i}_{target_sem}"):
                        with st.spinner(f"Projecting Semester {target_sem} (cascading through previous semesters)..."):
                            future_rec = llm_service.generate_future_projections(
                                student=student,
                                all_courses=all_courses,
                                current_recommendation=current_rec,
                                min_credits=st.session_state.min_credits,
                                max_credits=st.session_state.max_credits,
                                target_semester=target_sem,
                                previous_projections=projection_chain
                            )
                            
                            st.session_state[f'cascade_rec_{i}_{target_sem}'] = future_rec
                            projection_chain.append(future_rec)
                    
                    # Load existing projection if available
                    if f'cascade_rec_{i}_{target_sem}' in st.session_state:
                        future_recs = st.session_state[f'cascade_rec_{i}_{target_sem}']
                        projection_chain.append(future_recs)
                        
                        if 'recommendations' in future_recs and len(future_recs['recommendations']) > 0:
                            # Show assumptions
                            st.info(f"**Assumes completed:** Sem {student.current_semester}" + 
                                  (f" through Sem {target_sem-1}" if j > 0 else ""))
                            
                            # Show best recommendation
                            best_future = future_recs['recommendations'][0]
                            render_recommendation_card(
                                best_future, all_courses, student, validator,
                                is_current=False, semester=target_sem, show_validation=False
                            )

def render_recommendation_card(rec: Dict, all_courses: List[Course],
                              student: StudentProfile, validator: Validator,
                              is_current: bool, semester: int, show_validation: bool = True):
    """Render a single recommendation card"""
    
    # Get course objects
    rec_courses = [c for c in all_courses if c.course_code in rec['courses']]
    
    # Strategy display
    strategy_name = rec.get('strategy_name', f"Option {rec['rank']}")
    
    with st.expander(
        f"📋 {strategy_name} - {rec['total_credits']} Credits", 
        expanded=rec['rank'] == 1
    ):
        # Suitability badge
        suitability = rec.get('suitability', '')
        if suitability:
            st.info(f"**👤 Suitability:** {suitability}")
        
        # Overall Strategy
        st.markdown("### 📋 Strategy Overview")
        st.write(rec.get('reasoning', 'No reasoning provided'))
        
        # Graduation Impact
        if 'graduation_impact' in rec:
            st.markdown("### 🎓 Graduation Impact")
            st.info(rec['graduation_impact'])
        
        # Course-by-course rationale
        if 'course_rationale' in rec and rec['course_rationale']:
            st.markdown("### 🎯 Course Selection Rationale")
            for code, rationale in rec['course_rationale'].items():
                course = next((c for c in rec_courses if c.course_code == code), None)
                if course:
                    st.markdown(f"**{code}** ({course.name}):")
                    st.write(f"_{rationale}_")
        
        st.markdown("---")
        
        # Breakdown
        if 'breakdown' in rec:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📌 Mandatory Courses:**")
                for code in rec['breakdown'].get('mandatory', []):
                    course = next((c for c in rec_courses if c.course_code == code), None)
                    if course:
                        st.write(f"• {code}: {course.name} ({course.credits} cr)")
            
            with col2:
                st.markdown("**🎨 Elective Courses:**")
                electives = rec['breakdown'].get('electives', [])
                if electives:
                    for code in electives:
                        course = next((c for c in rec_courses if c.course_code == code), None)
                        if course:
                            st.write(f"• {code}: {course.name} ({course.credits} cr)")
                else:
                    st.write("_None_")
        
        # Course table
        st.markdown("### 📚 Course Details")
        course_data = []
        for course in rec_courses:
            course_data.append({
                "Code": course.course_code,
                "Name": course.name,
                "Credits": course.credits,
                "Type": course.type,
                "Difficulty": "⭐" * course.difficulty,
                "Prerequisites": ", ".join(course.prerequisites) if course.prerequisites else "None",
                "Slots": ", ".join(course.slots) if is_current else "N/A"
            })
        
        df = pd.DataFrame(course_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Slot allocation for current semester
        if is_current and 'slot_assignments' in rec:
            st.markdown("### 🕐 Slot Allocation")
            
            slots = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2', 
                    'E1', 'E2', 'F1', 'F2', 'G1', 'G2']
            
            slot_map = {}
            for code, slot_str in rec.get('slot_assignments', {}).items():
                for slot in slot_str.split('+'):
                    slot_map[slot] = code
            
            # Display in grid
            cols = st.columns(7)
            for i, slot in enumerate(slots):
                with cols[i % 7]:
                    if slot in slot_map:
                        st.success(f"**{slot}**\n{slot_map[slot]}")
                    else:
                        st.info(slot)
        
        # Validation (only for current semester)
        if show_validation and is_current:
            st.markdown("---")
            st.markdown("### ✅ Validation Results")
            
            slot_assignments = rec.get('slot_assignments', {})
            validation = validator.validate_selection(rec_courses, slot_assignments, student)
            
            if validation['valid']:
                st.success("✅ This recommendation is valid and ready to register!")
            else:
                st.error("❌ Validation Issues Found:")
                for error in validation['errors']:
                    st.write(f"• {error}")
            
            if validation['warnings']:
                st.warning("⚠️ Important Warnings:")
                for warning in validation['warnings']:
                    st.write(f"• {warning}")
        
        # Action button
        if is_current:
            if st.button(f"📌 Use This for Custom Builder", key=f"use_rec_{semester}_{rec['rank']}", use_container_width=True):
                st.session_state.custom_selection = rec['courses']
                if 'slot_assignments' in rec:
                    st.session_state.slot_assignments = rec['slot_assignments']
                st.success("✅ Loaded into Custom Set Builder! Switch to that tab.")

def render_custom_set_builder(student: StudentProfile, all_courses: List[Course],
                              course_pool_gen: CoursePoolGenerator, validator: Validator,
                              llm_service=None):
    """Render custom course selection builder with feasibility analysis"""
    
    st.subheader("🛠️ Build Your Custom Course Set")
    
    # Get available courses
    available_courses = course_pool_gen.generate_pool(
        student,
        st.session_state.selected_courses,
        st.session_state.deselected_courses
    )
    
    # Course selection
    st.markdown("**Select Courses:**")
    
    selected_codes = st.multiselect(
        "Choose courses for this semester",
        [c.course_code for c in available_courses],
        default=st.session_state.custom_selection,
        format_func=lambda x: f"{x} - {next((c.name for c in available_courses if c.course_code == x), '')}"
    )
    
    st.session_state.custom_selection = selected_codes
    
    if selected_codes:
        selected_courses = [c for c in all_courses if c.course_code in selected_codes]
        
        # Show selected courses
        st.markdown("---")
        st.markdown("**📚 Selected Courses:**")
        course_data = []
        total_credits = 0
        
        for course in selected_courses:
            course_data.append({
                "Code": course.course_code,
                "Name": course.name,
                "Credits": course.credits,
                "Type": course.type,
                "Difficulty": "⭐" * course.difficulty
            })
            total_credits += course.credits
        
        df = pd.DataFrame(course_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns(2)
        col1.metric("Total Credits", total_credits)
        col2.metric("Credit Status", 
                   "✅ Valid" if st.session_state.min_credits <= total_credits <= st.session_state.max_credits 
                   else "❌ Out of Range")
        
        st.markdown("---")
        
        # Slot assignment
        st.markdown("**🕐 Assign Slots:**")
        
        for course in selected_courses:
            if len(course.slots) > 1:
                current_slot = st.session_state.slot_assignments.get(course.course_code, course.slots[0])
                chosen_slot = st.selectbox(
                    f"{course.course_code} - {course.name}",
                    course.slots,
                    index=course.slots.index(current_slot) if current_slot in course.slots else 0,
                    key=f"slot_{course.course_code}"
                )
                st.session_state.slot_assignments[course.course_code] = chosen_slot
            else:
                st.info(f"{course.course_code}: {course.slots[0]} (only option)")
                st.session_state.slot_assignments[course.course_code] = course.slots[0]
        
        st.markdown("---")
        
        # Validate and Analyze
        if st.button("🔍 Validate & Analyze Feasibility", type="primary", use_container_width=True):
            st.markdown("### 📊 Validation & Feasibility Analysis")
            
            validation = validator.validate_selection(
                selected_courses,
                st.session_state.slot_assignments,
                student
            )
            
            # Immediate validation
            st.markdown("#### ✅ Immediate Validation")
            if validation['valid']:
                st.success("✅ Your selection is valid for this semester!")
            else:
                st.error("❌ Issues found:")
                for error in validation['errors']:
                    st.write(f"• {error}")
            
            if validation['warnings']:
                st.warning("⚠️ Warnings:")
                for warning in validation['warnings']:
                    st.write(f"• {warning}")
            
            st.markdown("---")
            
            # AI-Powered Feasibility Analysis
            st.markdown("#### 🤖 AI-Powered Graduation Feasibility Analysis")
            
            with st.spinner("Analyzing graduation feasibility with AI..."):
                from src.ui.recommendations import render_recommendations_page
                ai_analysis = llm_service.analyze_custom_set_feasibility(
                    student=student,
                    selected_courses=selected_courses,
                    all_courses=all_courses,
                    min_credits=st.session_state.min_credits,
                    max_credits=st.session_state.max_credits
                )
            
            # Risk badge
            risk_colors = {
                "none": "🟢",
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "critical": "🔴"
            }
            risk_icon = risk_colors.get(ai_analysis.get('graduation_risk', 'medium'), '🟡')
            
            # Summary
            if ai_analysis.get('feasible', True):
                st.success(f"{risk_icon} **{ai_analysis.get('summary', 'Analysis completed')}**")
            else:
                st.error(f"{risk_icon} **{ai_analysis.get('summary', 'Analysis completed')}**")
            
            # Detailed Analysis
            st.markdown("##### 📝 Detailed Analysis")
            st.info(ai_analysis.get('detailed_analysis', 'No detailed analysis available'))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 🎯 Impact on Future Semesters")
                st.write(ai_analysis.get('impact_on_future', 'No impact analysis available'))
            
            with col2:
                st.markdown("##### 💡 Recommendations")
                st.write(ai_analysis.get('recommendations', 'No recommendations available'))
            
            # Warnings and Positives
            if ai_analysis.get('warnings'):
                st.warning("##### ⚠️ Specific Warnings")
                for warning in ai_analysis['warnings']:
                    st.write(f"• {warning}")
            
            if ai_analysis.get('positives'):
                st.success("##### ✅ Positive Aspects")
                for positive in ai_analysis['positives']:
                    st.write(f"• {positive}")
    else:
        st.info("👆 Select courses to build your custom set and analyze feasibility.")

def render_history_tab(student: StudentProfile, history_manager):
    """Render recommendation history"""
    st.subheader("📜 Recommendation History")
    
    history = history_manager.get_student_history(student.student_id)
    
    if not history:
        st.info("No recommendation history yet. Generate recommendations to see them here.")
        return
    
    # Sort by timestamp descending
    history = sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    st.write(f"**Total sessions:** {len(history)}")
    
    # Group by semester
    semesters = {}
    for entry in history:
        sem = entry['semester']
        if sem not in semesters:
            semesters[sem] = []
        semesters[sem].append(entry)
    
    # Display by semester
    for sem in sorted(semesters.keys(), reverse=True):
        with st.expander(f"📅 Semester {sem} ({len(semesters[sem])} session(s))", expanded=sem==student.current_semester):
            for i, entry in enumerate(semesters[sem]):
                st.markdown(f"### Session {i+1}")
                st.caption(f"Generated: {entry['timestamp']}")
                
                # Preferences
                col1, col2, col3 = st.columns(3)
                col1.metric("GPA", entry['gpa'])
                col2.metric("Credits", entry['credits_earned'])
                col3.metric("Credit Range", f"{entry['preferences']['min_credits']}-{entry['preferences']['max_credits']}")
                
                # Preferences
                st.write(f"**Interests:** {', '.join(entry['preferences']['interests'])}")
                st.write(f"**Workload:** {entry['preferences']['workload']}")
                
                if entry['preferences']['selected_courses']:
                    st.write(f"**Manually Selected:** {', '.join(entry['preferences']['selected_courses'])}")
                if entry['preferences']['deselected_courses']:
                    st.write(f"**Manually Excluded:** {', '.join(entry['preferences']['deselected_courses'])}")
                
                # Recommendations
                st.markdown("**Recommendations:**")
                for rec in entry['recommendations']:
                    strategy = rec.get('strategy_name', f"Option {rec['rank']}")
                    st.write(f"**{strategy}:** {', '.join(rec['courses'])} ({rec['total_credits']} credits)")
                
                st.markdown("---")
    
    # Clear history button
    if st.button("🗑️ Clear All History", type="secondary"):
        if st.button("⚠️ Confirm Delete", key="confirm_clear"):
            history_manager.clear_student_history(student.student_id)
            st.success("History cleared!")
            st.rerun()
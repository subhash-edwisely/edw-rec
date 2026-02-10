import json
import os
from typing import List, Dict, Set
from openai import OpenAI
from src.models.student import StudentProfile
from src.models.course import Course

class LLMService:
    """Service to generate course recommendations using LLM"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4.1"
    
    def generate_recommendations(self,
                                student: StudentProfile,
                                available_courses: List[Course],
                                min_credits: int = 16,
                                max_credits: int = 27,
                                future_semester: bool = False,
                                assumed_passed: List[str] = None) -> Dict:
        """
        Generate 3 ranked course recommendations using PromptBuilder.
        Includes hard post-processing credit enforcement.
        """
        from src.services.prompt_builder import PromptBuilder

        is_project_semester = student.current_semester >= 7
        prompt_builder = PromptBuilder()
        prompt_data = prompt_builder.build_complete_prompt(
            student=student,
            available_courses=available_courses,
            min_credits=min_credits,
            max_credits=max_credits,
            future_semester=future_semester,
            assumed_passed=assumed_passed,
            is_project_semester=is_project_semester
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt_data["system"]},
                    {"role": "user", "content": prompt_data["user"]}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            content = response.choices[0].message.content

            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    recommendations = json.loads(content[json_start:json_end])
                else:
                    recommendations = json.loads(content)

                if 'recommendations' in recommendations:
                    fixed_recs = []
                    for rec in recommendations['recommendations']:
                        rec = self._enforce_credit_limits(
                            rec, available_courses, min_credits, max_credits,
                            current_semester=student.current_semester
                        )
                        if rec is not None:
                            fixed_recs.append(rec)

                    if fixed_recs:
                        recommendations['recommendations'] = fixed_recs
                    else:
                        recommendations = self._create_fallback_recommendations(
                            available_courses, min_credits, max_credits, is_project_semester
                        )

            except json.JSONDecodeError:
                recommendations = self._create_fallback_recommendations(
                    available_courses, min_credits, max_credits, is_project_semester
                )

            return recommendations

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._create_fallback_recommendations(
                available_courses, min_credits, max_credits, is_project_semester
            )
    
    def generate_future_projections(self,
                                    student: StudentProfile,
                                    all_courses: List[Course],
                                    current_recommendation: Dict,
                                    min_credits: int,
                                    max_credits: int,
                                    target_semester: int,
                                    previous_projections: List[Dict] = None) -> Dict:
        """
        Generate future semester recommendations with cascading assumptions.
        For Sem N+1: assumes Sem N courses passed
        For Sem N+2: assumes Sem N + Sem N+1 courses passed
        etc.
        """
        from src.services.prompt_builder import PromptBuilder

        assumed_completed = list(current_recommendation['courses'])

        if previous_projections:
            for proj in previous_projections:
                if 'recommendations' in proj and len(proj['recommendations']) > 0:
                    best_proj = proj['recommendations'][0]
                    assumed_completed.extend(best_proj['courses'])

        # Simulate completion AND set correct target semester on the student object
        simulated_student = self._simulate_cascading_completion(
            student, assumed_completed, all_courses, target_semester
        )

        # Build course pool for target semester
        passed = set(simulated_student.get_passed_courses())
        target_year = (target_semester + 1) // 2

        available = []
        for course in all_courses:
            if course.course_code in passed:
                continue
            # Hard gate: Proj1 only in sem 7, Proj2 only in sem 8
            if course.course_code == 'Proj1' and target_semester != 7:
                continue
            if course.course_code == 'Proj2' and target_semester != 8:
                continue
            if course.year_level <= target_year:
                available.append(course)

        # Use PromptBuilder for enriched future-specific prompt
        prompt_builder = PromptBuilder()
        simulated_credits = simulated_student.total_credits_earned
        prompt_data = prompt_builder.build_future_complete_prompt(
            student=simulated_student,
            available_courses=available,
            min_credits=min_credits,
            max_credits=max_credits,
            target_semester=target_semester,
            assumed_completed=assumed_completed,
            simulated_credits=simulated_credits
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt_data["system"]},
                    {"role": "user", "content": prompt_data["user"]}
                ],
                temperature=0.7,
                max_tokens=3000
            )

            content = response.choices[0].message.content

            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    recommendations = json.loads(content[json_start:json_end])
                else:
                    recommendations = json.loads(content)

                if 'recommendations' in recommendations:
                    fixed_recs = []
                    for rec in recommendations['recommendations']:
                        rec = self._enforce_credit_limits(
                            rec, available, min_credits, max_credits,
                            current_semester=target_semester
                        )
                        if rec is not None:
                            fixed_recs.append(rec)

                    if fixed_recs:
                        recommendations['recommendations'] = fixed_recs
                    else:
                        recommendations = self._create_fallback_recommendations(
                            available, min_credits, max_credits, target_semester >= 7
                        )

            except json.JSONDecodeError:
                recommendations = self._create_fallback_recommendations(
                    available, min_credits, max_credits, target_semester >= 7
                )

            return recommendations

        except Exception as e:
            print(f"Error generating future projections: {e}")
            return self._create_fallback_recommendations(
                available, min_credits, max_credits, target_semester >= 7
            )
    
    def _simulate_cascading_completion(self, student: StudentProfile, completed_courses: List[str], all_courses: List[Course], target_semester: int = None) -> StudentProfile:
        """Simulate student profile after completing multiple semesters of courses"""
        import copy
        from src.models.student import SemesterResult, CourseResult
        
        simulated = copy.deepcopy(student)
        
        course_map = {c.course_code: c for c in all_courses}
        new_credits = sum(course_map[code].credits for code in completed_courses if code in course_map)
        
        simulated.total_credits_earned += new_credits
        
        new_courses = [
            CourseResult(course_code=code, grade="A", credits=course_map[code].credits, status="passed")
            for code in completed_courses if code in course_map
        ]
        
        if new_courses:
            simulated.semester_results.append(
                SemesterResult(semester=student.current_semester, courses=new_courses)
            )
        
        # CRITICAL: update semester so prompts, risk checks, and project logic use correct values
        if target_semester is not None:
            simulated.current_semester = target_semester
            simulated.current_year = (target_semester + 1) // 2
        
        return simulated
    
    def _simulate_completion(self, student: StudentProfile, completed_courses: List[str], all_courses: List[Course]) -> StudentProfile:
        """Simulate student profile after completing given courses"""
        # Clone student
        import copy
        simulated = copy.deepcopy(student)
        
        # Add completed courses to passed
        course_map = {c.course_code: c for c in all_courses}
        new_credits = sum(course_map[code].credits for code in completed_courses if code in course_map)
        
        simulated.total_credits_earned += new_credits
        simulated.current_semester += 1
        
        # Add to semester results
        from src.models.student import SemesterResult, CourseResult
        new_courses = [
            CourseResult(course_code=code, grade="A", credits=course_map[code].credits, status="passed")
            for code in completed_courses if code in course_map
        ]
        simulated.semester_results.append(
            SemesterResult(semester=student.current_semester, courses=new_courses)
        )
        
        return simulated
    
    def _build_prompt(self, student: StudentProfile, available_courses: List[Course],
                     min_credits: int, max_credits: int, risk_profile: str,
                     future_semester: bool, assumed_passed: List[str] = None,
                     is_project_semester: bool = False) -> str:
        """Build the prompt for LLM with project semester awareness. Maintain the conversation not as a third-person, but as if you are talking or suggesting that person."""
        
        # Format course pool with slots
        courses_data = []
        project_courses = []
        
        for course in available_courses:
            course_info = {
                'code': course.course_code,
                'name': course.name,
                'credits': course.credits,
                'type': course.type,
                'prerequisites': course.prerequisites,
                'difficulty': course.difficulty,
                'slots': course.slots if not future_semester else None
            }
            courses_data.append(course_info)
            
            # Identify project courses
            if course.type == 'PR':
                project_courses.append(course)
        
        failed_courses = student.get_failed_courses()
        gpa_trend = student.calculate_gpa_trend()
        
        # Get remaining mandatory courses
        passed = set(student.get_passed_courses())
        mandatory_remaining = [c for c in available_courses if c.type in ['DC', 'FC', 'DLES']]
        electives_available = [c for c in available_courses if c.type in ['DE', 'OE']]
        
        remaining_sems = 8 - student.current_semester
        total_remaining_credits = 160 - student.total_credits_earned
        
        # Calculate mandatory credits needed
        mandatory_credits_remaining = sum(c.credits for c in mandatory_remaining)
        
        # Project semester context
        project_context = ""
        if is_project_semester:
            if student.current_semester == 7:
                project_context = f"""
🎓 SEMESTER 7 - PROJECT PREPARATION PHASE:
- **CRITICAL**: Student should start Project 1 (Proj1) if available
- Project 1 (3 credits) is prerequisite for Project 2 in Semester 8
- Focus: Complete remaining mandatory courses + Project 1 + minimal electives
- Strategy: Prioritize Proj1 in ALL recommendations to avoid delays in final semester
"""
            elif student.current_semester == 8:
                project_context = f"""
🎓🎓 FINAL SEMESTER (8) - PROJECT COMPLETION PHASE:
- **MANDATORY**: Project 2 (Proj2 - 10 credits) MUST be included in ALL recommendations
- This is the FINAL semester - student MUST graduate
- Project 2 alone takes 10 credits, leaving {max_credits - 10} credits for other courses
- Focus: Project 2 + any remaining mandatory courses + minimal completion courses
- NO NEW electives unless student has buffer credits
- Strategy: ALL three recommendations MUST include Project 2 as highest priority
"""
        
        # Build project courses list for display
        project_list = ""
        if project_courses:
            project_list = "\n**AVAILABLE PROJECT COURSES:**\n"
            for proj in project_courses:
                project_list += f"- {proj.course_code} ({proj.name}): {proj.credits} credits, Difficulty: {proj.difficulty}/7\n"
        
        future_context = ""
        if future_semester and assumed_passed:
            future_context = f"""
FUTURE SEMESTER SIMULATION:
- Assuming the following courses from current semester are PASSED: {', '.join(assumed_passed)}
- These courses are now prerequisites for advanced courses
- Student's updated credits: {student.total_credits_earned}
- Focus on: New courses unlocked + remaining mandatory courses
- If the future semester is 8, then it is mandatory to include Project 2 and project 1 is a prerequisite for project 2.
"""
        
        prompt = f"""You are a course advisor for VIT's FFCS system. Provide 3 DIFFERENT strategic approaches for course selection.

STUDENT PROFILE:
- Name: {student.name}
- Semester: {student.current_semester} of 8 {"⚠️ FINAL SEMESTER!" if student.current_semester == 8 else ""}
- Credits earned: {student.total_credits_earned}/160 (Remaining: {total_remaining_credits})
- GPA: {student.gpa}
- Failed courses: {', '.join(failed_courses) if failed_courses else 'None'}
- Interests: {', '.join(student.interests)}
- Workload preference: {student.workload_preference}
- GPA trend: {gpa_trend}
- Remaining semesters: {remaining_sems}

{project_context}
{project_list}

{future_context}

AVAILABLE COURSES ({len(available_courses)} total):
{json.dumps(courses_data, indent=2)}

COURSE BREAKDOWN:
- Mandatory remaining (DC/FC/DLES): {len(mandatory_remaining)} courses, {mandatory_credits_remaining} credits
- Electives available (DE/OE): {len(electives_available)} courses
- Project courses (PR): {len(project_courses)} courses

CRITICAL CONSTRAINTS (MUST FOLLOW):
1. CREDIT LIMITS: Total credits MUST be >= {min_credits} AND <= {max_credits}
2. Prerequisites must be satisfied
{'3. SLOT CLASHES: Each course has slots (e.g., "A1+A2"). NO two courses can share ANY slot code (A1, A2, etc.)' if not future_semester else '3. Slots not considered (future semester)'}
4. If failed courses exist, at least ONE recommendation MUST include ALL failed courses
{"5. 🎓 SEMESTER 8 CRITICAL: Project 2 (Proj2) MUST be included in ALL THREE recommendations - this is NON-NEGOTIABLE for final semester" if student.current_semester == 8 else ""}
{"5. 🎓 SEMESTER 7 PRIORITY: Project 1 (Proj1) should be included in AT LEAST TWO recommendations to prepare for final year" if student.current_semester == 7 else ""}

RECOMMENDATION STRATEGIES (provide exactly 3):

{"**FOR SEMESTER 8 - ALL STRATEGIES MUST INCLUDE PROJECT 2 (10 CREDITS):**" if student.current_semester == 8 else ""}

STRATEGY 1 - "{'PROJECT + COMPLETION' if student.current_semester >= 7 else 'GRADUATION FOCUSED'}" (Conservative):
{"- **MANDATORY**: Include Project 2 (Proj2 - 10 credits)" if student.current_semester == 8 else ""}
{"- **PRIORITY**: Include Project 1 (Proj1 - 3 credits)" if student.current_semester == 7 else ""}
- Priority: Complete ALL remaining mandatory courses (DC/FC/DLES)
- Include ALL failed courses if any exist
- Minimal electives (only if space permits)
- Target credits: {min_credits}-{min_credits+5}
- Best for: Ensuring graduation {"and project completion" if is_project_semester else ""}on time

STRATEGY 2 - "{'PROJECT + BALANCED' if student.current_semester >= 7 else 'BALANCED APPROACH'}" (Moderate):
{"- **MANDATORY**: Include Project 2 (Proj2 - 10 credits)" if student.current_semester == 8 else ""}
{"- **PRIORITY**: Include Project 1 (Proj1 - 3 credits)" if student.current_semester == 7 else ""}
- Mix mandatory courses with interest-aligned electives
- Include failed courses
- Balance workload based on student preference
- Target credits: {(min_credits+max_credits)//2 - 2}-{(min_credits+max_credits)//2 + 2}
- Best for: Progress + skill development {"+ project work" if is_project_semester else ""}

STRATEGY 3 - "{'PROJECT + SPECIALIZATION' if student.current_semester >= 7 else 'INTEREST ALIGNED'}" (Ambitious):
{"- **MANDATORY**: Include Project 2 (Proj2 - 10 credits)" if student.current_semester == 8 else ""}
{"- **RECOMMENDED**: Include Project 1 (Proj1 - 3 credits)" if student.current_semester == 7 else ""}
- Prioritize electives matching student interests: {', '.join(student.interests)}
- Still include mandatory courses to stay on track
- Include failed courses
- Target credits: {max_credits-5}-{max_credits}
- Best for: Students with strong GPA wanting specialization {"alongside project work" if is_project_semester else ""}

STUDENT CAPACITY ASSESSMENT:
- Strong (GPA > 8.5, no failures): Can handle Strategy 3
- Average (GPA 7-8.5): Strategy 2 recommended, can try Strategy 3
- Weak (GPA < 7 or failures): Strategy 1 strongly recommended

{"⚠️ FINAL SEMESTER OVERRIDE: Regardless of GPA, ALL strategies must prioritize Project 2 completion above all else." if student.current_semester == 8 else ""}

**CRITICAL CREDIT CALCULATION:**
- MUST calculate total_credits by SUMMING exact credit values from AVAILABLE COURSES list
- DO NOT guess credits - lookup each course's credit value above
- Example: ["BCSE301L"(3cr), "BCSE302L"(3cr)] = 6 total_credits
- Verify: {min_credits} <= total_credits <= {max_credits}


{"- CRITICAL FOR SEM 8: Whether student will have enough credits to graduate (must reach 160 total)" if student.current_semester == 8 else ""}

OUTPUT FORMAT (JSON only, no markdown, no extra text):
{{
  "recommendations": [
    {{
      "rank": 1,
      "strategy_name": "{'PROJECT + COMPLETION' if student.current_semester >= 7 else 'GRADUATION FOCUSED'}",
      "courses": [{'"Proj2", "BCSE301L", "BCSE302L"' if student.current_semester == 8 else '"Proj1", "BCSE301L", "BCSE302L", "BMAT301L"' if student.current_semester == 7 else '"BCSE301L", "BCSE302L", "BMAT301L"'}],
      "total_credits": {20 if student.current_semester >= 7 else 18},
      "reasoning": "Overall strategy explanation - why this approach, {'PROJECT EMPHASIS: How project work aligns with remaining courses,' if is_project_semester else ''} graduation timeline impact, workload considerations",
      "course_rationale": {{
        {'"Proj2": "FINAL YEAR PROJECT - Mandatory for graduation, 10 credits dedicated to capstone project work",' if student.current_semester == 8 else ''}
        {'"Proj1": "START OF PROJECT WORK - Essential to begin in Sem 7 to prepare for Proj2 in final semester",' if student.current_semester == 7 else ''}
        "BCSE301L": "Specific reason for including this course",
        "BCSE302L": "Another specific reason"
      }},
      "breakdown": {{
        "mandatory": ["BCSE301L", "BMAT301L"],
        "electives": ["BCSE302L"],
        "failed_courses_included": [],
        {'"project_courses": ["Proj2"]' if student.current_semester == 8 else '"project_courses": ["Proj1"]' if student.current_semester == 7 else '"project_courses": []'}
      }},
      "suitability": "Best for students prioritizing {'project completion and ' if is_project_semester else ''}graduation certainty"{',\n      "slot_assignments": {{"Proj2": "ANY", "BCSE301L": "A1+A2", "BCSE302L": "F1+F2"}}' if not future_semester and student.current_semester == 8 else ',\n      "slot_assignments": {{"BCSE301L": "A1+A2", "BCSE302L": "F1+F2", "BMAT301L": "C1+C2"}}' if not future_semester else ''}
    }},
    {{
      "rank": 2,
      "strategy_name": "{'PROJECT + BALANCED' if student.current_semester >= 7 else 'BALANCED APPROACH'}",
      "courses": [...],
      "total_credits": {22 if student.current_semester >= 7 else 20},
      "reasoning": "...",
      "course_rationale": {{...}},
      "breakdown": {{...}},
      "suitability": "..."{',\n      "slot_assignments": {{...}}' if not future_semester else ''}
    }},
    {{
      "rank": 3,
      "strategy_name": "{'PROJECT + SPECIALIZATION' if student.current_semester >= 7 else 'INTEREST ALIGNED'}",
      "courses": [...],
      "total_credits": {24 if student.current_semester >= 7 else 24},
      "reasoning": "...",
      "course_rationale": {{...}},
      "breakdown": {{...}},
      "suitability": "..."{',\n      "slot_assignments": {{...}}' if not future_semester else ''}
    }}
  ]
}}
"""
        
        return prompt
    
    def _enforce_credit_limits(self, rec: Dict, available_courses: List[Course],
                               min_credits: int, max_credits: int,
                               current_semester: int = None) -> Dict:
        """
        Hard-enforce credit limits on a single recommendation.
        Also strips project courses that don't belong to the current semester.
        """
        course_map = {c.course_code: c for c in available_courses}

        # Strip wrong project courses before any credit math
        codes = rec.get('courses', [])
        if current_semester is not None:
            codes = [c for c in codes if not (c == 'Proj1' and current_semester != 7)]
            codes = [c for c in codes if not (c == 'Proj2' and current_semester != 8)]
        codes = [c for c in codes if c in course_map]

        # Step 1: recalculate from real course objects
        selected = [course_map[c] for c in codes]
        total = sum(c.credits for c in selected)
        rec['total_credits'] = total
        rec['courses'] = codes

        # Step 2: trim if over max — drop OE first, then DE, never drop DC/FC/DLES/PR
        if total > max_credits:
            priority_drop = ['OE', 'DE']
            for drop_type in priority_drop:
                for course in sorted(selected, key=lambda x: x.credits, reverse=True):
                    if total <= max_credits:
                        break
                    if course.type == drop_type:
                        selected.remove(course)
                        total -= course.credits
            rec['courses'] = [c.course_code for c in selected]
            rec['total_credits'] = total

        # Step 3: pad if under min — add mandatory first, then electives
        if total < min_credits:
            already_in = {c.course_code for c in selected}
            candidates = sorted(
                [c for c in available_courses if c.course_code not in already_in],
                key=lambda x: (0 if x.type in ['DC', 'FC', 'DLES'] else 1, x.difficulty)
            )
            for course in candidates:
                if total >= min_credits:
                    break
                if total + course.credits <= max_credits:
                    selected.append(course)
                    total += course.credits
            rec['courses'] = [c.course_code for c in selected]
            rec['total_credits'] = total

        # Step 4: still out of bounds → discard
        if not (min_credits <= total <= max_credits):
            return None

        # Sync breakdown to match adjusted course list
        final_codes = set(rec['courses'])
        if 'breakdown' in rec:
            rec['breakdown']['mandatory'] = [
                c for c in rec['breakdown'].get('mandatory', []) if c in final_codes
            ]
            rec['breakdown']['electives'] = [
                c for c in rec['breakdown'].get('electives', []) if c in final_codes
            ]
            if 'project_courses' in rec['breakdown']:
                rec['breakdown']['project_courses'] = [
                    c for c in rec['breakdown'].get('project_courses', []) if c in final_codes
                ]

        return rec

    def _assess_risk_profile(self, student: StudentProfile) -> str:
        """Assess student's academic risk level"""
        failed = len(student.get_failed_courses())
        gpa = student.gpa
        
        if failed > 2 or gpa < 6.0:
            return "high_risk"
        elif failed > 0 or gpa < 7.5:
            return "medium_risk"
        else:
            return "low_risk"
    
    def analyze_custom_set_feasibility(self, student: StudentProfile, 
                                       selected_courses: List[Course],
                                       all_courses: List[Course],
                                       min_credits: int,
                                       max_credits: int) -> Dict:
        """
        Use LLM to analyze graduation feasibility if custom set is chosen
        """
        # Calculate what's remaining after this selection
        selected_codes = set(c.course_code for c in selected_courses)
        selected_credits = sum(c.credits for c in selected_courses)
        
        passed = set(student.get_passed_courses())
        
        # Simulate completion
        credits_after = student.total_credits_earned + selected_credits
        remaining_credits = 160 - credits_after
        remaining_sems = 8 - student.current_semester
        
        # Get remaining mandatory courses
        remaining_mandatory = []
        for course in all_courses:
            if course.type in ['DC', 'FC', 'DLES']:
                if course.course_code not in passed and course.course_code not in selected_codes:
                    remaining_mandatory.append(course)
        
        mandatory_credits_remaining = sum(c.credits for c in remaining_mandatory)
        
        # Build prompt for AI analysis
        prompt = f"""Analyze graduation feasibility for VIT student.

CURRENT SITUATION:
- Student: {student.name}, Semester {student.current_semester}/8
- Current credits: {student.total_credits_earned}/160
- GPA: {student.gpa}
- Failed courses: {', '.join(student.get_failed_courses())}

PROPOSED SELECTION FOR SEMESTER {student.current_semester}:
Courses: {', '.join([c.course_code for c in selected_courses])}
Total credits: {selected_credits}
Breakdown:
- Mandatory: {', '.join([c.course_code for c in selected_courses if c.type in ['DC', 'FC', 'DLES']])}
- Electives: {', '.join([c.course_code for c in selected_courses if c.type in ['DE', 'OE']])}

AFTER COMPLETING THIS SELECTION:
- Total credits: {credits_after}/160
- Remaining credits needed: {remaining_credits}
- Remaining semesters: {remaining_sems}
- Avg credits/sem needed: {remaining_credits/remaining_sems if remaining_sems > 0 else 0:.1f}

REMAINING MANDATORY COURSES ({len(remaining_mandatory)} courses, {mandatory_credits_remaining} credits):
{', '.join([c.course_code for c in remaining_mandatory])}

CONSTRAINTS:
- Credit limits per semester: {min_credits}-{max_credits}
- Must complete 160 credits in 8 semesters

Provide detailed analysis in JSON format:
{{
  "feasible": true/false,
  "graduation_risk": "none|low|medium|high|critical",
  "summary": "One-sentence verdict",
  "detailed_analysis": "Comprehensive explanation of what happens if this selection is chosen",
  "impact_on_future": "How this affects remaining semesters",
  "recommendations": "Specific advice - what to change or keep in mind",
  "warnings": ["List of specific warnings if any"],
  "positives": ["List of positive aspects of this selection"]
}}

Return ONLY valid JSON, no markdown, no extra text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an academic advisor analyzing graduation feasibility."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                analysis = json.loads(content[json_start:json_end])
            else:
                analysis = json.loads(content)
            
            return analysis
            
        except Exception as e:
            # Fallback to rule-based
            avg_needed = remaining_credits / remaining_sems if remaining_sems > 0 else 0
            
            if avg_needed > max_credits:
                risk = "critical"
                feasible = False
                summary = "Graduation at CRITICAL risk - impossible to complete"
            elif avg_needed > max_credits * 0.9:
                risk = "high"
                feasible = True
                summary = "Very tight schedule - no room for failures"
            elif avg_needed > max_credits * 0.7:
                risk = "medium"
                feasible = True
                summary = "Manageable but tight schedule"
            else:
                risk = "low"
                feasible = True
                summary = "Good pace - graduation likely on time"
            
            return {
                "feasible": feasible,
                "graduation_risk": risk,
                "summary": summary,
                "detailed_analysis": f"Need {avg_needed:.1f} credits/sem for remaining {remaining_sems} semesters.",
                "impact_on_future": f"{mandatory_credits_remaining} mandatory credits still needed.",
                "recommendations": "Consider including more mandatory courses." if not feasible else "Stay on track.",
                "warnings": [f"Need {avg_needed:.1f} credits/sem"] if not feasible else [],
                "positives": ["Good selection"] if feasible else []
            }
    
    def _create_fallback_recommendations(self, available_courses: List[Course], 
                                        min_credits: int, max_credits: int,
                                        is_project_semester: bool = False) -> Dict:
        """Create simple fallback recommendations when LLM fails"""
        
        # Separate courses by type
        mandatory = [c for c in available_courses if c.type in ['DC', 'FC', 'DLES']]
        electives = [c for c in available_courses if c.type in ['DE', 'OE']]
        projects = [c for c in available_courses if c.type == 'PR']
        
        recommendations = []
        
        # Recommendation 1: Conservative (mandatory focus + projects if semester 7/8)
        rec1_courses = []
        rec1_credits = 0
        
        # Add projects first if project semester
        if is_project_semester and projects:
            for proj in sorted(projects, key=lambda x: x.credits, reverse=True):
                if rec1_credits + proj.credits <= max_credits:
                    rec1_courses.append(proj)
                    rec1_credits += proj.credits
        
        # Add mandatory courses
        for course in sorted(mandatory, key=lambda x: x.difficulty):
            if rec1_credits + course.credits <= max_credits:
                rec1_courses.append(course)
                rec1_credits += course.credits
            if rec1_credits >= min_credits:
                break
        
        if rec1_credits >= min_credits:
            recommendations.append({
                "rank": 1,
                "strategy_name": "PROJECT + COMPLETION" if is_project_semester else "GRADUATION FOCUSED",
                "courses": [c.course_code for c in rec1_courses],
                "total_credits": rec1_credits,
                "reasoning": f"Conservative approach focusing on {'project work and ' if is_project_semester else ''}mandatory courses",
                "breakdown": {
                    "mandatory": [c.course_code for c in rec1_courses if c.type in ['DC', 'FC', 'DLES']],
                    "electives": [c.course_code for c in rec1_courses if c.type in ['DE', 'OE']],
                    "project_courses": [c.course_code for c in rec1_courses if c.type == 'PR'],
                    "failed_courses_included": []
                },
                "suitability": f"Best for {'final year students completing projects and ' if is_project_semester else ''}ensuring graduation"
            })
        
        return {"recommendations": recommendations}
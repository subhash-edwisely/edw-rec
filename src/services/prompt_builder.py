"""
Modular Prompt Builder for Course Recommendations
Direct, personal tone - speaks TO the student, not ABOUT them
Includes enriched future semester projections with mandatory project enforcement
"""
import json
from typing import List, Dict, Optional


class PromptBuilder:
    """Modular prompt construction with personalized, direct messaging"""
    
    def __init__(self):
        pass
    
    def build_system_message(self) -> str:
        """Build system message that sets direct, personal tone"""
        
        return """You are a friendly, supportive academic advisor helping a VIT student plan their semester.

**YOUR COMMUNICATION STYLE:**
- Speak DIRECTLY to the student using "you", "your" - NEVER third person
- Be encouraging and supportive, not clinical or robotic
- Explain WHY each course matters to THEM personally
- Sound like a mentor who cares about their success

**TONE EXAMPLES:**
❌ WRONG: "Student should take BCSE301L because it's mandatory for graduation"
✅ RIGHT: "You should take BCSE301L - it's required for your graduation and it unlocks advanced AI courses you're interested in"

❌ WRONG: "This course aligns with the student's interests in AI"
✅ RIGHT: "Since you're passionate about AI, this course will give you hands-on experience with neural networks"

❌ WRONG: "Completing these courses will leave X credits for the student"
✅ RIGHT: "After this semester, you'll have just X credits left - totally doable!"

❌ WRONG: "The student has failed BCSE205L"
✅ RIGHT: "You need to retake BCSE205L since it didn't go well last semester - let's get it cleared this time"

Remember: You're ADVISING them personally, not writing a report ABOUT them."""
    
    def build_student_greeting(self, student, 
                               remaining_sems: int,
                               total_remaining: int) -> str:
        """Build personalized greeting based on student's situation"""
        
        # Personalized greeting based on semester
        if student.current_semester == 8:
            greeting = "🎓 **Welcome to your FINAL semester!** This is it - let's make sure you cross that finish line successfully."
        elif student.current_semester == 7:
            greeting = "🎯 **You're in your final year!** Time to plan strategically so next semester is smooth sailing."
        elif student.current_semester <= 3:
            greeting = "📚 **Welcome!** You're still building your foundation - let's make smart choices that set you up for success."
        else:
            greeting = "📊 **You're halfway there!** Let's optimize your path and make these remaining semesters count."
        
        return greeting
    
    def build_student_context(self, student,
                             remaining_sems: int,
                             total_remaining: int) -> str:
        """Build personalized student context section"""
        
        failed_courses = student.get_failed_courses()
        
        context = self.build_student_greeting(student, remaining_sems, total_remaining)
        
        context += f"""

**HERE'S WHERE YOU STAND:**
- You've completed **{student.total_credits_earned} out of 160 credits** (that's {(student.total_credits_earned/160*100):.1f}%!)
- You have **{total_remaining} credits remaining** to graduate
- Your current GPA is **{student.gpa}**
- You have **{remaining_sems} semesters left** including this one
- You're interested in: {', '.join(student.interests)}
- Your preferred workload: **{student.workload_preference}**
"""
        
        # Add failed courses section with empathy
        if failed_courses:
            context += f"""
⚠️ **COURSES TO CLEAR:**
You didn't pass {len(failed_courses)} course(s) previously: **{', '.join(failed_courses)}**
Let's prioritize clearing these - they're blocking your progress and need attention.
"""
        
        # Add GPA-based encouragement
        if student.gpa >= 9.0:
            context += "\n✨ **Wow!** Your outstanding GPA gives you the flexibility to take on challenging electives and explore advanced topics!\n"
        elif student.gpa >= 8.5:
            context += "\n🌟 **Excellent work!** Your strong GPA means you can balance core requirements with interesting electives.\n"
        elif student.gpa >= 7.0:
            context += "\n💪 **Solid performance!** You're on track - let's keep the momentum going with a balanced approach.\n"
        else:
            context += "\n📈 **Let's build momentum together!** I'll focus on giving you an achievable workload that builds your confidence.\n"
        
        return context
    
    def build_semester_guidance(self, semester: int,
                               project_courses: List,
                               max_credits: int) -> str:
        """Build semester-specific strategic advice"""
        
        if semester == 8:
            return f"""
🚨 **FINAL SEMESTER - CRITICAL REQUIREMENTS:**

This is your last chance to graduate, so here's what you MUST do:
- **Include your final year project** (typically Project 2, around 10 credits) - this is NON-NEGOTIABLE
- Complete ANY remaining mandatory courses - you can't graduate without them
- Forget about new electives unless you have extra room
- Stay focused - with your project taking 10 credits, you have about {max_credits - 10} credits left for other courses

Every course you register for must directly contribute to graduation. No experimentation this semester!
"""
        elif semester == 7:
            project_info = ""
            if any(c for c in project_courses if 'Proj1' in c.course_code or 'Project 1' in c.name):
                project_info = """
**Project 1 is available!** I strongly recommend starting it now:
- It's only 3 credits but prerequisite for Project 2 next semester
- Starting early gives you breathing room in your final semester
- You don't want to cram Project 2 with other courses in semester 8
"""
            
            return f"""
📋 **FINAL YEAR PREPARATION - THINK AHEAD:**

You're setting yourself up for next semester, so let's be strategic:
- Clear as many mandatory courses as you can NOW{project_info}
- Leave yourself with a manageable workload for semester 8
- Think about what you DON'T want to deal with during your final project semester

Your goal: Make semester 8 as stress-free as possible.
"""
        elif semester <= 3:
            return """
🌱 **BUILDING YOUR FOUNDATION:**

Early semesters are about:
- Completing foundational courses (FC) - these unlock everything that comes later
- Don't rush or overload - build solid fundamentals first
- Passing courses on the first attempt saves you headaches later

Think of this as laying the groundwork for your entire degree.
"""
        else:
            return """
⚖️ **MID-PROGRAM SWEET SPOT:**

You're in the zone where you can:
- Balance mandatory discipline cores with electives you actually care about
- Start exploring specialization areas that interest you
- Build prerequisites for advanced courses you want to take later

This is your chance to shape your degree toward your interests.
"""
    
    def build_course_availability(self, mandatory_courses: List,
                                  electives: List,
                                  projects: List) -> str:
        """Build course availability section"""
        
        mandatory_credits = sum(c.credits for c in mandatory_courses)
        
        section = f"""
**HERE'S WHAT'S AVAILABLE TO YOU THIS SEMESTER:**

📚 **Mandatory Courses:** {len(mandatory_courses)} courses ({mandatory_credits} credits total)
   - These are required for graduation - you'll need to take them eventually
   
🎯 **Elective Courses:** {len(electives)} courses  
   - Pick ones that match your interests: choose wisely!
"""
        
        if projects:
            section += f"""   
🎓 **Project Courses:** {len(projects)} courses
   - Your capstone work - typically for final year
"""
        
        return section
    
    def build_credit_limits(self, min_credits: int, max_credits: int) -> str:
        """Build credit constraints explanation"""
        
        sweet_spot = (min_credits + max_credits) // 2
        
        return f"""
**CREDIT LIMITS YOU NEED TO FOLLOW:**

📊 **Minimum:** {min_credits} credits - you must register for at least this much
📊 **Maximum:** {max_credits} credits - VIT won't let you register for more
💡 **Sweet Spot:** Around {sweet_spot} credits - a balanced, manageable workload

I'll give you options ranging from conservative ({min_credits}-ish) to ambitious ({max_credits}-ish).
"""
    
    def build_strategy_intro(self, student,
                            min_credits: int, max_credits: int) -> str:
        """Build introduction to the 3 strategies"""
        
        failed = student.get_failed_courses()
        
        # Personalized recommendation
        if student.gpa >= 8.5 and not failed:
            my_recommendation = "**My recommendation:** Go for Strategy 3 - your excellent performance means you can handle it!"
        elif student.gpa >= 7.0:
            my_recommendation = "**My recommendation:** Strategy 2 is your sweet spot - keeps you on track while building skills."
        else:
            my_recommendation = "**My recommendation:** Stick with Strategy 1 - let's focus on graduation certainty first."
        
        intro = f"""
**I'M GIVING YOU 3 DIFFERENT APPROACHES TO CHOOSE FROM:**

Each strategy has a different priority and credit load. Pick the one that matches your current situation and goals.

{my_recommendation}
"""
        
        return intro
    
    def build_strategy_details(self, semester: int,
                               interests: List[str],
                               failed_courses: List[str],
                               min_credits: int,
                               max_credits: int,
                               is_project_semester: bool) -> str:
        """Build detailed strategy descriptions"""
        
        mid_credits = (min_credits + max_credits) // 2
        
        # Adjust for project semesters
        if semester == 8:
            s1_name = "PROJECT + COMPLETION"
            s2_name = "PROJECT + BALANCED"
            s3_name = "PROJECT + SPECIALIZATION"
            project_note = " (remember: 10 credits go to your project)"
        elif semester == 7:
            s1_name = "GRADUATION FOCUSED + PROJECT PREP"
            s2_name = "BALANCED + PROJECT START"
            s3_name = "INTEREST-DRIVEN + PROJECT"
            project_note = ""
        else:
            s1_name = "GRADUATION FOCUSED"
            s2_name = "BALANCED APPROACH"
            s3_name = "INTEREST ALIGNED"
            project_note = ""
        
        failed_note = f"\n   - **Must clear:** {', '.join(failed_courses)}" if failed_courses else ""
        
        strategies = f"""
**STRATEGY 1: {s1_name}** (Conservative: {min_credits}-{min_credits+5} credits{project_note})
   - **Priority:** Complete ALL your remaining mandatory courses first
   {failed_note}
   - Include electives only if there's room
   {"- Include your final project (10 credits)" if semester == 8 else ""}
   {"- Consider starting Project 1 (3 credits)" if semester == 7 else ""}
   - **Best for:** You want guaranteed graduation with minimal risk

**STRATEGY 2: {s2_name}** (Moderate: {mid_credits-2}-{mid_credits+2} credits{project_note})
   - **Priority:** Mix mandatory courses with electives matching your interests: {', '.join(interests)}
   {failed_note}
   - Balance progress with skill development
   {"- Include your final project (10 credits)" if semester == 8 else ""}
   {"- Include Project 1 (3 credits)" if semester == 7 else ""}
   - **Best for:** You want steady progress while building relevant skills

**STRATEGY 3: {s3_name}** (Ambitious: {max_credits-5}-{max_credits} credits{project_note})
   - **Priority:** Focus on electives in: {', '.join(interests)}
   - Still cover mandatory courses to stay on track
   {failed_note}
   {"- Include your final project (10 credits)" if semester == 8 else ""}
   {"- Consider Project 1 (3 credits)" if semester == 7 else ""}
   - **Best for:** You have a strong GPA and want to specialize/explore interests
"""
        
        # Special override for semester 8
        if semester == 8:
            strategies += """
⚠️ **IMPORTANT NOTE:** Since this is your final semester, ALL three strategies MUST include your final project. 
The difference is just what OTHER courses you take alongside it.
"""
        
        return strategies
    
    def build_rules(self, min_credits: int, max_credits: int,
                   failed_courses: List[str], has_slots: bool,
                   semester: int) -> str:
        """Build constraint rules in direct language"""
        
        rules = f"""
**RULES YOU MUST FOLLOW (NON-NEGOTIABLE):**

✅ **Credit Limits:** Your total must be between {min_credits} and {max_credits} credits - no exceptions
✅ **Prerequisites:** You can only take courses where you've completed the required prerequisites
"""
        
        if has_slots:
            rules += """✅ **NO SLOT CLASHES (CRITICAL FOR VIT FFCS):**
   - Each course has time slots like "A1+A2+L1+L2" or "B1+B2+TB1+TB2"
   - If ANY two courses share even ONE slot letter, they CLASH
   - Example: Course A has "A1+A2" and Course B has "A1+B1" → CLASH (both use A1)
   - Example: Course C has "F1+F2" and Course D has "G1+G2" → NO CLASH (no common slots)
   - You MUST check EVERY pair of courses for slot overlap
   - Parse slots carefully: "A1+A2+L1+L2" means slots A1, A2, L1, L2
   - Before finalizing ANY recommendation, verify NO two courses share any slot
"""
        
        if failed_courses:
            rules += f"""⚠️ **Clear Failed Courses:** At least ONE of my recommendations MUST include all your failed courses: {', '.join(failed_courses)}
"""
        
        if semester == 8:
            rules += """🎓 **FINAL PROJECT MANDATORY:** Your final year project (Project 2) MUST be in ALL three recommendations - you can't graduate without it
"""
        elif semester == 7:
            rules += """🎓 **PROJECT RECOMMENDED:** I'll try to include Project 1 in at least two recommendations to prepare you for semester 8
"""
        
        return rules
    
    def build_credit_calculation_guide(self, min_credits: int, max_credits: int) -> str:
        """Build credit calculation instructions"""
        
        return f"""
**HOW I CALCULATE CREDITS (IMPORTANT!):**

I will:
1. Look up EACH course's credit value from the course list provided
2. Add them ALL up - no guessing, no rounding
3. Verify the total is between {min_credits} and {max_credits}
4. Show you my math

Example: If I recommend BCSE301L (3cr) + BCSE302L (3cr) + BMAT301L (4cr), 
my total_credits will be: 3 + 3 + 4 = 10 credits
"""
    
    def build_output_format(self, has_slots: bool) -> str:
        """Build JSON output format"""
        
        slot_example = ',\n      "slot_assignments": {"BCSE301L": "A1+A2", "BCSE302L": "F1+F2"}' if has_slots else ''
        
        slot_validation_note = ""
        if has_slots:
            slot_validation_note = """

**CRITICAL SLOT VALIDATION CHECKLIST (DO THIS BEFORE FINALIZING):**
For each recommendation, verify:
1. Parse ALL slots: "A1+A2+L1" → [A1, A2, L1]
2. Check EVERY pair of courses for ANY common slot
3. If ANY overlap found → REJECT that combination
4. Example validation:
   - BCSE301L has "A1+A2" → slots: [A1, A2]
   - BCSE302L has "F1+F2" → slots: [F1, F2]
   - Check overlap: [A1, A2] ∩ [F1, F2] = [] → ✅ NO CLASH
   - BCSE303L has "A1+B1" → slots: [A1, B1]
   - Check with BCSE301L: [A1, A2] ∩ [A1, B1] = [A1] → ❌ CLASH!
"""
        
        return f"""
**RESPONSE FORMAT (JSON):**
{{
  "recommendations": [
    {{
      "rank": 1,
      "strategy_name": "GRADUATION FOCUSED",
      "courses": ["BCSE301L", "BCSE302L"],
      "total_credits": 6,
      "reasoning": "Here's why I recommend this combination for you...",
      "course_rationale": {{
        "BCSE301L": "You need this because... (explain personally)",
        "BCSE302L": "This helps you because... (explain personally)"
      }},
      "breakdown": {{
        "mandatory": ["BCSE301L"],
        "electives": ["BCSE302L"],
        "failed_courses_included": []
      }},
      "suitability": "This works best for you if..."{slot_example}
    }},
    ... (strategies 2 and 3)
  ]
}}
{slot_validation_note}"""
    
    def build_complete_prompt(self, student,
                             available_courses: List,
                             min_credits: int, max_credits: int,
                             future_semester: bool = False,
                             assumed_passed: Optional[List[str]] = None,
                             is_project_semester: bool = False) -> Dict[str, str]:
        """
        Build complete modular prompt with direct, personal tone
        Returns: {"system": system_message, "user": user_prompt}
        """
        
        # Calculate context
        remaining_sems = 8 - student.current_semester
        total_remaining = 160 - student.total_credits_earned
        failed = student.get_failed_courses()
        
        # Categorize courses
        mandatory = [c for c in available_courses if c.type in ['DC', 'FC', 'DLES']]
        electives = [c for c in available_courses if c.type in ['DE', 'OE']]
        projects = [c for c in available_courses if c.type == 'PR']
        
        # Format course data
        courses_json = json.dumps([
            {
                'code': c.course_code,
                'name': c.name,
                'credits': c.credits,
                'type': c.type,
                'prerequisites': c.prerequisites,
                'difficulty': c.difficulty,
                'slots': c.slots if not future_semester else None
            }
            for c in available_courses
        ], indent=2)
        
        # Build user prompt from modular sections
        sections = []
        
        # 1. Student greeting and context
        sections.append(self.build_student_context(
            student, remaining_sems, total_remaining
        ))
        
        # 2. Semester-specific guidance
        sections.append(self.build_semester_guidance(
            student.current_semester, projects, max_credits
        ))
        
        # 3. Course availability
        sections.append(self.build_course_availability(
            mandatory, electives, projects
        ))
        
        # 4. Available courses list
        sections.append(f"\n**FULL COURSE LIST ({len(available_courses)} courses):**\n{courses_json}\n")
        
        # 5. Credit limits
        sections.append(self.build_credit_limits(min_credits, max_credits))
        
        # 6. Strategy introduction
        sections.append(self.build_strategy_intro(student, min_credits, max_credits))
        
        # 7. Strategy details
        sections.append(self.build_strategy_details(
            student.current_semester, student.interests, failed,
            min_credits, max_credits, is_project_semester
        ))
        
        # 8. Rules
        sections.append(self.build_rules(
            min_credits, max_credits, failed, not future_semester, student.current_semester
        ))
        
        # 9. Credit calculation guide
        sections.append(self.build_credit_calculation_guide(min_credits, max_credits))
        
        # 10. Output format
        sections.append(self.build_output_format(not future_semester))
        
        # Combine all sections
        user_prompt = "\n".join(sections)
        
        return {
            "system": self.build_system_message(),
            "user": user_prompt
        }
    
    def build_future_semester_context(self, 
                                     current_semester: int,
                                     target_semester: int,
                                     assumed_completed: List[str],
                                     simulated_credits: int,
                                     remaining_credits: int,
                                     remaining_mandatory: List) -> str:
        """Build rich context for future semester projections"""
        
        semesters_away = target_semester - current_semester
        mandatory_credits = sum(c.credits for c in remaining_mandatory)
        
        context = f"""
🔮 **FUTURE PROJECTION: SEMESTER {target_semester}**

**THIS IS A SIMULATION:**
I'm planning ahead for your semester {target_semester} based on the assumption that you'll pass all recommended courses in the semesters before it.

**ASSUMPTIONS I'M MAKING:**
"""
        
        # Generic: describe how many semesters of courses are assumed completed
        if semesters_away == 1:
            context += f"""
✅ **Semester {current_semester} (your current semester):** You'll complete these {len(assumed_completed)} courses successfully:
   {', '.join(assumed_completed)}
"""
        elif semesters_away == 2:
            mid = len(assumed_completed) // 2
            sem_a_courses = assumed_completed[:mid] or assumed_completed
            sem_b_courses = assumed_completed[mid:] if mid < len(assumed_completed) else []
            context += f"""
✅ **Semester {current_semester}:** You'll pass: {', '.join(sem_a_courses[:4])}{'...' if len(sem_a_courses) > 4 else ''} ({len(sem_a_courses)} total)
✅ **Semester {current_semester + 1}:** You'll pass: {', '.join(sem_b_courses[:4])}{'...' if len(sem_b_courses) > 4 else ''} ({len(sem_b_courses)} total)
"""
        else:
            context += f"""
✅ **Semesters {current_semester} through {target_semester - 1}:** You'll successfully complete all recommended courses.
   Total assumed completed: {len(assumed_completed)} courses across {semesters_away} semesters.
"""
        
        context += f"""

**WHERE YOU'LL BE BY SEMESTER {target_semester}:**
- Credits completed: {simulated_credits}/160
- Credits remaining: {remaining_credits}
- Mandatory courses left: {len(remaining_mandatory)} courses ({mandatory_credits} credits)
- Semesters to graduation: {8 - target_semester + 1}
"""
        
        # Add semester-specific guidance
        if target_semester == 7:
            context += """

🎓 **SEMESTER 7 - PROJECT PREPARATION CRITICAL:**
This is NOT just another semester - this is your final year preparation phase!

**YOU MUST START PROJECT 1 NOW:**
- Project 1 (typically 3 credits) is MANDATORY for this semester
- It's a prerequisite for Project 2 in semester 8
- Starting it now gives you breathing room for your final semester
- ALL my recommendations will include Project 1 - this is non-negotiable

**Why this matters:**
If you skip Project 1 now, you'll have to cram it into semester 8 alongside 
Project 2 (10 credits) + remaining mandatory courses = disaster!
"""
        elif target_semester == 8:
            context += """

🚨 **FINAL SEMESTER - GRADUATION MODE:**
This is it - your LAST semester! Everything you do must lead to graduation.

**PROJECT 2 IS MANDATORY:**
- Project 2 (typically 10 credits) MUST be in every recommendation
- This is your final year capstone - you cannot graduate without it
- It will consume most of your time and credits
- ALL strategies will include Project 2 - this is absolute

**What else you need:**
- ANY remaining mandatory courses (you can't skip these)
- Minimal completion courses if you have credit gaps
- ZERO new electives unless you're ahead on credits

**Your only goal:** Cross the finish line and graduate!
"""
        else:
            context += f"""

**PLANNING AHEAD STRATEGY:**
Since semester {target_semester} is {semesters_away} semester(s) away, I'm being strategic:
- Clear as many mandatory courses as possible NOW
- Leave room for interesting electives aligned with your goals
- Build prerequisites for advanced courses you'll want later
- Keep graduation requirements on track
"""
        
        return context

    def build_future_unlocked_courses_explanation(self,
                                                  assumed_completed: List[str],
                                                  newly_available: List,
                                                  all_available: List) -> str:
        """Explain what courses are newly unlocked"""
        
        # Find courses that have prerequisites in assumed_completed
        unlocked = []
        for course in newly_available:
            for prereq in course.prerequisites:
                if prereq in assumed_completed:
                    unlocked.append(course)
                    break
        
        if not unlocked:
            return ""
        
        explanation = f"""
**🔓 NEWLY UNLOCKED COURSES:**
By completing your previous semester courses, you've unlocked {len(unlocked)} new courses:
"""
        
        for course in unlocked[:5]:  # Show first 5
            prereqs = [p for p in course.prerequisites if p in assumed_completed]
            explanation += f"\n- **{course.course_code}** ({course.name}) - unlocked because you'll have completed {', '.join(prereqs)}"
        
        if len(unlocked) > 5:
            explanation += f"\n- ... and {len(unlocked) - 5} more courses"
        
        return explanation

    def build_future_graduation_feasibility(self,
                                            target_semester: int,
                                            simulated_credits: int,
                                            remaining_mandatory_credits: int,
                                            min_credits: int,
                                            max_credits: int) -> str:
        """Assess and explain graduation feasibility"""
        
        remaining_credits = 160 - simulated_credits
        remaining_sems = 8 - target_semester + 1
        avg_needed = remaining_credits / remaining_sems if remaining_sems > 0 else 0
        avg_mandatory_needed = remaining_mandatory_credits / remaining_sems if remaining_sems > 0 else 0
        
        feasibility = """
**📊 GRADUATION FEASIBILITY CHECK:**
"""
        
        if avg_needed > max_credits:
            feasibility += f"""
🚨 **CRITICAL WARNING:** 
- You need {avg_needed:.1f} credits per semester on average
- Maximum allowed is {max_credits} credits per semester
- **GRADUATION AT RISK** - You're behind schedule!
- You MUST take maximum credits every remaining semester
- Consider summer courses if available
- Talk to your advisor about options
"""
        elif avg_needed > max_credits * 0.85:
            feasibility += f"""
⚠️ **TIGHT SCHEDULE:**
- You need {avg_needed:.1f} credits per semester on average
- That's {(avg_needed/max_credits*100):.0f}% of maximum capacity
- You have NO room for failures
- Must take heavy loads every semester
- Stay focused - this is doable but demanding
"""
        elif avg_needed > max_credits * 0.6:
            feasibility += f"""
✅ **ON TRACK:**
- You need {avg_needed:.1f} credits per semester on average
- This is manageable - right in the sweet spot
- You have some buffer for flexibility
- Stick to the plan and you'll graduate on time
"""
        else:
            feasibility += f"""
🌟 **COMFORTABLE PACE:**
- You only need {avg_needed:.1f} credits per semester
- You're ahead of schedule - great job!
- You can afford to take lighter loads
- Room to explore interesting electives
"""
        
        # Add mandatory course pressure
        feasibility += f"""

**Mandatory Course Pressure:**
- {remaining_mandatory_credits} mandatory credits still needed
- Averages to {avg_mandatory_needed:.1f} mandatory credits per semester
- You need to balance these with electives
"""
        
        return feasibility

    def build_future_strategic_recommendations(self,
                                              target_semester: int,
                                              student_interests: List[str],
                                              has_project_courses: bool) -> str:
        """Build strategic recommendations specific to future semester"""
        
        if target_semester == 8:
            return """
**MY STRATEGIC ADVICE FOR SEMESTER 8:**

1. **Project 2 First:** This is your #1 priority - everything else is secondary
2. **Clear Mandatory Backlog:** Any mandatory courses you haven't finished - DO THEM NOW
3. **No Experimenting:** This is NOT the time to try new things
4. **Focus on Completion:** Every course must directly lead to graduation
5. **Attendance Matters:** You can't afford to fail anything this semester

**What NOT to do:**
- ❌ Take courses "just for interest" that don't count toward graduation
- ❌ Overload yourself beyond your project capacity
- ❌ Skip any remaining mandatory courses
"""
        elif target_semester == 7:
            return f"""
**MY STRATEGIC ADVICE FOR SEMESTER 7:**

1. **Start Project 1:** Don't postpone this - you'll thank yourself in semester 8
2. **Clear Mandatory Cores:** Finish as many DC courses as possible
3. **Strategic Electives:** Pick 1-2 electives in {', '.join(student_interests[:2])} that you actually care about
4. **Lighten Semester 8:** Every mandatory course you clear now is one less headache later
5. **Build Prerequisites:** Make sure you have everything needed for semester 8 courses

**What to prioritize:**
- ✅ Project 1 (3 credits) - MUST include
- ✅ Remaining mandatory cores (2-3 courses)
- ✅ One meaningful elective aligned with your interests
"""
        else:
            return f"""
**MY STRATEGIC ADVICE FOR SEMESTER {target_semester}:**

1. **Balance Mandatory & Interests:** Mix required courses with electives in {', '.join(student_interests[:2])}
2. **Think Ahead:** Take courses that unlock advanced topics you want
3. **Maintain GPA:** Don't overload - quality over quantity
4. **Build Skills:** Choose electives that develop practical abilities
5. **Stay on Track:** Keep graduation requirements moving forward
"""

    def build_future_complete_prompt(self, 
                                    student,
                                    available_courses: List,
                                    min_credits: int, 
                                    max_credits: int,
                                    target_semester: int,
                                    assumed_completed: List[str],
                                    simulated_credits: int) -> Dict[str, str]:
        """
        Build enriched prompt for future semester projections
        """
        
        # Calculate context
        remaining_credits = 160 - simulated_credits
        failed = student.get_failed_courses()
        
        # Categorize courses
        mandatory = [c for c in available_courses if c.type in ['DC', 'FC', 'DLES']]
        electives = [c for c in available_courses if c.type in ['DE', 'OE']]
        projects = [c for c in available_courses if c.type == 'PR']
        
        # Check for mandatory projects
        has_proj1 = any('Proj1' in c.course_code or 'Project 1' in c.name for c in available_courses)
        has_proj2 = any('Proj2' in c.course_code or 'Project 2' in c.name for c in available_courses)
        
        # Format course data
        courses_json = json.dumps([
            {
                'code': c.course_code,
                'name': c.name,
                'credits': c.credits,
                'type': c.type,
                'prerequisites': c.prerequisites,
                'difficulty': c.difficulty
            }
            for c in available_courses
        ], indent=2)
        
        # Build sections
        sections = []
        
        # 1. Future semester context
        sections.append(self.build_future_semester_context(
            student.current_semester, target_semester, assumed_completed,
            simulated_credits, remaining_credits, mandatory
        ))
        
        # 2. Unlocked courses explanation
        sections.append(self.build_future_unlocked_courses_explanation(
            assumed_completed, available_courses, available_courses
        ))
        
        # 3. Graduation feasibility
        sections.append(self.build_future_graduation_feasibility(
            target_semester, simulated_credits, sum(c.credits for c in mandatory),
            min_credits, max_credits
        ))
        
        # 4. Available courses
        sections.append(f"""
**AVAILABLE COURSES FOR SEMESTER {target_semester}:**
({len(available_courses)} total courses)

{courses_json}
""")
        
        # 5. Strategic recommendations
        sections.append(self.build_future_strategic_recommendations(
            target_semester, student.interests, len(projects) > 0
        ))
        
        # 6. Mandatory project enforcement
        if target_semester == 7 and has_proj1:
            sections.append("""
**🎓 PROJECT 1 ENFORCEMENT:**
Since this is semester 7, I MUST include Project 1 in ALL three recommendations.
This is not optional - it's required for graduation planning.
""")
        elif target_semester == 8 and has_proj2:
            sections.append("""
**🚨 PROJECT 2 ENFORCEMENT:**
Since this is semester 8 (FINAL), I MUST include Project 2 in ALL three recommendations.
Without Project 2, you CANNOT graduate. This is absolute.
""")
        
        # 7. Standard rules
        sections.append(self.build_rules(
            min_credits, max_credits, failed, False, target_semester
        ))
        
        # 8. Credit calculation
        sections.append(self.build_credit_calculation_guide(min_credits, max_credits))
        
        # 9. Output format
        sections.append(self.build_output_format(False))
        
        # Combine
        user_prompt = "\n".join(sections)
        
        # Enhanced system message for future semesters
        system_message = """You are a strategic academic advisor helping a VIT student plan FUTURE semesters.

**CRITICAL DIFFERENCES FROM CURRENT SEMESTER PLANNING:**
- This is a PROJECTION - courses are based on assumptions
- Be clear about what you're assuming (e.g., "assuming you pass X and Y")
- Focus on strategic planning, not just immediate needs
- Consider how each choice affects graduation timeline

**MANDATORY PROJECT RULES:**
- Semester 7: Project 1 MUST be in ALL recommendations
- Semester 8: Project 2 MUST be in ALL recommendations
- These are ABSOLUTE requirements - no exceptions

**YOUR TONE:**
- Use future tense: "You'll need...", "You should plan to..."
- Acknowledge uncertainty: "If you complete X, then Y becomes available"
- Be strategic: Explain how choices now affect later semesters
- Still use "you/your" (direct), not "student" (third person)

Remember: You're helping them plan ahead, so explain the cascading effects of their choices."""
        
        return {
            "system": system_message,
            "user": user_prompt
        }
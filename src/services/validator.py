from typing import List, Dict, Set
from src.models.course import Course
from src.models.student import StudentProfile

class Validator:
    """Validate course selections against constraints"""
    
    def __init__(self, min_credits: int = 16, max_credits: int = 27):
        self.min_credits = min_credits
        self.max_credits = max_credits
    
    def set_credit_limits(self, min_credits: int, max_credits: int):
        """Update credit limits"""
        self.min_credits = min_credits
        self.max_credits = max_credits
    
    def check_slot_clashes(self, courses: List[Course], 
                          slot_assignments: Dict[str, str]) -> tuple[bool, List[str]]:
        """
        Check for slot clashes in selected courses
        slot_assignments: {course_code: chosen_slot}
        Returns: (valid, clash_messages)
        """
        slot_usage = {}
        clashes = []
        
        for course in courses:
            if course.course_code not in slot_assignments:
                continue
            
            chosen_slot = slot_assignments[course.course_code]
            
            # Parse slot (e.g., "A1+A2" -> ["A1", "A2"])
            slot_parts = chosen_slot.split('+')
            
            for slot in slot_parts:
                if slot in slot_usage:
                    clashes.append(
                        f"Slot clash: {slot} used by both {course.course_code} "
                        f"and {slot_usage[slot]}"
                    )
                else:
                    slot_usage[slot] = course.course_code
        
        return len(clashes) == 0, clashes
    
    def check_credit_bounds(self, courses: List[Course]) -> tuple[bool, List[str]]:
        """Check if total credits are within bounds"""
        total_credits = sum(c.credits for c in courses)
        errors = []
        
        if total_credits < self.min_credits:
            errors.append(
                f"Total credits ({total_credits}) below minimum ({self.min_credits})"
            )
        if total_credits > self.max_credits:
            errors.append(
                f"Total credits ({total_credits}) exceed maximum ({self.max_credits})"
            )
        
        return len(errors) == 0, errors
    
    def check_prerequisites(self, courses: List[Course], 
                          student: StudentProfile) -> tuple[bool, List[str]]:
        """Check if all prerequisites are satisfied"""
        passed = set(student.get_passed_courses())
        errors = []
        
        for course in courses:
            for prereq in course.prerequisites:
                if prereq not in passed:
                    errors.append(
                        f"{course.course_code} requires {prereq} (not completed)"
                    )
        
        return len(errors) == 0, errors
    
    def validate_selection(self, courses: List[Course], 
                          slot_assignments: Dict[str, str],
                          student: StudentProfile) -> Dict:
        """
        Comprehensive validation
        Returns: {valid: bool, errors: [], warnings: []}
        """
        errors = []
        warnings = []
        
        # Check prerequisites
        prereq_valid, prereq_errors = self.check_prerequisites(courses, student)
        errors.extend(prereq_errors)
        
        # Check slot clashes
        slots_valid, slot_errors = self.check_slot_clashes(courses, slot_assignments)
        errors.extend(slot_errors)
        
        # Check credit bounds
        credits_valid, credit_errors = self.check_credit_bounds(courses)
        errors.extend(credit_errors)
        
        # Check graduation feasibility (warning only)
        feasibility_analysis = self.analyze_graduation_feasibility(student, courses)
        if not feasibility_analysis['feasible']:
            warnings.extend(feasibility_analysis['warnings'])
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'feasibility': feasibility_analysis
        }
    
    def analyze_graduation_feasibility(self, student: StudentProfile, 
                                      current_selection: List[Course],
                                      all_courses: List[Course] = None) -> Dict:
        """
        Analyze if student can graduate on time with current selection
        Returns: {feasible: bool, warnings: [], details: {}}
        """
        warnings = []
        
        # Calculate remaining mandatory credits
        passed = set(student.get_passed_courses())
        selected = set(c.course_code for c in current_selection)
        
        # Count completed + selected mandatory credits
        completed_mandatory_credits = 0
        for sem in student.semester_results:
            for course_result in sem.courses:
                if course_result.status == "passed":
                    completed_mandatory_credits += course_result.credits
        
        selected_mandatory_credits = sum(
            c.credits for c in current_selection 
            if c.type in ['DC', 'FC', 'DLES'] and c.course_code not in passed
        )
        
        # Estimate remaining mandatory credits (assuming 120 out of 160 are mandatory)
        estimated_mandatory_total = 120
        remaining_mandatory = max(0, estimated_mandatory_total - completed_mandatory_credits - selected_mandatory_credits)
        
        # Calculate remaining semesters
        remaining_sems = 8 - student.current_semester
        
        if remaining_sems > 0:
            credits_per_sem = remaining_mandatory / remaining_sems
            
            if credits_per_sem > self.max_credits:
                warnings.append(
                    f"GRADUATION AT RISK: Need {credits_per_sem:.1f} credits/semester "
                    f"for remaining mandatory courses (max allowed: {self.max_credits})"
                )
                feasible = False
            elif credits_per_sem > (self.max_credits * 0.8):
                warnings.append(
                    f"TIGHT SCHEDULE: Need {credits_per_sem:.1f} credits/semester "
                    f"for remaining mandatory courses. Little room for failures."
                )
                feasible = True
            else:
                feasible = True
        else:
            feasible = remaining_mandatory == 0
            if not feasible:
                warnings.append(f"Cannot graduate: {remaining_mandatory} mandatory credits still needed")
        
        return {
            'feasible': feasible,
            'warnings': warnings,
            'details': {
                'remaining_mandatory_credits': remaining_mandatory,
                'remaining_semesters': remaining_sems,
                'avg_credits_per_sem_needed': remaining_mandatory / remaining_sems if remaining_sems > 0 else 0,
                'completed_mandatory_credits': completed_mandatory_credits,
                'selected_mandatory_credits': selected_mandatory_credits
            }
        }
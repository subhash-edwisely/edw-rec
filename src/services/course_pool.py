from typing import List, Set
from src.models.student import StudentProfile
from src.models.course import Course

class CoursePoolGenerator:
    """Generate available course pool for a student"""
    
    def __init__(self, all_courses: List[Course]):
        self.all_courses = all_courses
    
    def generate_pool(self, student: StudentProfile, 
                     selected_courses: Set[str] = None,
                     deselected_courses: Set[str] = None) -> List[Course]:
        """
        Generate available course pool based on:
        - Student's current year level
        - Passed courses (exclude)
        - Failed courses (include regardless of year)
        - Manual selections/deselections
        """
        if selected_courses is None:
            selected_courses = set()
        if deselected_courses is None:
            deselected_courses = set()
        
        passed = set(student.get_passed_courses())
        failed = set(student.get_failed_courses())
        
        available = []
        
        for course in self.all_courses:
            # Skip if already passed
            if course.course_code in passed:
                continue
            
            # Skip if manually deselected
            if course.course_code in deselected_courses:
                continue
            
            # Include if manually selected
            if course.course_code in selected_courses:
                available.append(course)
                continue
            
            # Include failed courses regardless of year
            if course.course_code in failed:
                available.append(course)
                continue
            
            # Include courses from current year or below
            if course.year_level <= student.current_year:
                available.append(course)
        
        return available
    
    def check_prerequisites(self, course: Course, student: StudentProfile) -> tuple[bool, List[str]]:
        """
        Check if student has completed prerequisites
        Returns: (satisfied, missing_prerequisites)
        """
        if not course.prerequisites:
            return True, []
        
        passed = set(student.get_passed_courses())
        missing = [prereq for prereq in course.prerequisites if prereq not in passed]
        
        return len(missing) == 0, missing
    
    def get_remaining_mandatory_courses(self, student: StudentProfile) -> List[Course]:
        """Get all remaining mandatory courses (DC, FC, DLES)"""
        passed = set(student.get_passed_courses())
        mandatory = []
        
        for course in self.all_courses:
            if course.type in ['DC', 'FC', 'DLES'] and course.course_code not in passed:
                mandatory.append(course)
        
        return mandatory
    
    def calculate_remaining_credits(self, student: StudentProfile, exclude_courses: Set[str] = None) -> float:
        """Calculate remaining credits needed for graduation"""
        if exclude_courses is None:
            exclude_courses = set()
        
        total_required = 160
        earned = student.total_credits_earned
        
        # Add credits from courses to be excluded (e.g., current selection)
        for course in self.all_courses:
            if course.course_code in exclude_courses:
                earned += course.credits
        
        return max(0, total_required - earned)
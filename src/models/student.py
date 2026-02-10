from dataclasses import dataclass
from typing import List, Dict

@dataclass
class CourseResult:
    course_code: str
    grade: str
    credits: float
    status: str

@dataclass
class SemesterResult:
    semester: int
    courses: List[CourseResult]

@dataclass
class StudentProfile:
    student_id: str
    name: str
    current_semester: int
    current_year: int
    interests: List[str]
    workload_preference: str
    total_credits_earned: float
    gpa: float
    semester_results: List[SemesterResult]
    
    @staticmethod
    def from_dict(data: dict) -> 'StudentProfile':
        semester_results = []
        for sem in data.get('semester_results', []):
            courses = [CourseResult(**c) for c in sem['courses']]
            semester_results.append(SemesterResult(semester=sem['semester'], courses=courses))
        
        return StudentProfile(
            student_id=data['student_id'],
            name=data['name'],
            current_semester=data['current_semester'],
            current_year=data['current_year'],
            interests=data['interests'],
            workload_preference=data['workload_preference'],
            total_credits_earned=data['total_credits_earned'],
            gpa=data['gpa'],
            semester_results=semester_results
        )
    
    def get_passed_courses(self) -> List[str]:
        """Get list of all passed course codes"""
        passed = []
        for sem in self.semester_results:
            for course in sem.courses:
                if course.status == "passed":
                    passed.append(course.course_code)
        return passed
    
    def get_failed_courses(self) -> List[str]:
        """Get list of currently failed course codes (excluding those later passed)"""
        failed = set()
        passed = set()
        
        # Collect all passed and failed courses
        for sem in self.semester_results:
            for course in sem.courses:
                if course.status == "passed":
                    passed.add(course.course_code)
                elif course.status == "failed":
                    failed.add(course.course_code)
        
        # Return only courses that are failed and NOT later passed
        return list(failed - passed)
    
    def calculate_gpa_trend(self) -> str:
        """Calculate GPA trend for risk assessment"""
        if self.gpa >= 8.5:
            return "improving"
        elif self.gpa >= 7.0:
            return "stable"
        else:
            return "declining"
"""
Student Data Manager - Helper script to add/manage students in student.json

This script provides functions to:
1. Add new students
2. View all students
3. Update student information
"""

import json
from typing import Dict, List

def load_students(filepath: str = "data/student.json") -> Dict:
    """Load students from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"students": []}

def save_students(data: Dict, filepath: str = "data/student.json") -> None:
    """Save students to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def create_student_template() -> Dict:
    """Create a template for a new student"""
    return {
        "student_id": "22BCE0000",
        "name": "New Student",
        "current_semester": 1,
        "current_year": 1,
        "interests": ["Machine Learning"],
        "workload_preference": "medium",
        "total_credits_earned": 0,
        "gpa": 0.0,
        "semester_results": []
    }

def add_student(student_data: Dict, filepath: str = "data/student.json") -> bool:
    """Add a new student to the database"""
    data = load_students(filepath)
    
    # Check if student ID already exists
    for student in data['students']:
        if student['student_id'] == student_data['student_id']:
            print(f"Error: Student ID {student_data['student_id']} already exists!")
            return False
    
    data['students'].append(student_data)
    save_students(data, filepath)
    print(f"✅ Successfully added student: {student_data['name']} ({student_data['student_id']})")
    return True

def list_all_students(filepath: str = "data/student.json") -> None:
    """List all students in the database"""
    data = load_students(filepath)
    
    print("\n" + "="*80)
    print(f"{'ID':<15} {'Name':<25} {'Sem':<5} {'GPA':<6} {'Credits':<8}")
    print("="*80)
    
    for student in data['students']:
        print(f"{student['student_id']:<15} {student['name']:<25} "
              f"{student['current_semester']:<5} {student['gpa']:<6.2f} "
              f"{student['total_credits_earned']:<8}")
    
    print("="*80)
    print(f"Total students: {len(data['students'])}\n")

def get_student_by_id(student_id: str, filepath: str = "data/student.json") -> Dict:
    """Get student data by ID"""
    data = load_students(filepath)
    
    for student in data['students']:
        if student['student_id'] == student_id:
            return student
    
    return None

def update_student(student_id: str, updates: Dict, filepath: str = "data/student.json") -> bool:
    """Update student information"""
    data = load_students(filepath)
    
    for i, student in enumerate(data['students']):
        if student['student_id'] == student_id:
            data['students'][i].update(updates)
            save_students(data, filepath)
            print(f"✅ Successfully updated student: {student_id}")
            return True
    
    print(f"❌ Student not found: {student_id}")
    return False

def delete_student(student_id: str, filepath: str = "data/student.json") -> bool:
    """Delete a student from the database"""
    data = load_students(filepath)
    
    for i, student in enumerate(data['students']):
        if student['student_id'] == student_id:
            removed = data['students'].pop(i)
            save_students(data, filepath)
            print(f"✅ Successfully deleted student: {removed['name']} ({student_id})")
            return True
    
    print(f"❌ Student not found: {student_id}")
    return False


# Example usage
if __name__ == "__main__":
    print("Student Data Manager")
    print("=" * 80)
    
    # List all students
    list_all_students()
    
    # Example: Add a new student
    # new_student = {
    #     "student_id": "22BCE5678",
    #     "name": "Priya Sharma",
    #     "current_semester": 3,
    #     "current_year": 2,
    #     "interests": ["Web Development", "Cloud Computing"],
    #     "workload_preference": "high",
    #     "total_credits_earned": 45,
    #     "gpa": 8.5,
    #     "semester_results": [
    #         {
    #             "semester": 1,
    #             "courses": [
    #                 {"course_code": "BMAT101L", "grade": "A", "credits": 3, "status": "passed"}
    #             ]
    #         }
    #     ]
    # }
    # add_student(new_student)
    
    # Example: Update student
    # update_student("21BCE1234", {"gpa": 8.0, "total_credits_earned": 95})
    
    # Example: Get student details
    # student = get_student_by_id("21BCE1234")
    # if student:
    #     print(f"\nStudent Details: {json.dumps(student, indent=2)}")
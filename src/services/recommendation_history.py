import json
import os
from datetime import datetime
from typing import Dict, List
from src.models.student import StudentProfile

class RecommendationHistory:
    """Manage recommendations history storage"""
    
    def __init__(self, history_file: str = "data/recommendation_history.json"):
        self.history_file = history_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create history file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump({"history": []}, f)
    
    def save_recommendation(self, student: StudentProfile, 
                          preferences: Dict,
                          recommendations: Dict,
                          semester: int) -> None:
        """Save a recommendation session"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "student_id": student.student_id,
            "student_name": student.name,
            "semester": semester,
            "gpa": student.gpa,
            "credits_earned": student.total_credits_earned,
            "preferences": {
                "interests": student.interests,
                "workload": student.workload_preference,
                "min_credits": preferences.get('min_credits'),
                "max_credits": preferences.get('max_credits'),
                "selected_courses": list(preferences.get('selected_courses', set())),
                "deselected_courses": list(preferences.get('deselected_courses', set()))
            },
            "recommendations": recommendations.get('recommendations', [])
        }
        
        # Load existing history
        with open(self.history_file, 'r') as f:
            data = json.load(f)
        
        # Add new entry
        data['history'].append(entry)
        
        # Save updated history
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_student_history(self, student_id: str) -> List[Dict]:
        """Get all recommendations for a student"""
        with open(self.history_file, 'r') as f:
            data = json.load(f)
        
        return [entry for entry in data['history'] if entry['student_id'] == student_id]
    
    def get_semester_history(self, student_id: str, semester: int) -> List[Dict]:
        """Get recommendations for a specific semester"""
        history = self.get_student_history(student_id)
        return [entry for entry in history if entry['semester'] == semester]
    
    def get_latest_recommendation(self, student_id: str) -> Dict:
        """Get most recent recommendation"""
        history = self.get_student_history(student_id)
        if history:
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)[0]
        return None
    
    def clear_student_history(self, student_id: str) -> None:
        """Clear all history for a student"""
        with open(self.history_file, 'r') as f:
            data = json.load(f)
        
        data['history'] = [entry for entry in data['history'] if entry['student_id'] != student_id]
        
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)
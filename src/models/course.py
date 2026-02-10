from dataclasses import dataclass
from typing import List

@dataclass
class Course:
    course_code: str
    name: str
    credits: float
    type: str  # FC, DLES, DC, DE, OE
    prerequisites: List[str]
    year_level: int
    difficulty: int
    slots: List[str]
    
    @staticmethod
    def from_dict(data: dict) -> 'Course':
        return Course(
            course_code=data['course_code'],
            name=data['name'],
            credits=data['credits'],
            type=data['type'],
            prerequisites=data.get('prerequisites', []),
            year_level=data['year_level'],
            difficulty=data['difficulty'],
            slots=data['slots']
        )
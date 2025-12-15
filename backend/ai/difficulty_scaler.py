"""
Resume-Aware Difficulty Scaling Engine
Adjusts question difficulty based on performance and resume skills
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Difficulty(Enum):
    """Question difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class Category(Enum):
    """Skill categories"""
    ALGORITHMS = "algorithms"
    DATA_STRUCTURES = "data_structures"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    LANGUAGE_SPECIFIC = "language_specific"
    FRAMEWORKS = "frameworks"


@dataclass
class SkillScore:
    """Score for a specific skill category"""
    category: str
    correctness: float = 0.5  # 0-1
    speed: float = 0.5  # 0-1
    clarity: float = 0.5  # 0-1
    depth: float = 0.5  # 0-1
    attempts: int = 0
    recent_performance: List[float] = field(default_factory=list)
    
    @property
    def overall_score(self) -> float:
        """Weighted overall score"""
        return (
            self.correctness * 0.4 +
            self.speed * 0.2 +
            self.clarity * 0.2 +
            self.depth * 0.2
        )
    
    @property
    def proficiency_level(self) -> str:
        """Human-readable proficiency"""
        score = self.overall_score
        if score >= 0.8:
            return "Expert"
        elif score >= 0.65:
            return "Senior"
        elif score >= 0.5:
            return "Mid-level"
        elif score >= 0.35:
            return "Junior"
        else:
            return "Learning"


@dataclass
class ResumeSkills:
    """Parsed skills from resume"""
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    years_experience: int = 0
    primary_language: Optional[str] = None


class DifficultyScaler:
    """
    Manages adaptive difficulty scaling based on performance
    """
    
    def __init__(self, resume_skills: ResumeSkills):
        self.resume_skills = resume_skills
        self.skill_scores: Dict[str, SkillScore] = {}
        self.question_history: List[Dict] = []
        
        # Initialize categories based on resume
        self._initialize_skill_scores()
    
    def _initialize_skill_scores(self):
        """Initialize skill scores based on resume"""
        # Base scores on years of experience
        base_score = min(0.3 + (self.resume_skills.years_experience * 0.05), 0.7)
        
        # Initialize all categories
        for category in Category:
            self.skill_scores[category.value] = SkillScore(
                category=category.value,
                correctness=base_score,
                speed=base_score,
                clarity=base_score,
                depth=base_score
            )
        
        # Boost language-specific if languages are listed
        if self.resume_skills.languages:
            self.skill_scores[Category.LANGUAGE_SPECIFIC.value].correctness = min(base_score + 0.2, 0.9)
        
        # Boost frameworks if experience listed
        if self.resume_skills.frameworks:
            self.skill_scores[Category.FRAMEWORKS.value].correctness = min(base_score + 0.15, 0.85)
    
    def update_performance(
        self,
        category: str,
        correctness: float,
        time_taken: float,
        clarity_score: float,
        depth_score: float,
        expected_time: float = 600  # 10 minutes default
    ):
        """
        Update skill scores based on performance
        
        Args:
            category: Skill category
            correctness: 0-1 (tests passed ratio)
            time_taken: Seconds taken
            clarity_score: 0-1 (code clarity)
            depth_score: 0-1 (explanation depth)
            expected_time: Expected time for the question
        """
        if category not in self.skill_scores:
            self.skill_scores[category] = SkillScore(category=category)
        
        score = self.skill_scores[category]
        
        # Calculate speed score (faster = higher, but cap at expected time)
        speed_score = min(expected_time / max(time_taken, 1), 1.0)
        
        # Update with exponential moving average (weight recent performance more)
        alpha = 0.3  # Learning rate
        score.correctness = (1 - alpha) * score.correctness + alpha * correctness
        score.speed = (1 - alpha) * score.speed + alpha * speed_score
        score.clarity = (1 - alpha) * score.clarity + alpha * clarity_score
        score.depth = (1 - alpha) * score.depth + alpha * depth_score
        score.attempts += 1
        
        # Track recent performance (last 5)
        score.recent_performance.append(correctness)
        if len(score.recent_performance) > 5:
            score.recent_performance.pop(0)
        
        logger.info(
            f"Updated {category}: "
            f"correctness={score.correctness:.2f}, "
            f"speed={score.speed:.2f}, "
            f"overall={score.overall_score:.2f}, "
            f"level={score.proficiency_level}"
        )
    
    def get_next_difficulty(self, category: str) -> Difficulty:
        """
        Determine next question difficulty for category
        
        Rules:
        - If 2+ recent successes (>0.8) → increase difficulty
        - If 2+ recent struggles (<0.4) → decrease difficulty
        - Otherwise maintain current level
        """
        if category not in self.skill_scores:
            return Difficulty.EASY
        
        score = self.skill_scores[category]
        recent = score.recent_performance[-3:] if len(score.recent_performance) >= 3 else score.recent_performance
        
        if not recent:
            # No history - start at medium if experienced, easy otherwise
            if self.resume_skills.years_experience >= 3:
                return Difficulty.MEDIUM
            return Difficulty.EASY
        
        avg_recent = sum(recent) / len(recent)
        
        # Strong performance - scale up
        if avg_recent >= 0.8 and len(recent) >= 2:
            current_level = self._score_to_difficulty(score.overall_score)
            if current_level == Difficulty.EASY:
                return Difficulty.MEDIUM
            elif current_level == Difficulty.MEDIUM:
                return Difficulty.HARD
            elif current_level == Difficulty.HARD:
                return Difficulty.EXPERT
            return Difficulty.EXPERT
        
        # Struggling - scale down
        elif avg_recent < 0.4 and len(recent) >= 2:
            current_level = self._score_to_difficulty(score.overall_score)
            if current_level == Difficulty.EXPERT:
                return Difficulty.HARD
            elif current_level == Difficulty.HARD:
                return Difficulty.MEDIUM
            elif current_level == Difficulty.MEDIUM:
                return Difficulty.EASY
            return Difficulty.EASY
        
        # Maintain current level
        return self._score_to_difficulty(score.overall_score)
    
    def _score_to_difficulty(self, score: float) -> Difficulty:
        """Convert overall score to difficulty level"""
        if score >= 0.75:
            return Difficulty.HARD
        elif score >= 0.55:
            return Difficulty.MEDIUM
        else:
            return Difficulty.EASY
    
    def get_follow_up_intensity(self, category: str) -> str:
        """
        Determine follow-up question intensity
        
        Returns: 'gentle', 'moderate', 'strict'
        """
        if category not in self.skill_scores:
            return 'gentle'
        
        score = self.skill_scores[category]
        
        if score.proficiency_level in ['Expert', 'Senior']:
            return 'strict'
        elif score.proficiency_level == 'Mid-level':
            return 'moderate'
        else:
            return 'gentle'
    
    def get_scoring_rubric(self, category: str) -> Dict:
        """
        Get appropriate scoring rubric based on proficiency
        
        Returns expectations aligned with skill level
        """
        if category not in self.skill_scores:
            level = "Junior"
        else:
            level = self.skill_scores[category].proficiency_level
        
        rubrics = {
            "Learning": {
                "correctness_weight": 0.5,
                "explanation_required": "basic",
                "edge_cases_expected": 0,
                "optimization_required": False,
                "time_limit_multiplier": 2.0
            },
            "Junior": {
                "correctness_weight": 0.6,
                "explanation_required": "moderate",
                "edge_cases_expected": 1,
                "optimization_required": False,
                "time_limit_multiplier": 1.5
            },
            "Mid-level": {
                "correctness_weight": 0.7,
                "explanation_required": "detailed",
                "edge_cases_expected": 2,
                "optimization_required": True,
                "time_limit_multiplier": 1.0
            },
            "Senior": {
                "correctness_weight": 0.8,
                "explanation_required": "comprehensive",
                "edge_cases_expected": 3,
                "optimization_required": True,
                "time_limit_multiplier": 0.9
            },
            "Expert": {
                "correctness_weight": 0.9,
                "explanation_required": "comprehensive_with_tradeoffs",
                "edge_cases_expected": 4,
                "optimization_required": True,
                "time_limit_multiplier": 0.8
            }
        }
        
        return rubrics.get(level, rubrics["Junior"])
    
    def get_preferred_language(self) -> str:
        """Get preferred programming language from resume"""
        if self.resume_skills.primary_language:
            return self.resume_skills.primary_language
        
        if self.resume_skills.languages:
            # Prioritize common interview languages
            priority = ['Python', 'Java', 'JavaScript', 'C++', 'Go']
            for lang in priority:
                if lang in self.resume_skills.languages:
                    return lang
            return self.resume_skills.languages[0]
        
        return "Python"  # Default
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        summary = {
            "categories": {},
            "overall_proficiency": "Mid-level",
            "strengths": [],
            "areas_to_improve": []
        }
        
        for category, score in self.skill_scores.items():
            summary["categories"][category] = {
                "proficiency": score.proficiency_level,
                "score": round(score.overall_score, 2),
                "attempts": score.attempts
            }
            
            # Identify strengths and weaknesses
            if score.overall_score >= 0.7 and score.attempts > 0:
                summary["strengths"].append(category)
            elif score.overall_score < 0.5 and score.attempts > 0:
                summary["areas_to_improve"].append(category)
        
        # Overall proficiency (average)
        if self.skill_scores:
            avg_score = sum(s.overall_score for s in self.skill_scores.values()) / len(self.skill_scores)
            if avg_score >= 0.8:
                summary["overall_proficiency"] = "Expert"
            elif avg_score >= 0.65:
                summary["overall_proficiency"] = "Senior"
            elif avg_score >= 0.5:
                summary["overall_proficiency"] = "Mid-level"
            elif avg_score >= 0.35:
                summary["overall_proficiency"] = "Junior"
            else:
                summary["overall_proficiency"] = "Learning"
        
        return summary


def create_scaler_from_resume(resume_text: str) -> DifficultyScaler:
    """
    Create difficulty scaler from resume text
    
    Extracts skills and experience automatically
    """
    # Simple extraction (in real system, use resume_parser.py)
    languages = []
    frameworks = []
    years_exp = 0
    
    # Extract languages
    lang_keywords = {
        'python': 'Python',
        'java': 'Java',
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'c++': 'C++',
        'go': 'Go',
        'rust': 'Rust',
        'ruby': 'Ruby'
    }
    
    text_lower = resume_text.lower()
    for keyword, proper_name in lang_keywords.items():
        if keyword in text_lower:
            languages.append(proper_name)
    
    # Extract frameworks
    framework_keywords = ['react', 'angular', 'vue', 'spring', 'django', 'flask', 'node']
    frameworks = [fw for fw in framework_keywords if fw in text_lower]
    
    # Extract years (rough)
    import re
    year_matches = re.findall(r'(\d+)\+?\s*years?', text_lower)
    if year_matches:
        years_exp = max(int(y) for y in year_matches)
    
    skills = ResumeSkills(
        languages=languages,
        frameworks=frameworks,
        years_experience=years_exp,
        primary_language=languages[0] if languages else "Python"
    )
    
    return DifficultyScaler(skills)

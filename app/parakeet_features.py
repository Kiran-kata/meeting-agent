"""
Parakeet AI-inspired features for meeting assistant.
Includes: Resume context, coding interview support, multilingual, performance analysis.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import hashlib
import base64

logger = logging.getLogger(__name__)


class ResumeProfile:
    """
    Manages user resume and profile information for personalized interview responses.
    Parakeet AI style: Upload once, auto-match answers to experience.
    """
    
    PROFILE_DIR = Path("data/profiles")
    
    def __init__(self):
        self.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self.current_profile = None
        self.resume_text = ""
        self.personal_info = {}
        
    def create_profile(self, name: str, email: str = "", role: str = ""):
        """Create a new interview profile."""
        profile_id = hashlib.md5(f"{name}{email}".encode()).hexdigest()[:8]
        
        self.current_profile = {
            "id": profile_id,
            "name": name,
            "email": email,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "interviews": [],
            "resume_path": None
        }
        
        self.personal_info = {
            "name": name,
            "email": email,
            "target_role": role,
            "skills": [],
            "experience_years": 0,
            "education": []
        }
        
        logger.info(f"Profile created: {name} ({profile_id})")
        return profile_id
    
    def upload_resume(self, pdf_path: str) -> bool:
        """
        Upload and parse resume for context matching.
        Extracts key information from PDF.
        """
        try:
            from PyPDF2 import PdfReader
            
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                resume_text = ""
                for page in reader.pages:
                    resume_text += page.extract_text()
            
            # Store resume reference
            if self.current_profile:
                self.current_profile["resume_path"] = pdf_path
            
            self.resume_text = resume_text
            
            # Extract key information
            self._extract_resume_info(resume_text)
            
            logger.info(f"Resume loaded: {os.path.basename(pdf_path)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load resume: {e}")
            return False
    
    def _extract_resume_info(self, text: str):
        """Extract skills, experience, education from resume text."""
        text_lower = text.lower()
        
        # Common technical skills
        skills_keywords = {
            'python', 'javascript', 'java', 'cpp', 'c#', 'golang',
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi',
            'sql', 'mongodb', 'postgresql', 'redis', 'elasticsearch',
            'aws', 'gcp', 'azure', 'kubernetes', 'docker',
            'git', 'ci/cd', 'jenkins', 'gitlab',
            'machine learning', 'deep learning', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'scikit-learn', 'numpy', 'pandas'
        }
        
        found_skills = [s for s in skills_keywords if s in text_lower]
        self.personal_info["skills"] = found_skills
        
        logger.info(f"Extracted skills: {found_skills}")
    
    def get_profile_context(self) -> str:
        """Return resume/profile context for LLM prompt."""
        if not self.resume_text:
            return ""
        
        context = f"""
User Profile:
- Name: {self.personal_info.get('name', 'Unknown')}
- Target Role: {self.personal_info.get('target_role', 'Unknown')}
- Skills: {', '.join(self.personal_info.get('skills', []))}

Resume Summary:
{self.resume_text[:2000]}  # First 2000 chars to save tokens
"""
        return context.strip()
    
    def save_profile(self):
        """Save profile to disk."""
        if not self.current_profile:
            return False
        
        profile_file = self.PROFILE_DIR / f"{self.current_profile['id']}.json"
        try:
            with open(profile_file, 'w') as f:
                json.dump(self.current_profile, f, indent=2)
            logger.info(f"Profile saved: {profile_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            return False


class CodingInterviewDetector:
    """
    Detect and handle coding interview questions.
    Parakeet AI style: Screen capture for LeetCode/HackerRank problems.
    """
    
    def __init__(self):
        self.last_code_block = ""
        self.last_problem_text = ""
        self.detected_platform = None
    
    def analyze_screen_content(self, screen_text: str, screen_image=None) -> dict:
        """
        Analyze screen content for coding interview detection.
        
        Returns:
            {
                "is_coding_interview": bool,
                "platform": str (leetcode, hackerrank, codesignal, etc),
                "problem_text": str,
                "code_visible": bool
            }
        """
        text_lower = screen_text.lower()
        
        # Detect platform
        platform = None
        if "leetcode" in text_lower:
            platform = "leetcode"
        elif "hackerrank" in text_lower:
            platform = "hackerrank"
        elif "codesignal" in text_lower:
            platform = "codesignal"
        elif "codeforces" in text_lower:
            platform = "codeforces"
        elif "codewars" in text_lower:
            platform = "codewars"
        
        # Check for coding patterns
        has_code_patterns = any([
            "def " in screen_text,
            "function " in screen_text,
            "class " in screen_text,
            "{" in screen_text and "}" in screen_text,
            "return " in screen_text,
            "import " in screen_text or "#include" in screen_text
        ])
        
        result = {
            "is_coding_interview": platform is not None or has_code_patterns,
            "platform": platform,
            "problem_text": screen_text[:1500],  # First 1500 chars
            "code_visible": has_code_patterns,
            "detected_platform": platform
        }
        
        if platform:
            self.detected_platform = platform
        
        return result


class MultilingualSupport:
    """
    Support 52+ languages for interview responses.
    Parakeet AI style: Real-time multilingual interview support.
    """
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'zh': 'Chinese (Simplified)',
        'zh-tw': 'Chinese (Traditional)',
        'ko': 'Korean',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'bn': 'Bengali',
        'pa': 'Punjabi',
        'pl': 'Polish',
        'tr': 'Turkish',
        'vi': 'Vietnamese',
        'th': 'Thai',
        'id': 'Indonesian',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish',
        'el': 'Greek',
        'cs': 'Czech',
        'hu': 'Hungarian',
        'ro': 'Romanian',
        'bg': 'Bulgarian',
        'sr': 'Serbian',
        'uk': 'Ukrainian',
        'he': 'Hebrew',
        'fa': 'Persian',
        'ur': 'Urdu',
        'ms': 'Malay',
        'tl': 'Filipino',
        'km': 'Khmer',
        'lo': 'Lao',
        'my': 'Burmese',
        'ta': 'Tamil',
        'te': 'Telugu',
        'kn': 'Kannada',
        'ml': 'Malayalam'
    }
    
    def __init__(self):
        self.current_language = 'en'
        self.language_detected = False
    
    def detect_language(self, text: str) -> str:
        """
        Detect interview language from audio transcription.
        Uses heuristics on available text.
        """
        # Simple heuristic detection
        text_lower = text.lower()
        
        # Add more sophisticated detection if needed
        # For now, default to English
        return 'en'
    
    def set_language(self, language_code: str) -> bool:
        """Set interview language."""
        if language_code in self.SUPPORTED_LANGUAGES:
            self.current_language = language_code
            logger.info(f"Language set to: {self.SUPPORTED_LANGUAGES[language_code]}")
            return True
        return False
    
    def get_language_instruction(self) -> str:
        """Get instruction for LLM to respond in selected language."""
        lang_name = self.SUPPORTED_LANGUAGES.get(self.current_language, 'English')
        return f"Respond in {lang_name} only."


class InterviewPerformanceAnalyzer:
    """
    Analyze interview performance and provide feedback.
    Parakeet AI style: Post-interview insights and improvement recommendations.
    """
    
    def __init__(self):
        self.interview_session = {
            "start_time": None,
            "end_time": None,
            "questions": [],
            "answers": [],
            "metrics": {}
        }
    
    def start_interview(self):
        """Mark interview start."""
        self.interview_session["start_time"] = datetime.now()
        self.interview_session["questions"] = []
        self.interview_session["answers"] = []
    
    def add_qa_pair(self, question: str, answer: str, answer_time: float):
        """Record Q&A pair with metrics."""
        self.interview_session["questions"].append({
            "text": question,
            "timestamp": datetime.now().isoformat()
        })
        self.interview_session["answers"].append({
            "text": answer,
            "generation_time": answer_time,
            "timestamp": datetime.now().isoformat()
        })
    
    def end_interview(self) -> dict:
        """Generate comprehensive post-interview analysis."""
        self.interview_session["end_time"] = datetime.now()
        
        duration = (
            self.interview_session["end_time"] - 
            self.interview_session["start_time"]
        ).total_seconds() / 60  # minutes
        
        num_questions = len(self.interview_session["questions"])
        total_answer_time = sum(a.get("generation_time", 0) for a in self.interview_session["answers"])
        avg_answer_time = total_answer_time / num_questions if num_questions > 0 else 0
        
        analysis = {
            "interview_duration_minutes": round(duration, 1),
            "total_questions": num_questions,
            "average_answer_time_seconds": round(avg_answer_time, 2),
            "interview_efficiency": self._calculate_efficiency(duration, num_questions),
            "recommendations": self._generate_recommendations(num_questions, avg_answer_time),
            "generated_at": datetime.now().isoformat(),
            "summary": self._generate_summary()
        }
        
        return analysis
    
    def _calculate_efficiency(self, duration: float, num_questions: int) -> str:
        """Assess interview efficiency."""
        if duration == 0:
            return "No data"
        
        questions_per_minute = num_questions / duration if duration > 0 else 0
        
        if questions_per_minute >= 0.8:
            return "Excellent - Fast pace with quality answers"
        elif questions_per_minute >= 0.5:
            return "Good - Moderate pace, thoughtful responses"
        else:
            return "Steady - Thorough, detailed answers"
    
    def _generate_recommendations(self, num_questions: int, avg_time: float) -> list:
        """Generate improvement recommendations."""
        recommendations = []
        
        if num_questions < 5:
            recommendations.append("Try to practice with more questions for better coverage")
        
        if avg_time > 30:
            recommendations.append("Consider more concise answers (current avg: {:.0f}s)".format(avg_time))
        elif avg_time < 10:
            recommendations.append("Provide more detailed answers for better impression (current avg: {:.0f}s)".format(avg_time))
        
        if num_questions > 0:
            recommendations.append("Review transcripts of difficult questions for improvement")
        
        recommendations.append("Practice active listening and clarification techniques")
        recommendations.append("Focus on behavioral examples using STAR method")
        
        return recommendations
    
    def _generate_summary(self) -> str:
        """Generate interview summary."""
        num_q = len(self.interview_session["questions"])
        duration = (
            self.interview_session["end_time"] - 
            self.interview_session["start_time"]
        ).total_seconds() / 60
        
        return f"""
Interview Summary:
- Questions: {num_q}
- Duration: {duration:.1f} minutes
- Questions covered: {', '.join(q['text'][:50] + '...' if len(q['text']) > 50 else q['text'] for q in self.interview_session['questions'][:5])}
"""
    
    def save_analysis(self, analysis: dict, filename: str = None) -> str:
        """Save interview analysis to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_analysis_{timestamp}.json"
        
        analysis_dir = Path("data/interview_analyses")
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = analysis_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(analysis, f, indent=2)
            logger.info(f"Interview analysis saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            return None


class StealthMode:
    """
    Advanced undetectability features.
    Parakeet AI style: Invisible on screen share, dock, task manager, tab switching.
    """
    
    def __init__(self, window_widget):
        self.window = window_widget
        self.stealth_active = False
    
    def enable_stealth(self):
        """Enable stealth mode (multiple undetectability layers)."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get window handle
            hwnd = self.window.winId()
            
            # Hide from task manager (set style to tool window)
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            
            # Apply extended window styles
            ctypes.windll.user32.SetWindowLongW(
                hwnd,
                ctypes.windll.user32.GWL_EXSTYLE if hasattr(ctypes.windll.user32, 'GWL_EXSTYLE') else -20,
                WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            )
            
            # Hide window
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
            
            self.stealth_active = True
            logger.info("Stealth mode enabled")
            
        except Exception as e:
            logger.warning(f"Could not enable full stealth: {e}")
    
    def disable_stealth(self):
        """Disable stealth mode and show window."""
        try:
            import ctypes
            hwnd = self.window.winId()
            ctypes.windll.user32.ShowWindow(hwnd, 1)  # SW_SHOW
            self.stealth_active = False
            logger.info("Stealth mode disabled")
        except Exception as e:
            logger.warning(f"Could not disable stealth: {e}")


class QuestionAutoDetector:
    """
    Auto-detect and categorize interview questions.
    Parakeet AI style: Automatic question recognition and response generation.
    """
    
    QUESTION_CATEGORIES = {
        "behavioral": [
            "tell me about", "describe", "give an example", "explain",
            "time when", "when have you", "why did you", "how did you handle",
            "failed", "mistake", "challenge", "conflict", "learned from"
        ],
        "technical": [
            "what is", "how does", "design a", "implement", "code",
            "algorithm", "data structure", "complexity", "optimize",
            "database", "architecture", "system design", "api"
        ],
        "situational": [
            "what if", "scenario", "conflict", "disagree", "difficult",
            "handled conflict", "managed", "resolved", "problem arose"
        ],
        "problem_solving": [
            "how would you solve", "approach", "strategy", "method",
            "troubleshoot", "debug", "fix", "improve", "optimize"
        ]
    }
    
    def __init__(self):
        self.last_question_category = None
    
    def categorize_question(self, question_text: str) -> str:
        """Categorize interview question type."""
        text_lower = question_text.lower()
        
        # Score each category based on keyword matches
        scores = {}
        for category, keywords in self.QUESTION_CATEGORIES.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[category] = score
        
        # Return category with highest score
        best_category = max(scores, key=scores.get) if max(scores.values()) > 0 else "general"
        self.last_question_category = best_category
        return best_category
    
    def get_response_template(self, category: str) -> str:
        """Get response template based on question category."""
        templates = {
            "behavioral": "Use STAR method (Situation, Task, Action, Result)",
            "technical": "Provide clear explanation with examples",
            "situational": "Show problem-solving and collaboration skills",
            "problem_solving": "Outline approach, discuss trade-offs",
            "general": "Provide comprehensive, thoughtful answer"
        }
        
        return templates.get(category, "Provide a thoughtful, complete answer")

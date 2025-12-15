"""
AI Module - Core intelligence for Interview Assistant
"""
from .interview_engine import InterviewEngine
from .scoring import ScoringEngine, ScoreResult
from .resume_parser import ResumeParser
from .followup_generator import FollowUpGenerator
from .vision_context_manager import VisionContextManager, MergedContext, ContextSource
from .speech_listener import SpeechListener, TranscriptResult, list_microphones
from .question_detector import QuestionDetector, DetectedQuestion, QuestionCategory
from .language_selector import LanguageSelector, ResumeLanguageData, LanguageProfile
from .interview_brain import InterviewBrain, BrainMode, BrainResponse

__all__ = [
    # Core
    'InterviewEngine',
    'ScoringEngine', 'ScoreResult',
    'ResumeParser', 'FollowUpGenerator',
    
    # Vision & Context
    'VisionContextManager', 'MergedContext', 'ContextSource',
    
    # Speech
    'SpeechListener', 'TranscriptResult', 'list_microphones',
    
    # Question Detection
    'QuestionDetector', 'DetectedQuestion', 'QuestionCategory',
    
    # Language Selection
    'LanguageSelector', 'ResumeLanguageData', 'LanguageProfile',
    
    # Brain
    'InterviewBrain', 'BrainMode', 'BrainResponse'
]



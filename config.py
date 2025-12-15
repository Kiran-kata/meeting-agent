"""
Configuration for Interview Assistant
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Audio Configuration
# Device 0 = Default Mic (your voice)
# Device 1 = Microphone Array
# Device 3 = NVIDIA Broadcast (if using RTX voice)
AUDIO_DEVICE_INDEX = 1  # Microphone Array - Intel Smart Sound
SAMPLE_RATE = 16000
CHUNK_DURATION = 3  # seconds per transcription chunk (reduced for faster response)

# Interview Settings
DEFAULT_ROLE = "SDE"
DIFFICULTY = "medium"  # easy, medium, hard
MAX_FOLLOWUPS = 3  # Max follow-up questions per answer
INTERVIEW_TIME_LIMIT = 45  # minutes

# Scoring Weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "star_structure": 0.25,
    "technical_accuracy": 0.30,
    "communication": 0.20,
    "problem_solving": 0.25,
}

# Role Templates
ROLE_TEMPLATES = {
    "SDE": {
        "name": "Software Development Engineer",
        "behavioral_weight": 0.4,
        "technical_weight": 0.6,
        "topics": ["DSA", "System Design", "OOP", "Debugging", "Code Review"],
    },
    "ML": {
        "name": "Machine Learning Engineer",
        "behavioral_weight": 0.3,
        "technical_weight": 0.7,
        "topics": ["ML Algorithms", "Deep Learning", "Feature Engineering", "MLOps", "Statistics"],
    },
    "DE": {
        "name": "Data Engineer",
        "behavioral_weight": 0.35,
        "technical_weight": 0.65,
        "topics": ["SQL", "ETL", "Data Modeling", "Spark", "Airflow"],
    },
    "PM": {
        "name": "Product Manager",
        "behavioral_weight": 0.7,
        "technical_weight": 0.3,
        "topics": ["Product Strategy", "Metrics", "Prioritization", "User Research", "Roadmapping"],
    },
    "QA": {
        "name": "QA Automation Engineer",
        "behavioral_weight": 0.4,
        "technical_weight": 0.6,
        "topics": ["Test Strategy", "Automation Frameworks", "CI/CD", "API Testing", "Performance"],
    },
    "FS": {
        "name": "Full Stack Developer",
        "behavioral_weight": 0.35,
        "technical_weight": 0.65,
        "topics": ["Frontend", "Backend", "Databases", "APIs", "DevOps"],
    },
}

# UI Settings
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 400
WINDOW_OPACITY = 0.95
STEALTH_MODE = True  # Auto-hide from screen capture

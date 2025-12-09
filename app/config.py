"""
Configuration module for Meeting Agent
Loads environment variables and validates Gemini API keys
"""
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your-api"):
    print("\n" + "="*60)
    print("❌ GEMINI_API_KEY NOT CONFIGURED!")
    print("="*60)
    print("\n📋 SETUP INSTRUCTIONS:")
    print("1. Get your Gemini API key from: https://aistudio.google.com/app/apikey")
    print("2. Create a .env file in the project root with:")
    print("   GEMINI_API_KEY=your-api-key-here")
    print("\n3. Run the agent again after configuration")
    print("="*60 + "\n")
    sys.exit(1)

# Paths
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe")

# Gemini Model Configuration
GEMINI_MODEL = "gemini-1.5-flash"  # Fast and efficient model
GEMINI_VISION_MODEL = "gemini-1.5-flash"  # For image/screen analysis

# Project Structure
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
SUMMARIES_DIR = os.path.join(PROJECT_ROOT, "meeting_summaries")

# Audio Settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION_SECONDS = 8

# Create directories
for directory in [DATA_DIR, LOGS_DIR, SUMMARIES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOGS_DIR, 'meeting_agent.log'))
    ]
)

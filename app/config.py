"""
Configuration module for Meeting Agent
Loads environment variables and validates API keys
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your"):
    raise ValueError(
        "\n" + "="*60
        + "\n❌ OPENAI_API_KEY NOT CONFIGURED!"
        + "\n" + "="*60
        + "\nSteps to fix:"
        + "\n1. Go to: https://platform.openai.com/account/api-keys"
        + "\n2. Create a new API key"
        + "\n3. Edit .env file and set: OPENAI_API_KEY=sk-..."
        + "\n4. Restart the application"
        + "\n" + "="*60 + "\n"
    )

# Paths
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "C:\\Program Files\\Tesseract-OCR\\tesseract.exe")

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

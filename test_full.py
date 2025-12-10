#!/usr/bin/env python3
"""
Comprehensive test of the meeting agent
"""
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test imports
logger.info("Testing imports...")
try:
    from app.config import GEMINI_API_KEY, GEMINI_MODEL
    logger.info(f"✓ Config loaded (model: {GEMINI_MODEL})")
except Exception as e:
    logger.error(f"✗ Config error: {e}")
    exit(1)

try:
    from app.llm_client import ask_llm_with_context
    logger.info("✓ LLM client loaded")
except Exception as e:
    logger.error(f"✗ LLM client error: {e}")
    exit(1)

try:
    import sounddevice as sd
    devices = sd.query_devices()
    logger.info(f"✓ Audio devices available: {len(devices)} devices")
    
    # Check specific devices
    dev_24 = devices[24] if len(devices) > 24 else None
    dev_2 = devices[2] if len(devices) > 2 else None
    
    if dev_24:
        logger.info(f"  Device 24: {dev_24['name']} (inputs: {dev_24['max_input_channels']})")
    if dev_2:
        logger.info(f"  Device 2: {dev_2['name']} (inputs: {dev_2['max_input_channels']})")
except Exception as e:
    logger.error(f"✗ Audio device error: {e}")
    exit(1)

try:
    from app.pdf_index import PDFIndex
    logger.info("✓ PDF index loaded")
except Exception as e:
    logger.error(f"✗ PDF index error: {e}")
    exit(1)

try:
    from app.narration import Narrator
    logger.info("✓ Narration module loaded")
except Exception as e:
    logger.error(f"✗ Narration error: {e}")
    exit(1)

# Test LLM
logger.info("\nTesting LLM functionality...")
try:
    response = ask_llm_with_context(
        question="What is 2+2?",
        transcript_context="The user asked what is 2 plus 2",
        screen_text="",
        pdf_context=""
    )
    logger.info(f"✓ LLM response: {response}")
except Exception as e:
    logger.error(f"✗ LLM test failed: {e}")
    exit(1)

logger.info("\n" + "="*50)
logger.info("✓ ALL TESTS PASSED!")
logger.info("="*50)
logger.info("\nNext steps:")
logger.info("1. Run: python -m app.main")
logger.info("2. Click 'Add PDF' button to load a PDF")
logger.info("3. Click 'Start' button to begin meeting")
logger.info("4. Click 'Stop' button to end and generate summary")

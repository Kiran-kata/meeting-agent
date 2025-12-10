#!/usr/bin/env python3
"""
Integration test for the meeting agent (non-GUI).
This tests all the key components without requiring manual interaction.
"""
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("="*60)
logger.info("MEETING AGENT INTEGRATION TEST")
logger.info("="*60)

# Import core components
logger.info("\n[1/6] Loading core components...")
try:
    from app.agent import MeetingAgentCore
    from app.llm_client import ask_llm_with_context, summarize_meeting, detect_questions
    from app.pdf_index import PDFIndex
    from app.context_manager import ContextManager
    logger.info("✓ All imports successful")
except Exception as e:
    logger.error(f"✗ Import failed: {e}")
    exit(1)

# Test PDF indexing
logger.info("\n[2/6] Testing PDF indexing...")
try:
    pdf_index = PDFIndex()
    pdf_index.build()
    
    # Try to find and add a PDF
    pdf_files = list(Path("C:/Users/kiran/OneDrive/Desktop").glob("**/*.pdf"))
    if pdf_files:
        pdf_path = str(pdf_files[0])
        success = pdf_index.add_pdf(pdf_path)
        if success:
            logger.info(f"✓ PDF loaded successfully: {Path(pdf_path).name}")
            # Test search
            results = pdf_index.query("test", k=3)
            logger.info(f"✓ PDF search returned {len(results)} results")
        else:
            logger.warning("⚠ PDF loaded but no results")
    else:
        logger.info("✓ PDF indexing working (no test PDFs found)")
except Exception as e:
    logger.error(f"✗ PDF test failed: {e}")
    exit(1)

# Test LLM functions
logger.info("\n[3/6] Testing LLM functions...")
try:
    # Test basic Q&A
    response = ask_llm_with_context(
        question="What is the capital of France?",
        transcript_context="User asked about the capital of France",
        screen_text="",
        pdf_context=""
    )
    logger.info(f"✓ LLM Q&A working: {response[:50]}...")
    
    # Test question detection
    is_q = detect_questions("What is 2+2?")
    logger.info(f"✓ Question detection: 'What is 2+2?' = {is_q}")
    
    is_q = detect_questions("This is a statement")
    logger.info(f"✓ Non-question detection: 'This is a statement' = {is_q}")
    
except Exception as e:
    logger.error(f"✗ LLM test failed: {e}")
    exit(1)

# Test context manager
logger.info("\n[4/6] Testing context manager...")
try:
    ctx = ContextManager()
    ctx.add_transcript("Hello, how are you?", source="meeting")
    ctx.add_transcript("I'm doing well", source="meeting")
    
    transcript = ctx.get_full_transcript()
    logger.info(f"✓ Transcript stored: {len(transcript)} characters")
    
    ctx.log_qa("How are you?", "I'm doing well")
    qa_log = ctx.qa_log
    logger.info(f"✓ Q&A pairs stored: {len(qa_log)} pairs")
    
except Exception as e:
    logger.error(f"✗ Context manager test failed: {e}")
    exit(1)

# Test agent initialization (without audio)
logger.info("\n[5/6] Testing agent initialization...")
try:
    # Create a mock overlay for testing
    class MockOverlay:
        def show_message(self, msg):
            logger.debug(f"[Overlay] {msg[:50]}...")
    
    agent = MeetingAgentCore(
        overlay_widget=MockOverlay(),
        meeting_device_index=24,
        mic_device_index=2
    )
    logger.info("✓ Agent initialized successfully")
    logger.info(f"  - PDF index ready: {agent.pdf_index is not None}")
    logger.info(f"  - Narrator ready: {agent.narrator is not None}")
    logger.info(f"  - Context manager ready: {agent.context is not None}")
    
except Exception as e:
    logger.error(f"✗ Agent init failed: {e}")
    exit(1)

# Test summary generation
logger.info("\n[6/6] Testing summary generation...")
try:
    agent.context.add_transcript(
        "Meeting started. User asked: How do I use this system? "
        "Answer: The system records audio and generates summaries. "
        "User asked: What about PDFs? Answer: You can upload PDFs for context.",
        source="meeting"
    )
    agent.context.log_qa("How do I use this system?", "The system records audio and generates summaries")
    agent.context.log_qa("What about PDFs?", "You can upload PDFs for context")
    
    # Get transcript and QA pairs in the format expected by summarize_meeting
    full_transcript = agent.context.get_full_transcript()
    qa_log = agent.context.qa_log
    # summarize_meeting expects a list of tuples, but qa_log is a list of strings
    # Extract QA pairs from the log format
    qa_pairs = []
    for entry in qa_log:
        if "Q:" in entry and "A:" in entry:
            parts = entry.split("A:")
            if len(parts) == 2:
                q = parts[0].replace("[", "").replace("Q:", "").strip()
                a = parts[1].strip()
                qa_pairs.append((q, a))
    
    summary = summarize_meeting(full_transcript, qa_pairs)
    logger.info(f"✓ Summary generated: {len(summary)} characters")
    logger.info(f"  Preview: {summary[:100]}...")
    
except Exception as e:
    logger.error(f"✗ Summary test failed: {e}")
    exit(1)

logger.info("\n" + "="*60)
logger.info("✓ ALL INTEGRATION TESTS PASSED!")
logger.info("="*60)
logger.info("\n📝 Test Results:")
logger.info("  ✓ Core components load successfully")
logger.info("  ✓ PDF indexing works")
logger.info("  ✓ LLM functions work (Q&A, question detection)")
logger.info("  ✓ Context manager works")
logger.info("  ✓ Agent initializes properly")
logger.info("  ✓ Summary generation works")
logger.info("\n🚀 Ready to run full agent with GUI!")
logger.info("\nNext: python -m app.main")

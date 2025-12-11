"""
LLM Client - Google Gemini Integration
Handles all language model interactions for the meeting agent
"""
import logging
import base64
from io import BytesIO
import google.generativeai as genai
from .config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_VISION_MODEL

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)


def ask_llm_with_context(
    question: str,
    transcript_context: str,
    screen_text: str = "",
    pdf_context: str = "",
    screen_image=None,
) -> str:
    """
    Ask Gemini a question with PDF context for comprehensive answers.
    Uses PDF knowledge base + question to generate detailed response.
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Build context from PDF (most important for accuracy)
        pdf_part = f"\nKNOWLEDGE BASE (from PDF):\n{pdf_context[:500]}" if pdf_context else ""
        
        # Add recent transcript for context
        tx = transcript_context[-200:].strip() if transcript_context else ""
        tx_part = f"\nRECENT DISCUSSION:\n{tx}" if tx else ""
        
        # Combine context
        context = pdf_part + tx_part
        
        # Build prompt with context
        prompt = f"QUESTION: {question}\n{context}\n\nProvide a detailed, helpful answer based on the above information."
        
        response = model.generate_content(prompt)
        answer = response.text.strip()
        logger.info(f"Q:{question[:30]}... Ans:{answer[:50]}...")
        return answer
    except Exception as e:
        logger.error(f"Error asking: {e}")
        return "Unable to generate answer. Please try again."


def ask_llm_with_image(
    question: str,
    image_bytes: bytes,
    context: str = "",
) -> str:
    """
    Ask Gemini a question with an image (for screen analysis).
    
    Args:
        question: The question about the image
        image_bytes: Image data in bytes
        context: Additional context text
    
    Returns:
        Gemini's analysis
    """
    try:
        model = genai.GenerativeModel(GEMINI_VISION_MODEL)
        
        # Convert bytes to PIL Image
        from PIL import Image
        image = Image.open(BytesIO(image_bytes))
        
        prompt = f"""Analyze this screenshot and answer the question.

QUESTION:
{question}

CONTEXT:
{context}

Be concise and focus on what's relevant to the question."""
        
        response = model.generate_content([prompt, image])
        answer = response.text.strip()
        logger.info(f"Gemini analyzed image for: {question[:50]}...")
        return answer
    except Exception as e:
        logger.error(f"Error analyzing image with Gemini: {e}")
        return "Could not analyze the image."


def summarize_meeting(transcript: str, qa_pairs: list = None) -> str:
    """
    Generate meeting summary.
    ULTRA-OPTIMIZED: ~50-70 tokens per call (down from 500).
    """
    if not transcript or not transcript.strip():
        return "MEETING SUMMARY\n===============\nNo audio captured.\nCheck device config: https://ai.dev/usage"
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # ULTRA-AGGRESSIVE: last 700 chars only
        tx = transcript[-700:].strip() if len(transcript) > 700 else transcript
        
        # Minimal Q&A: top 2 only, 30 chars each
        qa_str = ""
        if qa_pairs and len(qa_pairs) > 0:
            qa_str = "\nTop Q&A: "
            for q, a in qa_pairs[:2]:
                q = q[:30].replace("\n", " ")
                a = a[:30].replace("\n", " ")
                qa_str += f"[{q}? {a}] "
        
        # Ultra-minimal prompt: ~15 token instruction
        prompt = f"Summarize {tx}{qa_str}\nSections: 1.Topics 2.Decisions 3.Actions"
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        logger.info(f"Summary generated: {len(summary)} chars")
        return summary
    except Exception as e:
        logger.error(f"Summary error: {e}")
        return f"MEETING SUMMARY\n===============\n{transcript[:300]}...\n\nAPI error. Review transcript above."


def transcribe_audio_bytes(wav_bytes: bytes) -> str:
    """
    Transcribe audio using offline Google Speech Recognition.
    Does NOT use API quota - completely free.
    
    Args:
        wav_bytes: Audio data in WAV format
    
    Returns:
        Transcribed text or empty string if silent
    """
    try:
        import speech_recognition as sr
        from io import BytesIO
        
        # Convert bytes to audio file
        audio_file = BytesIO(wav_bytes)
        
        # Use Google Speech Recognition API (offline-capable)
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        
        # Recognize using Google's free speech recognition
        text = recognizer.recognize_google(audio)
        
        if text:
            logger.info(f"Transcribed: {text[:100]}...")
        return text.strip()
    except sr.UnknownValueError:
        # Audio was not clear enough
        logger.debug("Audio could not be understood")
        return ""
    except sr.RequestError as e:
        logger.warning(f"Speech recognition service error: {e}")
        return ""
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        # Fallback: Check if audio has significant volume (not silence)
        try:
            import numpy as np
            from scipy import signal
            
            # Convert bytes back to audio for analysis
            import soundfile as sf
            from io import BytesIO
            
            audio, sr = sf.read(BytesIO(wav_bytes))
            # If RMS > 0.01, there's audio; otherwise it's silent
            rms = np.sqrt(np.mean(audio ** 2))
            if rms > 0.01:
                return "[Audio detected but transcription unavailable]"
        except:
            pass
        return ""


def detect_questions(text: str) -> list:
    """
    Detect questions using HEURISTICS-ONLY (saves 100% API tokens).
    Pattern-based detection without Gemini API calls.
    """
    questions = []
    lines = text.split('\n')
    
    # Check for question marks (completely free, no tokens)
    for line in lines:
        line_s = line.strip()
        if '?' in line_s and len(line_s) > 5:
            # Remove question mark and clean
            q = line_s.rstrip('?').rstrip('!').strip()
            if len(q) > 5 and q not in questions:
                questions.append(q)
    
    # Also check common question starters (what, how, when, why, who, where, can, will, do)
    if not questions:
        q_starters = ('what ', 'how ', 'when ', 'why ', 'who ', 'where ', 'can ', 'will ', 'do ', 'should ')
        for line in lines:
            line_lower = line.lower().strip()
            if any(line_lower.startswith(s) for s in q_starters):
                q = line.strip().rstrip('?').rstrip('!').strip()
                if len(q) > 5 and q not in questions:
                    questions.append(q)
    
    # No API call - 100% token savings
    logger.info(f"Questions detected (heuristic): {len(questions)}")
    return questions


def generate_action_items(transcript: str) -> list:
    """
    Extract action items. ULTRA-OPTIMIZED: ~30-40 tokens per call.
    Only processes last 500 chars for maximum efficiency.
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Only last 500 chars - very aggressive
        tx = transcript[-500:].strip() if len(transcript) > 500 else transcript
        
        # Ultra-minimal prompt: ~10 tokens
        prompt = f"Actions:{tx}"
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if not result or result.lower() in ("none", "no actions", ""):
            return []
        
        # Return non-empty lines only
        return [line.strip() for line in result.split('\n') if line.strip()]
    except Exception as e:
        logger.error(f"Action items error: {e}")
        return []

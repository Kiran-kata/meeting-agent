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
    Ask Gemini a question with meeting context.
    
    Args:
        question: The question to answer
        transcript_context: Recent meeting transcript
        screen_text: Text currently on screen
        pdf_context: Relevant PDF content
        screen_image: Optional screenshot
    
    Returns:
        Gemini's answer
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # AGGRESSIVE truncation to minimize tokens
        transcript_context = transcript_context[-500:] if transcript_context else ""
        pdf_context = pdf_context[:200] if pdf_context else ""
        screen_text = screen_text[:150] if screen_text else ""
        
        # Ultra-minimal prompt format - ~30 tokens vs 200+ before
        context_parts = []
        if transcript_context.strip():
            context_parts.append(f"Recent: {transcript_context}")
        if screen_text.strip():
            context_parts.append(f"Screen: {screen_text}")
        if pdf_context.strip():
            context_parts.append(f"Docs: {pdf_context}")
        
        context_str = "\n".join(context_parts) if context_parts else "No context available"
        
        # Minimal prompt: uses ~5x fewer tokens
        prompt = f"Q: {question}\n\nContext:\n{context_str}\n\nAnswer concisely."
        
        response = model.generate_content(prompt)
        answer = response.text.strip()
        logger.info(f"Gemini answered question: {question[:50]}...")
        return answer
    except Exception as e:
        logger.error(f"Error asking Gemini: {e}")
        return "Sorry, I encountered an error processing your question."


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
    Generate a comprehensive meeting summary.
    
    Args:
        transcript: Full meeting transcript
        qa_pairs: List of (question, answer) tuples from the meeting
    
    Returns:
        Meeting summary
    """
    # If no transcript, return a default message
    if not transcript or transcript.strip() == "":
        default_summary = """
MEETING SUMMARY
===============

No audio was captured during this meeting.

Possible reasons:
- Microphone/meeting audio device not properly configured
- Gemini API quota exceeded
- No audio was actually present during the meeting

To troubleshoot:
1. Check audio device indices (run: python -c "import sounddevice as sd; print(sd.query_devices())")
2. Update MEETING_DEVICE_INDEX and MIC_DEVICE_INDEX in config.py
3. Check Gemini API quota at: https://ai.dev/usage?tab=rate-limit
4. Ensure audio is being captured from the correct device
"""
        return default_summary
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # AGGRESSIVE truncation: last 1200 chars only (~180 tokens)
        transcript = transcript[-1200:] if len(transcript) > 1200 else transcript
        
        # Only include top 3 Q&A pairs (vs all)
        qa_text = ""
        if qa_pairs and len(qa_pairs) > 0:
            qa_text = "\n\nTop Q&A:"
            for q, a in qa_pairs[:3]:
                # Truncate each to 60 chars
                q_short = q[:60].replace("\n", " ")
                a_short = a[:60].replace("\n", " ")
                qa_text += f"\nQ: {q_short}...\nA: {a_short}..."
        
        # MINIMAL prompt: 3 sections vs 4, no formatting instructions
        prompt = f"""Summarize in 3 sections:\n1. Topics\n2. Decisions\n3. Actions\n\nTranscript:{transcript}{qa_text}"""
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        logger.info("Meeting summary generated")
        return summary
    except Exception as e:
        logger.error(f"Error summarizing meeting: {e}")
        # Return fallback summary with what we have
        fallback = f"""
MEETING SUMMARY (Auto-generated)
================================

TRANSCRIPT:
{transcript}
{qa_text if qa_pairs else ''}

NOTE: Could not generate AI summary due to API limitations.
Please review the raw transcript above.
"""
        return fallback


def transcribe_audio_bytes(wav_bytes: bytes) -> str:
    """
    Transcribe audio using Gemini's audio transcription capability.
    Falls back to silence detection if API is unavailable.
    
    Args:
        wav_bytes: Audio data in WAV format
    
    Returns:
        Transcribed text or empty string if silent
    """
    try:
        # Use Gemini's audio transcription
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Encode audio as base64
        audio_data = base64.standard_b64encode(wav_bytes).decode('utf-8')
        
        # Create audio part for Gemini
        audio_part = {
            'mime_type': 'audio/wav',
            'data': audio_data
        }
        
        # Ask Gemini to transcribe
        response = model.generate_content([
            "Please transcribe this audio and return only the transcribed text, nothing else.",
            audio_part
        ])
        
        text = response.text.strip()
        if text:
            logger.info(f"Transcribed: {text[:100]}...")
        return text
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
    Detect questions in text using HEURISTICS FIRST, then Gemini if needed.
    Saves tokens by avoiding API calls for obvious cases.
    
    Args:
        text: Text to analyze
    
    Returns:
        List of detected questions
    """
    # HEURISTIC-FIRST approach: use patterns before calling API
    questions = []
    lines = text.split('\n')
    
    # Find lines with question marks (free, no tokens)
    for line in lines:
        line_stripped = line.strip()
        if '?' in line_stripped and len(line_stripped) > 5:
            questions.append(line_stripped.rstrip('?'))
    
    if questions:
        return questions  # Found via heuristics, no API call needed!
    
    # Only call API if no obvious questions found
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"Questions in text (one per line, no intro):\\n{text[-300:]}"  # Only last 300 chars!
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if result.lower() != "none":
            questions = [q.strip() for q in result.split('\n') if q.strip()]
        return questions
    except Exception as e:
        logger.error(f"Error detecting questions: {e}")
        return []


def generate_action_items(transcript: str) -> list:
    """
    Extract action items (OPTIMIZED for tokens - only processes last 600 chars).
    
    Args:
        transcript: Meeting transcript (will be truncated to last 600 chars)
    
    Returns:
        List of action items with owner and deadline if available
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Only use last 600 chars to minimize tokens
        transcript_short = transcript[-600:] if len(transcript) > 600 else transcript
        
        # Ultra-minimal prompt
        prompt = f"Actions from:\\n{transcript_short}"
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if result.lower() == "none" or not result:
            return []
        
        return result.split('\n')
    except Exception as e:
        logger.error(f"Error generating action items: {e}")
        return []
    except Exception as e:
        logger.error(f"Error generating action items: {e}")
        return []

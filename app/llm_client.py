"""
LLM Client - Google Gemini Integration
Handles all language model interactions for the meeting agent
"""
import logging
import base64
from io import BytesIO
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_VISION_MODEL

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
        
        prompt = f"""You are a helpful meeting assistant. Answer questions based on the provided context.

QUESTION:
{question}

CONTEXT:
[Meeting Transcript]
{transcript_context}

[Screen Content]
{screen_text}

[PDF Documents]
{pdf_context}

Instructions: Answer only using the provided context. If you don't have enough information, say so clearly.
Be concise and practical."""
        
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
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        qa_text = ""
        if qa_pairs:
            qa_text = "\n\nQUESTIONS & ANSWERS:\n"
            for q, a in qa_pairs:
                qa_text += f"\nQ: {q}\nA: {a}\n"
        
        prompt = f"""Please create a structured meeting summary with the following sections:

1. **Main Topics** - What was discussed
2. **Key Decisions** - What was decided
3. **Action Items** - What needs to be done (who, what, when)
4. **Risks/Concerns** - Any open issues or blockers

TRANSCRIPT:
{transcript}
{qa_text}

Format the summary clearly with headers and bullet points."""
        
        response = model.generate_content(prompt)
        summary = response.text.strip()
        logger.info("Meeting summary generated")
        return summary
    except Exception as e:
        logger.error(f"Error summarizing meeting: {e}")
        return "Could not generate summary."


def transcribe_audio_bytes(wav_bytes: bytes) -> str:
    """
    Transcribe audio using Gemini's audio transcription capability.
    
    Args:
        wav_bytes: Audio data in WAV format
    
    Returns:
        Transcribed text
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
        return ""


def detect_questions(text: str) -> list:
    """
    Detect questions in text using Gemini.
    
    Args:
        text: Text to analyze
    
    Returns:
        List of detected questions
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""Extract all questions from this text. Return ONLY the questions, one per line.
If there are no questions, return "None".

TEXT:
{text}"""
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if result.lower() == "none":
            return []
        
        questions = [q.strip() for q in result.split('\n') if q.strip()]
        return questions
    except Exception as e:
        logger.error(f"Error detecting questions: {e}")
        return []


def generate_action_items(transcript: str) -> list:
    """
    Extract action items from meeting transcript.
    
    Args:
        transcript: Meeting transcript
    
    Returns:
        List of action items with owner and deadline if available
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""From this meeting transcript, extract action items in this format:
- Action: [what needs to be done]
  Owner: [who is responsible] (if mentioned)
  Deadline: [when it needs to be done] (if mentioned)

If there are no action items, return "None".

TRANSCRIPT:
{transcript}"""
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if result.lower() == "none":
            return []
        
        return result.split('\n')
    except Exception as e:
        logger.error(f"Error generating action items: {e}")
        return []

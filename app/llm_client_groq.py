"""LLM Client using Groq API (FREE)"""

import logging
from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)


def ask_llm(question: str, context: str = "") -> str:
    """
    Ask Groq LLM a question with optional context.
    
    Args:
        question: The question to ask
        context: Optional context for the question
        
    Returns:
        The response from the LLM
    """
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant in a meeting. Provide concise and relevant answers."
            }
        ]
        
        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            })
        else:
            messages.append({
                "role": "user",
                "content": question
            })
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error asking LLM: {e}")
        return ""


def ask_llm_with_context(question: str, transcript_context: str, screen_text: str = "", pdf_context: str = "", screen_image=None) -> str:
    """
    Ask LLM with meeting context and optional PDF/screen context.
    
    Args:
        question: The question to ask
        transcript_context: Recent meeting transcript
        screen_text: Text from screen
        pdf_context: Optional context from PDFs
        screen_image: Optional image (not used in Groq, but kept for compatibility)
        
    Returns:
        The response from the LLM
    """
    context = f"Recent meeting:\n{transcript_context}"
    
    if screen_text:
        context += f"\n\nWhat's on screen:\n{screen_text}"
    
    if pdf_context:
        context += f"\n\nRelevant documents:\n{pdf_context}"
    
    context += "\n\nAnswer only using the provided context. If unsure, say you don't have enough information."
    
    return ask_llm(question, context)


def summarize_meeting(full_transcript: str, qa_log: str = "") -> str:
    """
    Generate a summary of the meeting.
    
    Args:
        full_transcript: The full meeting transcript
        qa_log: Optional Q&A log
        
    Returns:
        The summary
    """
    try:
        prompt = f"TRANSCRIPT:\n{full_transcript}"
        if qa_log:
            prompt += f"\n\nQUESTIONS & ANSWERS:\n{qa_log}"
        
        prompt += "\n\nCreate a structured summary with: 1) Main topics, 2) Key decisions, 3) Action items, 4) Open questions"
        
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at summarizing meetings. Be clear, concise, and actionable."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.5
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error summarizing meeting: {e}")
        return ""


def extract_key_points(text: str) -> list:
    """
    Extract key points from text.
    
    Args:
        text: Text to extract from
        
    Returns:
        List of key points
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Extract the main key points from the given text. Return as a numbered list, one per line."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=500,
            temperature=0.5
        )
        
        points = response.choices[0].message.content.split('\n')
        return [p.strip() for p in points if p.strip() and not p.strip().isdigit()]
    except Exception as e:
        logger.error(f"Error extracting key points: {e}")
        return []


def transcribe_audio_bytes(wav_bytes: bytes) -> str:
    """
    Transcribe audio using Groq's Whisper API (FREE).
    This uses Groq's free speech-to-text service.
    
    Args:
        wav_bytes: Audio bytes in WAV format
        
    Returns:
        Transcribed text
    """
    try:
        from io import BytesIO
        
        # Use Groq's speech-to-text (if available)
        # For now, we'll use Whisper.cpp locally
        logger.info("Audio transcription would use Whisper.cpp locally")
        return ""
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return ""

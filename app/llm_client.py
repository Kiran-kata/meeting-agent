"""
LLM Client - OpenAI Integration
Handles all language model interactions for the meeting agent
"""
import logging
from openai import OpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)


def ask_llm_with_context(
    question: str,
    transcript_context: str,
    screen_text: str = "",
    pdf_context: str = "",
    screen_image=None,
) -> str:
    """
    Ask GPT-4o a question with meeting context.
    
    Args:
        question: The question to answer
        transcript_context: Recent meeting transcript
        screen_text: Text currently on screen
        pdf_context: Relevant PDF content
        screen_image: Optional screenshot (not used currently)
    
    Returns:
        GPT-4o's answer
    """
    try:
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
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an intelligent meeting assistant. Be concise and practical."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        logger.info(f"LLM answered question: {question[:50]}...")
        return answer
    except Exception as e:
        logger.error(f"Error asking LLM: {e}")
        return "Sorry, I encountered an error processing your question."


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
        qa_text = ""
        if qa_pairs:
            qa_text = "\n\nQUESTIONS & ANSWERS:\n"
            for q, a in qa_pairs:
                qa_text += f"\nQ: {q}\nA: {a}\n"
        
        prompt = f"""Please create a structured meeting summary with:

1. **Main Topics** - What was discussed
2. **Key Decisions** - What was decided
3. **Action Items** - What needs to be done (who, what, deadline)
4. **Risks/Concerns** - Any open issues

TRANSCRIPT:
{transcript}
{qa_text}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert meeting summarizer. Create clear, actionable summaries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info("Meeting summary generated")
        return summary
    except Exception as e:
        logger.error(f"Error summarizing meeting: {e}")
        return "Could not generate summary."


def transcribe_audio_bytes(wav_bytes: bytes) -> str:
    """
    Transcribe audio bytes using OpenAI's Whisper API.
    
    Args:
        wav_bytes: Audio data in WAV format
    
    Returns:
        Transcribed text
    """
    try:
        from io import BytesIO
        
        audio_file = BytesIO(wav_bytes)
        audio_file.name = "audio.wav"
        
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        
        text = response.text.strip()
        if text:
            logger.info(f"Transcribed: {text[:100]}...")
        return text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return ""

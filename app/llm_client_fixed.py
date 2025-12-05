from io import BytesIO
import base64
from typing import List, Optional
import logging

from groq import Groq
from .config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)


def ask_llm_with_context(
    question: str,
    transcript_context: str,
    screen_text: str = "",
    pdf_context: str = "",
    screen_image=None,
) -> str:
    """
    Sends a prompt to Groq LLM with meeting context.
    """
    content_text = f"""
QUESTION:
{question}

[RECENT TRANSCRIPT]
{transcript_context}

[SCREEN TEXT]
{screen_text}

[PDF CONTEXT]
{pdf_context}
    """.strip()

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": content_text}],
            temperature=0.1,
            max_tokens=500
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error with Groq LLM: {e}")
        return ""


def summarize_meeting(full_transcript: str, qa_log: str = "") -> str:
    """
    Generate a structured meeting summary using Groq.
    """
    prompt = f"""
You are a meeting summarizer.

FULL TRANSCRIPT:
{full_transcript}

QUESTIONS AND ANSWERS:
{qa_log}

Produce a concise, structured summary with:

1. Main topics discussed (bullet points)
2. Key decisions
3. Action items (who / what / by when)
4. Any open questions or risks
    """.strip()

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You summarize meetings clearly and concisely."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.5
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error summarizing meeting: {e}")
        return ""


def transcribe_audio_bytes(wav_bytes: bytes) -> str:
    """
    Transcribe audio using Whisper.cpp (local) or Groq API.
    For now, returns empty string - will be handled by whisper.cpp
    """
    try:
        logger.info("Audio would be transcribed using Whisper.cpp locally")
        return ""
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return ""

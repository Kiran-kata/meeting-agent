import google.generativeai as genai
from .config import GEMINI_API_KEY, GEMINI_MODEL
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

QUESTION_CUES = [
    "what is", "what are", "how do", "how does", "how to",
    "why is", "could you", "can you", "would you", "should we",
    "is there", "does it", "what happens", "what does",
]


def _is_question_heuristic(text: str) -> bool:
    t = text.lower().strip()
    if "?" in t:
        logger.info(f"Question detected (heuristic - has ?): {text[:100]}")
        return True
    result = any(cue in t for cue in QUESTION_CUES)
    if result:
        logger.info(f"Question detected (heuristic - cue found): {text[:100]}")
    return result


def _is_question_llm(text: str) -> bool:
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""Text: {text}

Is this text someone in a meeting asking a question that expects an explanation or answer?
Reply with just YES or NO."""

        resp = model.generate_content(prompt)
        ans = resp.text.strip().upper()
        is_q = ans.startswith("Y")
        if is_q:
            logger.info(f"Question detected (LLM): {text[:100]}")
        return is_q
    except Exception as e:
        logger.error(f"Error in LLM question detection: {e}")
        return False


def is_question(text: str) -> bool:
    # Use only heuristic detection to avoid quota issues
    # In production, add LLM verification: return _is_question_llm(text)
    return _is_question_heuristic(text)


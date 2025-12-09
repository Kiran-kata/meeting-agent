import google.generativeai as genai
from .config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

QUESTION_CUES = [
    "what is", "what are", "how do", "how does", "how to",
    "why is", "could you", "can you", "would you", "should we",
    "is there", "does it", "what happens", "what does",
]


def _is_question_heuristic(text: str) -> bool:
    t = text.lower().strip()
    if "?" in t:
        return True
    return any(cue in t for cue in QUESTION_CUES)


def _is_question_llm(text: str) -> bool:
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = f"""Text: {text}

Is this text someone in a meeting asking a question that expects an explanation or answer?
Reply with just YES or NO."""

    resp = model.generate_content(prompt)
    ans = resp.text.strip().upper()
    return ans.startswith("Y")


def is_question(text: str) -> bool:
    if _is_question_heuristic(text):
        return True
    return _is_question_llm(text)

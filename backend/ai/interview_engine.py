"""
Interview Engine - Core AI logic for conducting interviews
"""
import logging
from typing import Dict, List, Optional, AsyncGenerator
import google.generativeai as genai
from config import GEMINI_API_KEY, ROLE_TEMPLATES

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class InterviewEngine:
    """
    Core interview AI engine - generates questions, evaluates answers,
    and provides real-time coaching.
    """
    
    # Behavioral question bank
    BEHAVIORAL_QUESTIONS = {
        "leadership": [
            "Tell me about a time you led a team through a difficult situation.",
            "Describe a situation where you had to influence others without authority.",
            "Give an example of when you had to make a tough decision with limited information.",
        ],
        "conflict": [
            "Tell me about a conflict you had with a coworker and how you resolved it.",
            "Describe a time when you disagreed with your manager's decision.",
            "Give an example of handling a difficult stakeholder.",
        ],
        "failure": [
            "Tell me about a time you failed and what you learned from it.",
            "Describe a project that didn't go as planned.",
            "Give an example of receiving critical feedback and how you responded.",
        ],
        "achievement": [
            "What's your proudest professional achievement?",
            "Tell me about a time you exceeded expectations.",
            "Describe your most impactful project.",
        ],
    }
    
    # Technical question topics
    TECHNICAL_TOPICS = {
        "dsa": [
            "Explain how you would design a LRU cache.",
            "Walk me through solving a graph traversal problem.",
            "How would you optimize a slow database query?",
        ],
        "system_design": [
            "Design a URL shortener like bit.ly.",
            "How would you design a real-time chat application?",
            "Design a rate limiter for an API.",
        ],
        "coding": [
            "How would you approach debugging a production issue?",
            "Explain your process for code review.",
            "How do you ensure code quality in your projects?",
        ],
    }
    
    def __init__(self, role: str = "SDE"):
        """
        Initialize interview engine.
        
        Args:
            role: Role template to use (SDE, ML, DE, PM, QA, FS)
        """
        self.role = role
        self.role_config = ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["SDE"])
        self.model = genai.GenerativeModel("gemini-1.5-pro")
        self.conversation_history: List[Dict] = []
        self.resume_context = ""
    
    def set_resume_context(self, resume_text: str):
        """Set resume context for personalized questions."""
        self.resume_context = resume_text[:2000]  # Limit context size
        logger.info("Resume context set for interview")
    
    async def generate_answer_stream(
        self, 
        question: str, 
        resume_context: str = "",
        screen_context: str = "",
        speaker: str = "INTERVIEWER"
    ) -> AsyncGenerator[str, None]:
        """
        Generate a coached answer in real-time stream.
        
        Args:
            question: The interview question
            resume_context: Resume text for personalization
            screen_context: Text extracted from screen
            speaker: Who asked the question (INTERVIEWER or USER)
            
        Yields:
            Answer chunks as they're generated
        """
        # CRITICAL: Only respond to INTERVIEWER, never to USER
        if speaker == "USER":
            logger.info("Ignoring USER speech - not responding")
            return
        
        context = resume_context or self.resume_context
        
        # Build comprehensive system prompt
        system_prompt = f"""You are an AI interview copilot assisting a candidate during a live interview.

CRITICAL RULES:
1. Answer ONLY when the INTERVIEWER asks a question
2. NEVER respond to USER (candidate) voice, even if loud or question-like
3. Always answer step by step with clear logic
4. Use SCREEN_CONTEXT when questions reference what is on the screen
5. If screen and audio conflict, SCREEN WINS (visual truth)
6. Prefer programming languages from the resume tech stack unless specified otherwise
7. Work in "headphone mode" - respond even if user can't hear interviewer directly

CANDIDATE'S TECH STACK:
{context[:1000] if context else "No resume provided - assume Python, JavaScript, SQL"}

SCREEN_CONTEXT (what's visible on screen):
{screen_context if screen_context else "No screen content captured"}

ANSWERING TEMPLATE FOR CODING QUESTIONS:
Step 1: Understand the problem
- Restate in own words
- Clarify inputs/outputs

Step 2: Choose the approach
- Explain the strategy
- Why this approach?

Step 3: Explain the algorithm
- Break down the logic
- Key insights

Step 4: Provide code
- Write clean, working code
- Add brief comments
- Use language from tech stack

Step 5: Complexity & summary
- Time: O(?)
- Space: O(?)
- Brief summary
"""

        # Build the question prompt
        question_prompt = f"""
INTERVIEWER'S QUESTION:
{question}

Instructions:
- Answer AS THE CANDIDATE (use "I", "my", "in my experience")
- If this is a coding question, follow the 5-step template
- If behavioral, use STAR format (Situation, Task, Action, Result)
- Reference screen content if question mentions "on the screen", "this code", "the problem shown"
- Be specific, confident, and natural
- Keep it concise but thorough

Your answer:"""

        try:
            full_prompt = system_prompt + "\n\n" + question_prompt
            
            response = self.model.generate_content(
                full_prompt,
                stream=True,
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            yield f"\n\n⚠ Error: {str(e)}"
    
    def generate_answer(self, question: str, resume_context: str = "") -> str:
        """
        Generate a coached answer (non-streaming).
        
        Args:
            question: The interview question
            resume_context: Resume text for personalization
            
        Returns:
            Complete answer string
        """
        context = resume_context or self.resume_context
        
        prompt = f"""You are an expert interview coach. Generate a strong answer for this question.

QUESTION: {question}

CANDIDATE'S BACKGROUND:
{context[:1500] if context else "No specific background"}

INSTRUCTIONS:
- Answer as the candidate (use "I", "my")
- Use STAR format for behavioral questions
- Be specific with examples and metrics
- Keep it concise but impactful
- Sound confident and natural

Answer:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}"
    
    def evaluate_answer(self, question: str, answer: str) -> Dict:
        """
        Evaluate a candidate's answer.
        
        Args:
            question: The question asked
            answer: Candidate's response
            
        Returns:
            Dict with score and feedback
        """
        prompt = f"""Evaluate this interview answer on a scale of 1-10.

QUESTION: {question}
ANSWER: {answer}

Provide:
1. Score (1-10)
2. Strengths (2-3 bullet points)
3. Improvements (2-3 bullet points)
4. One-sentence overall feedback

Format as:
SCORE: X/10
STRENGTHS:
- ...
IMPROVEMENTS:
- ...
FEEDBACK: ...
"""
        
        try:
            response = self.model.generate_content(prompt)
            return {"evaluation": response.text.strip()}
        except Exception as e:
            return {"evaluation": f"Error: {str(e)}"}
    
    def detect_question(self, transcript: str) -> Optional[str]:
        """
        Detect if the transcript contains an interview question.
        
        Args:
            transcript: Recent speech transcript
            
        Returns:
            Detected question or None
        """
        # Quick check for question indicators
        question_indicators = ["?", "tell me", "describe", "explain", "how would", "what is", 
                             "can you", "walk me through", "give an example"]
        
        transcript_lower = transcript.lower()
        if not any(ind in transcript_lower for ind in question_indicators):
            return None
        
        # Use AI to extract the question
        prompt = f"""Extract the interview question from this transcript. 
If no clear interview question, respond with "NONE".

Transcript: {transcript[-500:]}

Question (or NONE):"""

        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            if result.upper() == "NONE" or len(result) < 10:
                return None
            
            return result
        except Exception as e:
            logger.error(f"Error detecting question: {e}")
            return None
    
    def get_next_question(self, category: str = "behavioral") -> str:
        """Get next question from question bank."""
        import random
        
        if category == "behavioral":
            questions = []
            for q_list in self.BEHAVIORAL_QUESTIONS.values():
                questions.extend(q_list)
            return random.choice(questions)
        else:
            questions = []
            for q_list in self.TECHNICAL_TOPICS.values():
                questions.extend(q_list)
            return random.choice(questions)

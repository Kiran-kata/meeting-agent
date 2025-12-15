"""
Parakeet-Style Decision Engine
Deterministic, transcript-driven answer generation
"""
import re
import logging
import time
from typing import Optional
from dataclasses import dataclass

from backend.audio.parakeet_audio import TranscriptEvent, Speaker

logger = logging.getLogger(__name__)


@dataclass
class QuestionIntent:
    """Detected question intent"""
    text: str
    confidence: float
    question_type: str  # "direct", "imperative", "contextual"
    

class ParakeetDecisionEngine:
    """
    Parakeet-style decision engine
    
    CRITICAL INVARIANT:
    Answer is generated ONLY if ALL are true:
    1. speaker == INTERVIEWER
    2. text is finalized (end-of-speech detected)
    3. text matches a question intent
    4. cooldown is inactive
    
    If even one fails → do nothing
    """
    
    def __init__(self):
        self.cooldown_active = False
        self.last_answer_time = 0
        self.cooldown_duration = 2.0  # seconds
        
        # Question detection patterns (deterministic NLP + regex)
        self.imperative_verbs = [
            'explain', 'walk me through', 'solve', 'design', 
            'implement', 'write', 'create', 'build', 'develop',
            'describe', 'tell me', 'show me', 'demonstrate',
            'code', 'program', 'debug', 'fix', 'optimize'
        ]
        
        self.contextual_phrases = [
            'on the screen', 'based on this', 'look at this',
            'see here', 'in this code', 'this problem',
            'given this', 'for this', 'with this'
        ]
        
        logger.info("Parakeet decision engine initialized")
    
    def should_generate_answer(self, event: TranscriptEvent, screen_changed: bool = False) -> bool:
        """
        Gate function: Decide if we should generate an answer
        
        ALL conditions must be true:
        1. speaker == INTERVIEWER
        2. text is finalized (guaranteed by transcript event)
        3. text matches question intent
        4. cooldown is inactive
        
        Args:
            event: Finalized transcript event
            screen_changed: Whether screen context changed
            
        Returns:
            True if should generate answer, False otherwise
        """
        # Condition 1: Must be INTERVIEWER
        if event.speaker != Speaker.INTERVIEWER:
            logger.debug(f"❌ Gate failed: speaker={event.speaker.name} (not INTERVIEWER)")
            return False
        
        # Condition 2: Text finalized (guaranteed by TranscriptEvent)
        # This is enforced by the audio processor
        
        # Condition 3: Must match question intent
        intent = self.detect_question_intent(event.text)
        if not intent:
            logger.debug(f"❌ Gate failed: no question intent in '{event.text[:30]}...'")
            return False
        
        # Condition 4: Cooldown must be inactive
        if self.cooldown_active:
            logger.debug(f"❌ Gate failed: cooldown active")
            return False
        
        # All conditions passed
        logger.info(f"✅ Gate PASSED: Generating answer for question")
        return True
    
    def detect_question_intent(self, text: str) -> Optional[QuestionIntent]:
        """
        Question Intent Detection (PARAKEET STYLE)
        
        Trigger if any of the following are true:
        1. Ends with ?
        2. Starts with imperative verb
        3. References visible context
        
        This is deterministic NLP + regex (NO ML MAGIC)
        
        Args:
            text: Transcript text
            
        Returns:
            QuestionIntent if detected, None otherwise
        """
        text_lower = text.lower().strip()
        
        # Rule 1: Direct question (ends with ?)
        if text.endswith('?'):
            return QuestionIntent(
                text=text,
                confidence=0.95,
                question_type="direct"
            )
        
        # Rule 2: Imperative verb (command)
        for verb in self.imperative_verbs:
            if text_lower.startswith(verb) or f" {verb} " in text_lower:
                return QuestionIntent(
                    text=text,
                    confidence=0.90,
                    question_type="imperative"
                )
        
        # Rule 3: Contextual reference (screen/code)
        for phrase in self.contextual_phrases:
            if phrase in text_lower:
                return QuestionIntent(
                    text=text,
                    confidence=0.85,
                    question_type="contextual"
                )
        
        # No question intent detected
        return None
    
    def activate_cooldown(self):
        """
        Activate cooldown after generating answer
        
        CRITICAL: This prevents double answers and jitter
        """
        self.cooldown_active = True
        self.last_answer_time = time.time()
        logger.info("🔒 Cooldown activated")
    
    def release_cooldown(self, reason: str = "interviewer spoke"):
        """
        Release cooldown
        
        Cooldown ends only when:
        1. Interviewer speaks again, OR
        2. Screen context changes
        
        Args:
            reason: Why cooldown was released
        """
        if self.cooldown_active:
            self.cooldown_active = False
            logger.info(f"🔓 Cooldown released: {reason}")
    
    def check_cooldown_timeout(self):
        """Check if cooldown should auto-release (timeout)"""
        if self.cooldown_active:
            elapsed = time.time() - self.last_answer_time
            if elapsed > self.cooldown_duration:
                self.release_cooldown("timeout")
    
    def on_interviewer_spoke(self):
        """Called when interviewer speaks - releases cooldown"""
        self.release_cooldown("interviewer spoke")
    
    def on_screen_changed(self):
        """Called when screen context changes - releases cooldown"""
        self.release_cooldown("screen changed")


class ParakeetAnswerFormatter:
    """
    Parakeet-style answer formatting
    
    For logic/programming questions, always uses:
    1. Problem restatement
    2. Approach explanation
    3. Step-by-step logic
    4. Code (if applicable)
    5. Complexity analysis
    
    This is TEMPLATED - not free-form
    """
    
    @staticmethod
    def format_prompt(question: str, resume_context: str = "") -> str:
        """
        Generate structured prompt for answer generation
        
        Args:
            question: The interviewer's question
            resume_context: User's resume skills/experience
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are an expert interview assistant. Answer the following question in a structured, step-by-step format.

QUESTION:
{question}

ANSWER STRUCTURE (MANDATORY):

1. PROBLEM RESTATEMENT
   - Rephrase the problem in your own words
   - Identify key requirements

2. APPROACH EXPLANATION
   - Explain your strategy at a high level
   - Justify why this approach works

3. STEP-BY-STEP LOGIC
   - Break down the solution into clear steps
   - Explain the reasoning for each step

4. CODE IMPLEMENTATION
   - Provide clean, well-commented code
   - Use best practices and proper naming
"""

        if resume_context:
            # Extract preferred language from resume
            languages = ['Python', 'Java', 'JavaScript', 'C++', 'Go']
            preferred_lang = 'Python'  # default
            for lang in languages:
                if lang.lower() in resume_context.lower():
                    preferred_lang = lang
                    break
            
            prompt += f"   - Use {preferred_lang} (from resume)\n"
        
        prompt += """
5. COMPLEXITY ANALYSIS
   - Time complexity: O(?)
   - Space complexity: O(?)
   - Explain the complexity reasoning

Keep the answer concise but complete. Focus on clarity and correctness.
"""
        return prompt
    
    @staticmethod
    def format_behavioral_prompt(question: str) -> str:
        """Format prompt for behavioral questions"""
        return f"""Answer this behavioral question using the STAR method:

QUESTION: {question}

STRUCTURE YOUR ANSWER:
- Situation: Set the context
- Task: Describe the challenge
- Action: Explain what you did
- Result: Share the outcome

Keep it concise (2-3 minutes of speaking).
"""

"""
Follow-up Question Generator - Smart probing based on answer analysis
"""
import logging
from typing import List, Optional
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class FollowUpGenerator:
    """
    Generate intelligent follow-up questions based on candidate answers.
    Detects weak points and challenges them.
    """
    
    # Follow-up templates by weakness type
    FOLLOWUP_TEMPLATES = {
        "vague": [
            "Can you be more specific about {topic}?",
            "What exactly did you do in that situation?",
            "Can you give me a concrete example?",
        ],
        "no_metrics": [
            "What was the measurable impact of your work?",
            "Can you quantify the results?",
            "What metrics did you use to measure success?",
        ],
        "no_challenges": [
            "What challenges did you face during this?",
            "What would you do differently if you could do it again?",
            "What was the hardest part of this project?",
        ],
        "incomplete_star": [
            "What was the specific outcome or result?",
            "Can you walk me through the exact actions you took?",
            "What was your specific role vs the team's role?",
        ],
        "technical_shallow": [
            "Can you explain the technical architecture in more detail?",
            "What trade-offs did you consider?",
            "How did you handle edge cases?",
        ],
    }
    
    def __init__(self, max_followups: int = 3):
        self.max_followups = max_followups
        self.followup_count = 0
        self.model = genai.GenerativeModel("gemini-1.5-pro")
    
    def should_followup(self, answer: str, score: float) -> bool:
        """Determine if a follow-up question is needed."""
        if self.followup_count >= self.max_followups:
            return False
        
        # Follow up on weak answers
        if score < 0.6:
            return True
        
        # Follow up on short answers
        if len(answer.split()) < 50:
            return True
        
        return False
    
    def detect_weakness(self, answer: str) -> str:
        """Detect the primary weakness in an answer."""
        answer_lower = answer.lower()
        word_count = len(answer.split())
        
        # Check for vagueness
        vague_indicators = ["something like", "kind of", "sort of", "basically", "stuff"]
        if any(ind in answer_lower for ind in vague_indicators):
            return "vague"
        
        # Check for missing metrics
        metric_indicators = ["%", "percent", "million", "thousand", "x", "increased", "decreased", "reduced"]
        if word_count > 30 and not any(ind in answer_lower for ind in metric_indicators):
            return "no_metrics"
        
        # Check for missing challenges
        challenge_indicators = ["challenge", "difficult", "problem", "obstacle", "hard"]
        if word_count > 50 and not any(ind in answer_lower for ind in challenge_indicators):
            return "no_challenges"
        
        # Check for incomplete STAR
        result_indicators = ["result", "outcome", "achieved", "delivered", "impact"]
        if word_count > 40 and not any(ind in answer_lower for ind in result_indicators):
            return "incomplete_star"
        
        # Check for shallow technical content
        if word_count > 30:
            technical_indicators = ["architecture", "design", "algorithm", "complexity", "scale"]
            if not any(ind in answer_lower for ind in technical_indicators):
                return "technical_shallow"
        
        return "vague"  # Default
    
    def generate_followup(self, question: str, answer: str, weakness: str = None) -> str:
        """
        Generate a follow-up question based on the answer and detected weakness.
        
        Args:
            question: Original question
            answer: Candidate's answer
            weakness: Detected weakness type (optional, will detect if not provided)
            
        Returns:
            Follow-up question string
        """
        if not weakness:
            weakness = self.detect_weakness(answer)
        
        self.followup_count += 1
        
        # Try AI-generated follow-up first
        try:
            followup = self._generate_ai_followup(question, answer, weakness)
            if followup:
                return followup
        except Exception as e:
            logger.warning(f"AI follow-up generation failed: {e}")
        
        # Fall back to template
        import random
        templates = self.FOLLOWUP_TEMPLATES.get(weakness, self.FOLLOWUP_TEMPLATES["vague"])
        return random.choice(templates)
    
    def _generate_ai_followup(self, question: str, answer: str, weakness: str) -> Optional[str]:
        """Generate follow-up using AI."""
        prompt = f"""You are an expert interviewer. Generate ONE short follow-up question.

Original question: {question}
Candidate's answer: {answer[:500]}
Weakness detected: {weakness}

Generate a probing follow-up question that:
1. Addresses the weakness
2. Pushes for more specific details
3. Is direct and concise (under 20 words)

Follow-up question:"""
        
        response = self.model.generate_content(prompt)
        return response.text.strip()
    
    def reset(self):
        """Reset follow-up counter for new question."""
        self.followup_count = 0

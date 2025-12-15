"""
Interview Scoring Engine - STAR analysis, technical scoring, and feedback
"""
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    """Individual answer score."""
    question: str
    answer: str
    star_score: float = 0.0
    technical_score: float = 0.0
    communication_score: float = 0.0
    problem_solving_score: float = 0.0
    overall_score: float = 0.0
    feedback: str = ""
    weaknesses: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class ScoringEngine:
    """
    Comprehensive interview scoring with STAR framework analysis.
    """
    
    # STAR framework keywords
    STAR_KEYWORDS = {
        "situation": ["situation", "context", "background", "when", "where", "scenario", "project"],
        "task": ["task", "goal", "objective", "responsible", "challenge", "problem", "needed"],
        "action": ["action", "did", "implemented", "developed", "created", "built", "led", "designed"],
        "result": ["result", "outcome", "achieved", "improved", "increased", "reduced", "saved", "delivered"],
    }
    
    # Technical quality indicators
    TECHNICAL_INDICATORS = {
        "positive": ["complexity", "optimize", "scale", "architecture", "design pattern", "algorithm", 
                    "trade-off", "benchmark", "performance", "efficiency", "edge case"],
        "negative": ["don't know", "not sure", "maybe", "i think", "probably", "guess"],
    }
    
    # Communication quality indicators
    COMMUNICATION_INDICATORS = {
        "positive": ["specifically", "for example", "in particular", "firstly", "secondly", "finally",
                    "to clarify", "in summary", "the key point"],
        "negative": ["um", "uh", "like", "you know", "basically", "actually", "honestly"],
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize scoring engine.
        
        Args:
            weights: Custom scoring weights (must sum to 1.0)
        """
        self.weights = weights or {
            "star_structure": 0.25,
            "technical_accuracy": 0.30,
            "communication": 0.20,
            "problem_solving": 0.25,
        }
        self.scores: List[ScoreResult] = []
        self.session_start = datetime.now()
    
    def score_answer(self, question: str, answer: str, question_type: str = "behavioral") -> ScoreResult:
        """
        Score an interview answer comprehensively.
        
        Args:
            question: The interview question
            answer: Candidate's answer
            question_type: 'behavioral' or 'technical'
            
        Returns:
            ScoreResult with detailed scoring
        """
        answer_lower = answer.lower()
        
        # Calculate component scores
        star_score = self._score_star(answer_lower) if question_type == "behavioral" else 0.5
        technical_score = self._score_technical(answer_lower)
        communication_score = self._score_communication(answer_lower)
        problem_solving_score = self._score_problem_solving(answer_lower, question.lower())
        
        # Weighted overall score
        overall = (
            star_score * self.weights["star_structure"] +
            technical_score * self.weights["technical_accuracy"] +
            communication_score * self.weights["communication"] +
            problem_solving_score * self.weights["problem_solving"]
        )
        
        # Generate feedback and identify weaknesses
        feedback, weaknesses = self._generate_feedback(
            star_score, technical_score, communication_score, problem_solving_score, question_type
        )
        
        result = ScoreResult(
            question=question,
            answer=answer,
            star_score=star_score,
            technical_score=technical_score,
            communication_score=communication_score,
            problem_solving_score=problem_solving_score,
            overall_score=overall,
            feedback=feedback,
            weaknesses=weaknesses,
        )
        
        self.scores.append(result)
        logger.info(f"Scored answer: {overall:.2f}/1.0")
        return result
    
    def _score_star(self, answer: str) -> float:
        """Score STAR framework usage (0-1)."""
        components_found = 0
        for component, keywords in self.STAR_KEYWORDS.items():
            if any(kw in answer for kw in keywords):
                components_found += 1
        return components_found / 4.0
    
    def _score_technical(self, answer: str) -> float:
        """Score technical depth (0-1)."""
        positive_count = sum(1 for ind in self.TECHNICAL_INDICATORS["positive"] if ind in answer)
        negative_count = sum(1 for ind in self.TECHNICAL_INDICATORS["negative"] if ind in answer)
        
        # Base score from length and specificity
        length_score = min(len(answer.split()) / 150, 1.0)
        
        # Adjust for positive/negative indicators
        indicator_score = (positive_count * 0.1) - (negative_count * 0.15)
        
        return max(0, min(1, length_score + indicator_score))
    
    def _score_communication(self, answer: str) -> float:
        """Score communication clarity (0-1)."""
        words = answer.split()
        
        # Check structure indicators
        positive_count = sum(1 for ind in self.COMMUNICATION_INDICATORS["positive"] if ind in answer)
        negative_count = sum(1 for ind in self.COMMUNICATION_INDICATORS["negative"] if ind in answer)
        
        # Sentence structure (avg words per sentence)
        sentences = answer.count('.') + answer.count('!') + answer.count('?')
        avg_sentence_length = len(words) / max(sentences, 1)
        
        # Optimal sentence length is 15-25 words
        length_score = 1.0 if 15 <= avg_sentence_length <= 25 else 0.7
        
        # Combine scores
        structure_score = (positive_count * 0.1) - (negative_count * 0.1)
        
        return max(0, min(1, 0.5 + length_score * 0.3 + structure_score))
    
    def _score_problem_solving(self, answer: str, question: str) -> float:
        """Score problem-solving approach (0-1)."""
        # Look for structured thinking
        approach_keywords = ["first", "then", "next", "finally", "approach", "solution", "consider", "analyze"]
        approach_count = sum(1 for kw in approach_keywords if kw in answer)
        
        # Look for consideration of alternatives
        alternative_keywords = ["alternatively", "another approach", "trade-off", "compared to", "instead"]
        alternative_count = sum(1 for kw in alternative_keywords if kw in answer)
        
        # Relevance to question (simple keyword overlap)
        question_words = set(question.split()) - {"what", "how", "why", "when", "the", "a", "is", "are"}
        answer_words = set(answer.split())
        relevance = len(question_words & answer_words) / max(len(question_words), 1)
        
        return min(1, (approach_count * 0.15) + (alternative_count * 0.2) + (relevance * 0.5) + 0.2)
    
    def _generate_feedback(self, star: float, tech: float, comm: float, prob: float, 
                          q_type: str) -> Tuple[str, List[str]]:
        """Generate feedback and identify weaknesses."""
        feedback_parts = []
        weaknesses = []
        
        # STAR feedback (for behavioral)
        if q_type == "behavioral":
            if star < 0.5:
                feedback_parts.append("Structure your answer using STAR: Situation, Task, Action, Result.")
                weaknesses.append("STAR framework")
            elif star < 0.75:
                feedback_parts.append("Good structure, but ensure all STAR components are clear.")
        
        # Technical feedback
        if tech < 0.5:
            feedback_parts.append("Add more technical depth - mention specific technologies or approaches.")
            weaknesses.append("Technical depth")
        elif tech < 0.75:
            feedback_parts.append("Good technical content. Consider discussing trade-offs.")
        
        # Communication feedback
        if comm < 0.5:
            feedback_parts.append("Be more concise and structured. Use clear transitions.")
            weaknesses.append("Communication clarity")
        
        # Problem-solving feedback
        if prob < 0.5:
            feedback_parts.append("Show your thinking process - explain your approach step by step.")
            weaknesses.append("Problem-solving approach")
        
        if not feedback_parts:
            feedback_parts.append("Strong answer! Consider adding a specific metric or outcome.")
        
        return " ".join(feedback_parts), weaknesses
    
    def get_session_summary(self) -> Dict:
        """Get summary of all scores in this session."""
        if not self.scores:
            return {"message": "No answers scored yet"}
        
        avg_overall = sum(s.overall_score for s in self.scores) / len(self.scores)
        avg_star = sum(s.star_score for s in self.scores) / len(self.scores)
        avg_tech = sum(s.technical_score for s in self.scores) / len(self.scores)
        avg_comm = sum(s.communication_score for s in self.scores) / len(self.scores)
        avg_prob = sum(s.problem_solving_score for s in self.scores) / len(self.scores)
        
        # Aggregate weaknesses
        all_weaknesses = []
        for s in self.scores:
            all_weaknesses.extend(s.weaknesses)
        weakness_counts = {}
        for w in all_weaknesses:
            weakness_counts[w] = weakness_counts.get(w, 0) + 1
        
        # Sort by frequency
        top_weaknesses = sorted(weakness_counts.items(), key=lambda x: -x[1])[:3]
        
        return {
            "questions_answered": len(self.scores),
            "overall_score": round(avg_overall * 100),
            "star_score": round(avg_star * 100),
            "technical_score": round(avg_tech * 100),
            "communication_score": round(avg_comm * 100),
            "problem_solving_score": round(avg_prob * 100),
            "top_weaknesses": [w[0] for w in top_weaknesses],
            "duration_minutes": (datetime.now() - self.session_start).seconds // 60,
            "grade": self._calculate_grade(avg_overall),
        }
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "A-"
        elif score >= 0.75:
            return "B+"
        elif score >= 0.7:
            return "B"
        elif score >= 0.65:
            return "B-"
        elif score >= 0.6:
            return "C+"
        elif score >= 0.55:
            return "C"
        else:
            return "Needs Improvement"

"""
Advanced Scoring Rubrics
Comprehensive evaluation framework for all interview answer types
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import re


class QuestionType(Enum):
    """Types of interview questions"""
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    TECHNICAL_CONCEPT = "technical_concept"
    DEBUGGING = "debugging"


@dataclass
class ScoringResult:
    """Complete scoring result"""
    overall_score: float  # 0-100
    category_scores: Dict[str, float]
    strengths: List[str]
    improvements: List[str]
    feedback: str
    rubric_used: str


class CodingRubric:
    """Scoring rubric for coding questions"""
    
    @staticmethod
    def evaluate(
        code: str,
        validation_result: Dict,
        explanation: str,
        expected_complexity: str = "O(n log n)",
        proficiency_level: str = "Mid-level"
    ) -> ScoringResult:
        """
        Evaluate coding answer
        
        Categories:
        - Correctness (40%)
        - Code Quality (20%)
        - Explanation (15%)
        - Complexity Analysis (15%)
        - Edge Cases (10%)
        """
        scores = {}
        strengths = []
        improvements = []
        
        # 1. Correctness (40 points)
        if validation_result.get("passed"):
            correctness = 40
            strengths.append("All test cases passed")
        else:
            passed_tests = sum(1 for t in validation_result.get("test_results", []) if t.get("passed"))
            total_tests = len(validation_result.get("test_results", []))
            correctness = (passed_tests / max(total_tests, 1)) * 40
            improvements.append(f"Only {passed_tests}/{total_tests} tests passed - review counterexamples")
        
        scores["correctness"] = correctness
        
        # 2. Code Quality (20 points)
        quality = 20
        code_lower = code.lower()
        
        # Check for good practices
        if "def " in code or "function " in code:
            strengths.append("Proper function definition")
        else:
            quality -= 5
            improvements.append("Use functions for modularity")
        
        # Check for comments
        if "#" in code or "//" in code:
            strengths.append("Code includes comments")
        else:
            quality -= 3
            improvements.append("Add comments for clarity")
        
        # Check for descriptive naming
        if any(len(var) > 2 for var in re.findall(r'\b(\w+)\b', code)):
            strengths.append("Descriptive variable names")
        else:
            quality -= 4
            improvements.append("Use more descriptive variable names")
        
        # Check for magic numbers
        if re.search(r'\b\d{2,}\b', code):
            quality -= 2
            improvements.append("Avoid magic numbers, use constants")
        
        scores["code_quality"] = max(quality, 0)
        
        # 3. Explanation (15 points)
        explanation_score = 15
        if explanation:
            explanation_lower = explanation.lower()
            
            # Check for approach explanation
            if any(word in explanation_lower for word in ['approach', 'algorithm', 'method', 'strategy']):
                strengths.append("Clear approach explanation")
            else:
                explanation_score -= 5
                improvements.append("Explain your approach before coding")
            
            # Check for step-by-step
            if any(word in explanation_lower for word in ['step', 'first', 'then', 'finally']):
                strengths.append("Step-by-step reasoning")
            else:
                explanation_score -= 3
                improvements.append("Break down solution into steps")
            
            # Check length (should be substantive)
            if len(explanation.split()) < 20:
                explanation_score -= 4
                improvements.append("Provide more detailed explanation")
        else:
            explanation_score = 3
            improvements.append("Missing explanation - always explain your thinking")
        
        scores["explanation"] = max(explanation_score, 0)
        
        # 4. Complexity Analysis (15 points)
        complexity_score = 15
        complexity_mentioned = False
        
        if explanation:
            if "o(n" in explanation.lower() or "time complexity" in explanation.lower():
                complexity_mentioned = True
                strengths.append("Discussed time complexity")
            
            if "space" in explanation.lower():
                strengths.append("Discussed space complexity")
            else:
                complexity_score -= 5
                improvements.append("Analyze space complexity")
        
        if not complexity_mentioned:
            complexity_score -= 10
            improvements.append("Always analyze time and space complexity")
        
        # Check if meets expected complexity
        if validation_result.get("complexity_warnings"):
            complexity_score -= 3
            for warning in validation_result["complexity_warnings"]:
                improvements.append(warning)
        
        scores["complexity_analysis"] = max(complexity_score, 0)
        
        # 5. Edge Cases (10 points)
        edge_case_score = 10
        
        # Check code for edge case handling
        if "if" in code_lower and ("not" in code_lower or "empty" in code_lower or "none" in code_lower):
            strengths.append("Handles edge cases")
        else:
            edge_case_score -= 5
            improvements.append("Consider edge cases (empty input, null, etc.)")
        
        # Check explanation mentions edge cases
        if explanation and "edge" in explanation.lower():
            strengths.append("Discussed edge cases")
        else:
            edge_case_score -= 3
            improvements.append("Discuss edge cases in explanation")
        
        scores["edge_cases"] = max(edge_case_score, 0)
        
        # Calculate overall score
        overall = sum(scores.values())
        
        # Adjust for proficiency level
        if proficiency_level in ["Junior", "Learning"]:
            # Be more lenient
            overall = min(overall * 1.1, 100)
        elif proficiency_level == "Expert":
            # Be stricter
            overall = overall * 0.95
        
        # Generate feedback
        feedback = CodingRubric._generate_feedback(overall, strengths, improvements, proficiency_level)
        
        return ScoringResult(
            overall_score=round(overall, 1),
            category_scores=scores,
            strengths=strengths,
            improvements=improvements,
            feedback=feedback,
            rubric_used="coding"
        )
    
    @staticmethod
    def _generate_feedback(score: float, strengths: List[str], improvements: List[str], level: str) -> str:
        """Generate human-readable feedback"""
        if score >= 90:
            tone = "Excellent work!"
        elif score >= 75:
            tone = "Strong solution overall."
        elif score >= 60:
            tone = "Good attempt, but room for improvement."
        else:
            tone = "Needs significant improvement."
        
        feedback_parts = [tone]
        
        if strengths:
            feedback_parts.append(f"\n\n✅ Strengths:\n" + "\n".join(f"  • {s}" for s in strengths[:3]))
        
        if improvements:
            feedback_parts.append(f"\n\n📈 Areas to improve:\n" + "\n".join(f"  • {i}" for i in improvements[:4]))
        
        feedback_parts.append(f"\n\n🎯 Expected level: {level}")
        
        return "".join(feedback_parts)


class BehavioralRubric:
    """Scoring rubric for behavioral questions"""
    
    @staticmethod
    def evaluate(answer: str, proficiency_level: str = "Mid-level") -> ScoringResult:
        """
        Evaluate behavioral answer using STAR framework
        
        Categories:
        - STAR Structure (30%)
        - Specificity (25%)
        - Impact/Results (25%)
        - Self-Awareness (20%)
        """
        scores = {}
        strengths = []
        improvements = []
        
        answer_lower = answer.lower()
        
        # 1. STAR Structure (30 points)
        star_score = 0
        star_components = {
            "situation": ["situation", "context", "background", "at", "when"],
            "task": ["task", "challenge", "problem", "needed to", "goal"],
            "action": ["i did", "i took", "i implemented", "my role", "i decided"],
            "result": ["result", "outcome", "impact", "achieved", "improved", "increased"]
        }
        
        for component, keywords in star_components.items():
            if any(kw in answer_lower for kw in keywords):
                star_score += 7.5
                strengths.append(f"Included {component.title()} in answer")
            else:
                improvements.append(f"Missing {component.title()} - add context about {component}")
        
        scores["star_structure"] = star_score
        
        # 2. Specificity (25 points)
        specificity_score = 25
        
        # Check for vague language
        vague_words = ["things", "stuff", "basically", "kind of", "sort of"]
        vague_count = sum(1 for word in vague_words if word in answer_lower)
        if vague_count > 2:
            specificity_score -= vague_count * 3
            improvements.append("Avoid vague language - be more specific")
        
        # Check for concrete examples
        if any(indicator in answer_lower for indicator in ["for example", "specifically", "in particular"]):
            strengths.append("Used specific examples")
        else:
            specificity_score -= 8
            improvements.append("Include specific examples and details")
        
        # Check for numbers/metrics
        if re.search(r'\d+%|\d+ (users|customers|hours|days)', answer):
            strengths.append("Quantified results with metrics")
        else:
            specificity_score -= 5
            improvements.append("Quantify impact with specific numbers")
        
        scores["specificity"] = max(specificity_score, 0)
        
        # 3. Impact/Results (25 points)
        impact_score = 25
        
        # Check for measurable outcomes
        if any(word in answer_lower for word in ["increased", "decreased", "improved", "reduced", "achieved"]):
            strengths.append("Described measurable impact")
        else:
            impact_score -= 10
            improvements.append("Clearly state the results and impact")
        
        # Check for team/company benefit
        if any(word in answer_lower for word in ["team", "company", "users", "customers", "business"]):
            strengths.append("Highlighted broader impact")
        else:
            impact_score -= 8
            improvements.append("Explain how it helped team/company")
        
        scores["impact"] = max(impact_score, 0)
        
        # 4. Self-Awareness (20 points)
        awareness_score = 20
        
        # Check for learning/reflection
        if any(word in answer_lower for word in ["learned", "realized", "discovered", "now i", "next time"]):
            strengths.append("Showed self-reflection and learning")
        else:
            awareness_score -= 10
            improvements.append("Reflect on what you learned from the experience")
        
        # Check for acknowledging challenges
        if any(word in answer_lower for word in ["challenge", "difficult", "obstacle", "struggled"]):
            strengths.append("Acknowledged challenges honestly")
        else:
            awareness_score -= 5
            improvements.append("Be honest about challenges faced")
        
        scores["self_awareness"] = max(awareness_score, 0)
        
        # Calculate overall
        overall = sum(scores.values())
        
        # Adjust for proficiency
        if proficiency_level in ["Junior", "Learning"]:
            overall = min(overall * 1.15, 100)
        
        feedback = BehavioralRubric._generate_feedback(overall, strengths, improvements)
        
        return ScoringResult(
            overall_score=round(overall, 1),
            category_scores=scores,
            strengths=strengths,
            improvements=improvements,
            feedback=feedback,
            rubric_used="behavioral"
        )
    
    @staticmethod
    def _generate_feedback(score: float, strengths: List[str], improvements: List[str]) -> str:
        """Generate feedback for behavioral answers"""
        if score >= 85:
            tone = "Excellent STAR response!"
        elif score >= 70:
            tone = "Good behavioral answer."
        elif score >= 55:
            tone = "Decent response, but could be stronger."
        else:
            tone = "Needs more structure and detail."
        
        feedback = [tone]
        
        if strengths:
            feedback.append("\n\n✅ What worked:\n" + "\n".join(f"  • {s}" for s in strengths[:3]))
        
        if improvements:
            feedback.append("\n\n📈 How to improve:\n" + "\n".join(f"  • {i}" for i in improvements[:4]))
        
        feedback.append("\n\n💡 Tip: Use STAR framework - Situation, Task, Action, Result")
        
        return "".join(feedback)


class SystemDesignRubric:
    """Scoring rubric for system design questions"""
    
    @staticmethod
    def evaluate(
        design_text: str,
        diagram_generated: bool,
        proficiency_level: str = "Mid-level"
    ) -> ScoringResult:
        """
        Evaluate system design answer
        
        Categories:
        - Requirements Clarity (20%)
        - Architecture Components (25%)
        - Scalability Discussion (20%)
        - Tradeoffs (20%)
        - Diagram/Visual (15%)
        """
        scores = {}
        strengths = []
        improvements = []
        
        design_lower = design_text.lower()
        
        # 1. Requirements (20 points)
        req_score = 20
        
        if "requirements" in design_lower or "assumptions" in design_lower:
            strengths.append("Clarified requirements upfront")
        else:
            req_score -= 10
            improvements.append("Start by clarifying requirements and assumptions")
        
        # Check for functional vs non-functional
        if "functional" in design_lower or "non-functional" in design_lower:
            strengths.append("Distinguished functional vs non-functional requirements")
        else:
            req_score -= 5
            improvements.append("Separate functional and non-functional requirements")
        
        scores["requirements"] = max(req_score, 0)
        
        # 2. Architecture Components (25 points)
        arch_score = 0
        components = {
            "API/Gateway": ["api", "gateway", "endpoint", "rest"],
            "Database": ["database", "postgres", "mysql", "mongo", "storage"],
            "Cache": ["cache", "redis", "memcached"],
            "Load Balancer": ["load balancer", "lb", "nginx"],
            "Queue": ["queue", "kafka", "rabbitmq", "sqs", "pubsub"]
        }
        
        for comp_name, keywords in components.items():
            if any(kw in design_lower for kw in keywords):
                arch_score += 5
                strengths.append(f"Included {comp_name}")
        
        scores["architecture"] = min(arch_score, 25)
        
        # 3. Scalability (20 points)
        scale_score = 20
        
        scalability_keywords = ["scale", "scalability", "horizontal", "vertical", "replicas", "sharding", "partitioning"]
        if any(kw in design_lower for kw in scalability_keywords):
            strengths.append("Discussed scalability")
        else:
            scale_score -= 12
            improvements.append("Explain how the system scales (horizontal/vertical)")
        
        # Check for numbers
        if re.search(r'\d+\s*(qps|rps|users|requests)', design_lower):
            strengths.append("Provided scale estimates")
        else:
            scale_score -= 5
            improvements.append("Estimate scale (QPS, storage, users)")
        
        scores["scalability"] = max(scale_score, 0)
        
        # 4. Tradeoffs (20 points)
        tradeoff_score = 20
        
        if "tradeoff" in design_lower or "trade-off" in design_lower:
            strengths.append("Discussed tradeoffs")
        else:
            tradeoff_score -= 10
            improvements.append("Always discuss tradeoffs between options")
        
        # CAP theorem
        if any(word in design_lower for word in ["consistency", "availability", "partition"]):
            strengths.append("Considered CAP theorem")
        else:
            tradeoff_score -= 5
            improvements.append("Consider CAP theorem (Consistency, Availability, Partition tolerance)")
        
        scores["tradeoffs"] = max(tradeoff_score, 0)
        
        # 5. Diagram (15 points)
        diagram_score = 15 if diagram_generated else 5
        if diagram_generated:
            strengths.append("Provided visual diagram")
        else:
            improvements.append("Draw a diagram to visualize the system")
        
        scores["diagram"] = diagram_score
        
        # Calculate overall
        overall = sum(scores.values())
        
        # Adjust for proficiency
        if proficiency_level in ["Junior", "Learning"]:
            overall = min(overall * 1.2, 100)
        elif proficiency_level == "Expert":
            overall = overall * 0.9
        
        feedback = SystemDesignRubric._generate_feedback(overall, strengths, improvements, proficiency_level)
        
        return ScoringResult(
            overall_score=round(overall, 1),
            category_scores=scores,
            strengths=strengths,
            improvements=improvements,
            feedback=feedback,
            rubric_used="system_design"
        )
    
    @staticmethod
    def _generate_feedback(score: float, strengths: List[str], improvements: List[str], level: str) -> str:
        """Generate feedback"""
        if score >= 85:
            tone = "Excellent system design!"
        elif score >= 70:
            tone = "Solid design overall."
        elif score >= 55:
            tone = "Good start, but needs more depth."
        else:
            tone = "Requires significant improvement."
        
        feedback = [tone]
        
        if strengths:
            feedback.append("\n\n✅ Strengths:\n" + "\n".join(f"  • {s}" for s in strengths[:4]))
        
        if improvements:
            feedback.append("\n\n📈 Areas to improve:\n" + "\n".join(f"  • {i}" for i in improvements[:4]))
        
        feedback.append(f"\n\n🎯 Expected level: {level}")
        feedback.append("\n💡 Remember: Requirements → Architecture → Scalability → Tradeoffs")
        
        return "".join(feedback)


def score_answer(
    question_type: QuestionType,
    answer: str,
    proficiency_level: str = "Mid-level",
    **kwargs
) -> ScoringResult:
    """
    Universal scoring function
    
    Usage:
        # Coding
        score_answer(
            QuestionType.CODING,
            answer=code,
            proficiency_level="Senior",
            validation_result=validation_result,
            explanation=explanation
        )
        
        # Behavioral
        score_answer(
            QuestionType.BEHAVIORAL,
            answer=behavioral_answer,
            proficiency_level="Mid-level"
        )
        
        # System Design
        score_answer(
            QuestionType.SYSTEM_DESIGN,
            answer=design_text,
            proficiency_level="Senior",
            diagram_generated=True
        )
    """
    if question_type == QuestionType.CODING:
        return CodingRubric.evaluate(
            code=answer,
            validation_result=kwargs.get("validation_result", {}),
            explanation=kwargs.get("explanation", ""),
            proficiency_level=proficiency_level
        )
    
    elif question_type == QuestionType.BEHAVIORAL:
        return BehavioralRubric.evaluate(
            answer=answer,
            proficiency_level=proficiency_level
        )
    
    elif question_type == QuestionType.SYSTEM_DESIGN:
        return SystemDesignRubric.evaluate(
            design_text=answer,
            diagram_generated=kwargs.get("diagram_generated", False),
            proficiency_level=proficiency_level
        )
    
    else:
        # Generic scoring for other types
        return ScoringResult(
            overall_score=70.0,
            category_scores={"generic": 70.0},
            strengths=["Answer provided"],
            improvements=["Add more detail"],
            feedback="Generic scoring applied",
            rubric_used="generic"
        )

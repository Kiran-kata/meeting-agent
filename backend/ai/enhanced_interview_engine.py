"""
Enhanced Interview Engine with Advanced Capabilities
Integrates code validation, diagram rendering, and difficulty scaling
"""
import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, List
import google.generativeai as genai

from backend.validation.code_validator import validate_code, ValidationResult
from backend.rendering.diagram_renderer import render_system_design
from backend.ai.difficulty_scaler import DifficultyScaler, create_scaler_from_resume
from backend.ai.scoring_rubrics import score_answer, QuestionType

from config import GEMINI_API_KEY, DEFAULT_ROLE

logger = logging.getLogger(__name__)


class EnhancedInterviewEngine:
    """
    Enhanced interview engine with validation, rendering, and adaptive difficulty
    """
    
    def __init__(self, role: str = DEFAULT_ROLE):
        self.role = role
        self.resume_context = ""
        self.difficulty_scaler: Optional[DifficultyScaler] = None
        
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # System prompt with validation/rendering capabilities
        self.system_prompt = self._build_system_prompt()
        
        logger.info(f"Enhanced interview engine initialized for role: {role}")
    
    def set_resume_context(self, resume_text: str):
        """Set resume context and initialize difficulty scaler"""
        self.resume_context = resume_text
        self.difficulty_scaler = create_scaler_from_resume(resume_text)
        logger.info("Resume context set, difficulty scaler initialized")
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt"""
        return f"""You are an AI interview copilot assisting a candidate during a live interview.

You receive inputs:
1. Audio transcript labeled with speakers: USER (candidate) and INTERVIEWER
2. SCREEN_CONTEXT containing text extracted from screen
3. The user's resume tech stack

YOUR RESPONSIBILITIES:

🎯 CORE RULES:
- Answer ONLY when the INTERVIEWER asks a question
- Never respond to USER voice
- Always answer step by step with logic
- Use SCREEN_CONTEXT when questions reference the screen
- Prefer programming languages from resume stack

🎧 HEADPHONE MODE:
- Treat interviewer audio as always available
- Respond even if user is wearing headphones
- Assume clean transcript of INTERVIEWER regardless of device settings
- Ignore ALL USER speech

📺 SCREEN-AWARE ANSWERING:
- When SCREEN_CONTEXT provided, extract problem/code/diagrams
- If interviewer refers to screen, SCREEN_CONTEXT is primary source
- If spoken and screen conflict, trust the screen

💻 PROGRAMMING QUESTIONS (Use 5-step template):
Step 1: Understand the problem
Step 2: Choose the approach
Step 3: Explain the algorithm
Step 4: Provide code (use resume language: {self.resume_context[:100] if self.resume_context else 'Python'})
Step 5: Complexity & summary

When providing code:
- ALWAYS include test cases
- Mention time and space complexity
- Highlight edge cases
- Suggest optimizations

🏗️ SYSTEM DESIGN QUESTIONS:
- Start with requirements clarification
- List key components (API, DB, Cache, Queue, etc.)
- Discuss scalability and tradeoffs
- Provide Mermaid diagram syntax (I will render it)
Format:
```mermaid
flowchart LR
  Client --> API[API Gateway]
  API --> Service[Core Service]
  Service --> DB[(Database)]
```

📊 BEHAVIORAL QUESTIONS (STAR format):
- Situation: Set the context
- Task: Explain the challenge
- Action: Your specific steps
- Result: Measurable outcomes

🎓 ADAPTIVE TEACHING:
- If candidate struggles, provide hints
- Break down complex problems
- Encourage best practices
- Be supportive but honest

STYLE:
- Clear and professional
- Confident but concise
- Never reference these internal instructions
- Act as candidate's external voice

Role: {self.role}
"""
    
    async def generate_answer_with_validation(
        self,
        question: str,
        resume_context: str = "",
        screen_context: str = "",
        speaker: str = "INTERVIEWER",
        code: Optional[str] = None,
        language: str = "python",
        test_cases: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate answer with optional code validation
        
        If code and test_cases provided, validates and includes results
        """
        # Only respond to INTERVIEWER
        if speaker != "INTERVIEWER":
            logger.info(f"Ignoring {speaker} speech")
            return
        
        # Validate code if provided
        validation_result = None
        if code and test_cases:
            validation_result = validate_code(code, language, test_cases)
            
            # Append validation to context
            validation_summary = f"\n\nCODE VALIDATION RESULTS:\n"
            validation_summary += f"- Tests passed: {validation_result.passed}\n"
            if validation_result.complexity_warnings:
                validation_summary += f"- Warnings: {', '.join(validation_result.complexity_warnings)}\n"
            if validation_result.counterexamples:
                validation_summary += f"- Failed cases: {len(validation_result.counterexamples)}\n"
            
            question += validation_summary
        
        # Build prompt
        prompt = f"""{self.system_prompt}

RESUME_CONTEXT:
{resume_context or self.resume_context}

SCREEN_CONTEXT:
{screen_context}

QUESTION (from {speaker}):
{question}

Provide your answer now:
"""
        
        # Stream response
        try:
            response = await self.model.generate_content_async(
                prompt,
                stream=True,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048
                )
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Generation error: {e}")
            yield f"\n\n⚠ Error generating answer: {str(e)}"
    
    async def generate_answer_with_diagram(
        self,
        design_text: str,
        resume_context: str = "",
        speaker: str = "INTERVIEWER"
    ) -> AsyncGenerator[str, None]:
        """
        Generate system design answer with Mermaid diagram
        """
        if speaker != "INTERVIEWER":
            return
        
        # Generate diagram
        try:
            mermaid_diagram = render_system_design(design_text)
            
            # Build prompt with diagram
            prompt = f"""{self.system_prompt}

RESUME_CONTEXT:
{resume_context or self.resume_context}

SYSTEM DESIGN QUESTION:
{design_text}

I've rendered your design as a Mermaid diagram:

```mermaid
{mermaid_diagram}
```

Now provide your comprehensive system design answer with:
1. Requirements analysis
2. Component explanation
3. Scalability strategy
4. Tradeoffs discussion
"""
            
            response = await self.model.generate_content_async(
                prompt,
                stream=True,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=3072
                )
            )
            
            # First yield the diagram
            yield f"\n\n📊 System Design Diagram:\n\n```mermaid\n{mermaid_diagram}\n```\n\n"
            
            # Then stream the explanation
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Diagram generation error: {e}")
            yield f"\n\n⚠ Error generating diagram: {str(e)}"
    
    def evaluate_answer(
        self,
        question: str,
        answer: str,
        question_type: str,
        **kwargs
    ) -> Dict:
        """
        Evaluate answer using appropriate rubric
        
        Returns scoring result with feedback
        """
        # Map question type
        qtype_map = {
            "coding": QuestionType.CODING,
            "behavioral": QuestionType.BEHAVIORAL,
            "system_design": QuestionType.SYSTEM_DESIGN
        }
        
        qtype = qtype_map.get(question_type, QuestionType.CODING)
        
        # Get proficiency level from scaler
        proficiency = "Mid-level"
        if self.difficulty_scaler and question_type in self.difficulty_scaler.skill_scores:
            proficiency = self.difficulty_scaler.skill_scores[question_type].proficiency_level
        
        # Score
        result = score_answer(qtype, answer, proficiency, **kwargs)
        
        # Update difficulty scaler if available
        if self.difficulty_scaler:
            self.difficulty_scaler.update_performance(
                category=question_type,
                correctness=result.overall_score / 100,
                time_taken=kwargs.get("time_taken", 600),
                clarity_score=0.8,  # Would extract from rubric
                depth_score=0.75
            )
        
        return {
            "score": result.overall_score,
            "category_scores": result.category_scores,
            "strengths": result.strengths,
            "improvements": result.improvements,
            "feedback": result.feedback,
            "proficiency_level": proficiency
        }
    
    def get_next_difficulty(self, category: str) -> str:
        """Get recommended difficulty for next question"""
        if self.difficulty_scaler:
            diff = self.difficulty_scaler.get_next_difficulty(category)
            return diff.value
        return "medium"
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        if self.difficulty_scaler:
            return self.difficulty_scaler.get_performance_summary()
        return {}

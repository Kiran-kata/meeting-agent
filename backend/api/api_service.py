"""
FastAPI Backend Service
Exposes all interview assistant capabilities via REST API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import logging
from pathlib import Path

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.validation.code_validator import validate_code, ValidationResult
from backend.rendering.diagram_renderer import render_system_design, generate_mermaid_from_components
from backend.ai.difficulty_scaler import create_scaler_from_resume, DifficultyScaler, ResumeSkills, Difficulty
from backend.ai.scoring_rubrics import score_answer, QuestionType, ScoringResult
from backend.ai.interview_engine import InterviewEngine
from backend.ai.resume_parser import ResumeParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Interview Assistant API",
    description="Comprehensive interview preparation and assistance API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use proper state management)
sessions: Dict[str, Dict] = {}
scalers: Dict[str, DifficultyScaler] = {}


# ============= Request/Response Models =============

class SessionStartRequest(BaseModel):
    user_id: str
    resume_text: Optional[str] = None
    role: str = "SDE"


class TranscribeRequest(BaseModel):
    audio_base64: str
    session_id: str


class OCRRequest(BaseModel):
    image_base64: str
    session_id: str


class QuestionRequest(BaseModel):
    session_id: str
    category: str = "algorithms"  # algorithms, system_design, behavioral
    difficulty: Optional[str] = None  # auto-determined if None


class AnswerEvaluateRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    question_type: str  # coding, behavioral, system_design
    code: Optional[str] = None
    explanation: Optional[str] = None


class CodeValidateRequest(BaseModel):
    code: str
    language: str = "python"
    test_cases: List[Dict]  # [{"input": ..., "expected": ...}]


class SystemDesignRequest(BaseModel):
    design_text: str
    structured: bool = False  # If true, expects services/databases lists
    services: Optional[List[str]] = None
    databases: Optional[List[str]] = None
    caches: Optional[List[str]] = None
    queues: Optional[List[str]] = None
    workers: Optional[List[str]] = None


# ============= Endpoints =============

@app.get("/")
def root():
    """Health check"""
    return {
        "status": "online",
        "service": "Interview Assistant API",
        "version": "1.0.0"
    }


@app.post("/session/start")
def start_session(request: SessionStartRequest):
    """
    Start new interview session
    
    Initializes difficulty scaler based on resume
    """
    try:
        session_id = f"session_{len(sessions) + 1}"
        
        # Parse resume if provided
        resume_skills = None
        if request.resume_text:
            scaler = create_scaler_from_resume(request.resume_text)
            scalers[session_id] = scaler
            resume_skills = {
                "languages": scaler.resume_skills.languages,
                "frameworks": scaler.resume_skills.frameworks,
                "years_experience": scaler.resume_skills.years_experience,
                "primary_language": scaler.resume_skills.primary_language
            }
        
        # Create session
        sessions[session_id] = {
            "user_id": request.user_id,
            "role": request.role,
            "questions_asked": [],
            "performance_history": [],
            "start_time": None,
            "resume_skills": resume_skills
        }
        
        logger.info(f"Started session {session_id} for {request.user_id}")
        
        return {
            "session_id": session_id,
            "status": "started",
            "resume_skills": resume_skills,
            "message": "Session initialized. Ready for questions."
        }
    
    except Exception as e:
        logger.error(f"Session start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe")
def transcribe_audio(request: TranscribeRequest):
    """
    Transcribe audio to text using Whisper
    
    Returns speaker-labeled transcript
    """
    try:
        # In production, use actual Whisper API
        # For now, return mock
        return {
            "transcript": "This is a mock transcription",
            "speaker": "INTERVIEWER",
            "confidence": 0.95,
            "processing_time": 0.5
        }
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr")
def process_ocr(request: OCRRequest):
    """
    Extract text from screen capture via OCR
    
    Returns detected text and question indicators
    """
    try:
        # In production, use actual Tesseract
        # For now, return mock
        return {
            "text": "Mock OCR text",
            "coding_question_detected": False,
            "confidence": 0.85,
            "processing_time": 0.3
        }
    
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question/next")
def get_next_question(request: QuestionRequest):
    """
    Get next question based on difficulty scaling
    
    Automatically adjusts difficulty based on performance
    """
    try:
        session = sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get scaler
        scaler = scalers.get(request.session_id)
        
        # Determine difficulty
        if request.difficulty:
            difficulty = Difficulty(request.difficulty)
        elif scaler:
            difficulty = scaler.get_next_difficulty(request.category)
        else:
            difficulty = Difficulty.MEDIUM
        
        # Generate question (mock for now)
        question = {
            "id": f"q_{len(session['questions_asked']) + 1}",
            "category": request.category,
            "difficulty": difficulty.value,
            "text": f"Sample {difficulty.value} {request.category} question",
            "expected_time": 600,  # 10 minutes
            "hints": ["Hint 1", "Hint 2"],
            "follow_up_intensity": scaler.get_follow_up_intensity(request.category) if scaler else "moderate"
        }
        
        # Track question
        session["questions_asked"].append(question)
        
        logger.info(f"Generated {difficulty.value} question for session {request.session_id}")
        
        return question
    
    except Exception as e:
        logger.error(f"Question generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/answer/evaluate")
def evaluate_answer(request: AnswerEvaluateRequest):
    """
    Evaluate answer using appropriate rubric
    
    Returns detailed scoring and feedback
    """
    try:
        session = sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get proficiency level
        scaler = scalers.get(request.session_id)
        if scaler:
            category = request.question_type
            proficiency = scaler.skill_scores.get(category, None)
            proficiency_level = proficiency.proficiency_level if proficiency else "Mid-level"
        else:
            proficiency_level = "Mid-level"
        
        # Score based on question type
        question_type_map = {
            "coding": QuestionType.CODING,
            "behavioral": QuestionType.BEHAVIORAL,
            "system_design": QuestionType.SYSTEM_DESIGN
        }
        
        qtype = question_type_map.get(request.question_type, QuestionType.CODING)
        
        # Additional kwargs for coding
        kwargs = {}
        if qtype == QuestionType.CODING and request.code:
            # Would run validation here
            kwargs["validation_result"] = {"passed": True, "test_results": []}
            kwargs["explanation"] = request.explanation or ""
        
        # Score answer
        result = score_answer(
            qtype,
            request.answer,
            proficiency_level=proficiency_level,
            **kwargs
        )
        
        # Update performance in scaler
        if scaler:
            scaler.update_performance(
                category=request.question_type,
                correctness=result.overall_score / 100,
                time_taken=300,  # Would track actual time
                clarity_score=0.8,
                depth_score=0.75
            )
        
        # Track performance
        session["performance_history"].append({
            "question": request.question,
            "score": result.overall_score,
            "category": request.question_type
        })
        
        logger.info(f"Evaluated {request.question_type} answer: {result.overall_score}/100")
        
        return {
            "score": result.overall_score,
            "category_scores": result.category_scores,
            "strengths": result.strengths,
            "improvements": result.improvements,
            "feedback": result.feedback,
            "proficiency_level": proficiency_level
        }
    
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/code/validate")
def validate_code_endpoint(request: CodeValidateRequest):
    """
    Validate code with static checks + runtime tests
    
    Returns test results and complexity warnings
    """
    try:
        result = validate_code(
            code=request.code,
            language=request.language,
            test_cases=request.test_cases
        )
        
        logger.info(f"Validated {request.language} code: {result.passed}")
        
        return {
            "passed": result.passed,
            "test_results": result.test_results,
            "syntax_valid": result.syntax_valid,
            "complexity_warnings": result.complexity_warnings,
            "execution_time": result.execution_time,
            "memory_estimate": result.memory_estimate,
            "error_message": result.error_message,
            "counterexamples": result.counterexamples
        }
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/systemdesign/render")
def render_diagram(request: SystemDesignRequest):
    """
    Render system design as Mermaid diagram
    
    Supports both natural language and structured input
    """
    try:
        if request.structured and request.services:
            # Use explicit components
            mermaid = generate_mermaid_from_components(
                services=request.services,
                databases=request.databases or [],
                caches=request.caches,
                queues=request.queues,
                workers=request.workers
            )
        else:
            # Parse from text
            mermaid = render_system_design(request.design_text)
        
        logger.info("Generated Mermaid diagram")
        
        return {
            "mermaid": mermaid,
            "format": "mermaid",
            "preview_url": None  # Could generate image preview
        }
    
    except Exception as e:
        logger.error(f"Diagram rendering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/report/{session_id}")
def get_session_report(session_id: str):
    """
    Get comprehensive session report
    
    Returns performance summary and improvement areas
    """
    try:
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        scaler = scalers.get(session_id)
        
        # Calculate summary
        performance = session["performance_history"]
        avg_score = sum(p["score"] for p in performance) / len(performance) if performance else 0
        
        # Get proficiency summary from scaler
        proficiency_summary = scaler.get_performance_summary() if scaler else {}
        
        report = {
            "session_id": session_id,
            "role": session["role"],
            "questions_attempted": len(session["questions_asked"]),
            "average_score": round(avg_score, 1),
            "performance_by_category": {},
            "proficiency_summary": proficiency_summary,
            "strengths": proficiency_summary.get("strengths", []),
            "areas_to_improve": proficiency_summary.get("areas_to_improve", []),
            "resume_skills": session["resume_skills"]
        }
        
        # Group by category
        for perf in performance:
            cat = perf["category"]
            if cat not in report["performance_by_category"]:
                report["performance_by_category"][cat] = []
            report["performance_by_category"][cat].append(perf["score"])
        
        # Average per category
        for cat in report["performance_by_category"]:
            scores = report["performance_by_category"][cat]
            report["performance_by_category"][cat] = {
                "average": round(sum(scores) / len(scores), 1),
                "attempts": len(scores),
                "trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
            }
        
        logger.info(f"Generated report for session {session_id}")
        
        return report
    
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "scalers_active": len(scalers),
        "version": "1.0.0"
    }


# ============= Run Server =============

if __name__ == "__main__":
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# 🚀 Quick Start Guide - Advanced Interview Assistant

## Installation

### 1. Install Dependencies
```bash
cd meeting-agent
pip install -r requirements.txt
```

### 2. Configure API Keys
Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## Usage Options

### Option 1: Desktop App (Existing)
Run the transparent overlay UI:
```bash
python run.py
```

**Features:**
- Transparent glassmorphism UI
- Live audio transcription
- Screen OCR capture
- Real-time AI answers
- Keyboard shortcuts (Ctrl+Shift+H, P, C, etc.)

---

### Option 2: FastAPI Backend
Run the REST API service:
```bash
cd backend/api
python api_service.py
```

**API Docs:** http://localhost:8000/docs

**Test endpoint:**
```bash
curl http://localhost:8000/health
```

---

### Option 3: Enhanced Engine (Python API)

```python
from backend.ai.enhanced_interview_engine import EnhancedInterviewEngine
from backend.validation.code_validator import validate_code
from backend.rendering.diagram_renderer import render_system_design

# Initialize engine
engine = EnhancedInterviewEngine(role="SDE")
engine.set_resume_context("Python developer, 5 years experience...")

# Validate code
result = validate_code(
    code='''
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    ''',
    language="python",
    test_cases=[
        {"input": [[2,7,11,15], 9], "expected": [0,1]},
        {"input": [[3,2,4], 6], "expected": [1,2]}
    ]
)

print(f"Tests passed: {result.passed}")
print(f"Execution time: {result.execution_time}s")

# Render system design
mermaid = render_system_design("""
Client connects to API Gateway
API Gateway talks to Auth Service and Core Service
Core Service uses Postgres database
Core Service reads from Redis cache
Core Service writes to Kafka queue
""")

print(f"Mermaid diagram:\n{mermaid}")

# Generate answer with validation
import asyncio

async def main():
    async for chunk in engine.generate_answer_with_validation(
        question="Implement two sum",
        code=code,
        test_cases=test_cases
    ):
        print(chunk, end="")

asyncio.run(main())
```

---

## Quick Test: Code Validation

```python
from backend.validation.code_validator import validate_code

# Test a buggy solution
buggy_code = '''
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(len(nums)):  # Bug: should start at i+1
            if nums[i] + nums[j] == target:
                return [i, j]
'''

result = validate_code(
    buggy_code,
    "python",
    [
        {"input": [[2,7,11,15], 9], "expected": [0,1]},
        {"input": [[3,2,4], 6], "expected": [1,2]},
        {"input": [[3,3], 6], "expected": [0,1]}
    ]
)

print(f"Passed: {result.passed}")
print(f"Warnings: {result.complexity_warnings}")
print(f"Counterexamples: {result.counterexamples}")
```

**Expected Output:**
```
Passed: False
Warnings: ['⚠ Multiple nested loops detected - consider O(n²) or O(n³) complexity']
Counterexamples: [{'input': [[3, 3], 6], 'expected': [0, 1], 'actual': [0, 0]}]
```

---

## Quick Test: System Design Renderer

```python
from backend.rendering.diagram_renderer import render_system_design

design = '''
Design a URL shortener:

Client sends long URL to API Gateway
API Gateway validates and generates short code
API Gateway stores mapping in Postgres database
API Gateway caches frequently accessed URLs in Redis
When user visits short URL, API checks Redis cache first
If not in cache, API queries Postgres database
Response redirects user to long URL
'''

mermaid = render_system_design(design)
print(mermaid)

# Copy output and paste into: https://mermaid.live/
```

---

## Quick Test: Difficulty Scaling

```python
from backend.ai.difficulty_scaler import create_scaler_from_resume

resume = '''
Senior Python Developer
5+ years experience with Django, Flask, FastAPI
Strong algorithms and data structures background
Proficient in system design at scale
'''

scaler = create_scaler_from_resume(resume)

# Simulate performance
scaler.update_performance(
    category="algorithms",
    correctness=0.9,  # 90% correct
    time_taken=300,   # 5 minutes
    clarity_score=0.85,
    depth_score=0.8
)

scaler.update_performance(
    category="algorithms",
    correctness=0.95,
    time_taken=250,
    clarity_score=0.9,
    depth_score=0.85
)

# Get next difficulty (should scale up)
next_diff = scaler.get_next_difficulty("algorithms")
print(f"Next difficulty: {next_diff.value}")  # Expected: "hard"

# Get summary
summary = scaler.get_performance_summary()
print(f"Overall proficiency: {summary['overall_proficiency']}")
print(f"Strengths: {summary['strengths']}")
```

---

## Quick Test: Scoring Rubrics

```python
from backend.ai.scoring_rubrics import score_answer, QuestionType

# Test behavioral answer
behavioral_answer = '''
At my previous company, we faced a critical production bug affecting 10,000 users.
I took the lead in investigating the issue, identified it was a race condition in our 
payment processing service. I implemented a distributed lock using Redis, thoroughly 
tested the fix, and deployed it within 4 hours. As a result, we prevented potential
revenue loss of $50,000 and improved system reliability. I learned the importance
of proper concurrency handling in distributed systems.
'''

result = score_answer(
    QuestionType.BEHAVIORAL,
    behavioral_answer,
    proficiency_level="Senior"
)

print(f"Score: {result.overall_score}/100")
print(f"Strengths: {result.strengths}")
print(f"Improvements: {result.improvements}")
print(f"\nFeedback:\n{result.feedback}")
```

---

## API Usage Examples

### Start Session
```bash
curl -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "resume_text": "Python developer, 5 years...",
    "role": "SDE"
  }'
```

### Validate Code
```bash
curl -X POST http://localhost:8000/code/validate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def two_sum(nums, target): ...",
    "language": "python",
    "test_cases": [
      {"input": [[2,7,11,15], 9], "expected": [0,1]}
    ]
  }'
```

### Render Diagram
```bash
curl -X POST http://localhost:8000/systemdesign/render \
  -H "Content-Type: application/json" \
  -d '{
    "design_text": "Client connects to API Gateway..."
  }'
```

### Get Session Report
```bash
curl http://localhost:8000/session/report/session_1
```

---

## Troubleshooting

### Code validation fails
- **Issue**: "Tesseract not found"
- **Fix**: Install Tesseract OCR (not required for code validation)

### API won't start
- **Issue**: Port 8000 already in use
- **Fix**: Change port in `api_service.py` or kill existing process

### Import errors
- **Issue**: Module not found
- **Fix**: Run `pip install -r requirements.txt` and ensure you're in the right directory

---

## File Structure

```
meeting-agent/
├── backend/
│   ├── ai/
│   │   ├── interview_engine.py           # Original engine
│   │   ├── enhanced_interview_engine.py  # ✨ Enhanced with validation
│   │   ├── difficulty_scaler.py          # ✨ Adaptive difficulty
│   │   ├── scoring_rubrics.py            # ✨ Comprehensive rubrics
│   │   ├── resume_parser.py
│   │   └── scoring.py
│   ├── api/
│   │   ├── api_service.py                # ✨ FastAPI REST API
│   │   └── __init__.py
│   ├── validation/
│   │   ├── code_validator.py             # ✨ Code sandbox
│   │   └── __init__.py
│   ├── rendering/
│   │   ├── diagram_renderer.py           # ✨ Mermaid generator
│   │   └── __init__.py
│   └── capture/
│       ├── screen_capture.py
│       └── ocr_processor.py
├── frontend/
│   ├── main.py                           # Desktop app
│   ├── overlay.py                        # Transparent UI
│   └── audio_listener.py
├── requirements.txt                      # ✨ Updated with FastAPI
├── run.py
├── ADVANCED_CAPABILITIES.md              # ✨ Full documentation
├── TRANSPARENT_UI_GUIDE.md
└── KEYBOARD_SHORTCUTS.md
```

---

## What's Next?

### Integrate Enhanced Engine
Replace `InterviewEngine` with `EnhancedInterviewEngine` in `frontend/main.py`:

```python
from backend.ai.enhanced_interview_engine import EnhancedInterviewEngine

self.engine = EnhancedInterviewEngine(role=self.current_role)
```

### Add Code Detection
Detect when code is shown on screen and extract it for validation

### Enable Diagram Rendering
When system design question detected, render Mermaid in UI

### Track Performance
Use difficulty scaler to adjust question difficulty in real-time

---

## Resources

- **API Docs**: http://localhost:8000/docs (when API running)
- **Mermaid Live Editor**: https://mermaid.live/
- **Full Docs**: See `ADVANCED_CAPABILITIES.md`
- **UI Guide**: See `TRANSPARENT_UI_GUIDE.md`
- **Shortcuts**: See `KEYBOARD_SHORTCUTS.md`

---

**🎉 You're all set! Start building amazing interview experiences!**

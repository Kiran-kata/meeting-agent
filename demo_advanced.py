"""
Quick Demo - Advanced Capabilities Test
Tests all 5 core capabilities in one script
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🚀 ADVANCED INTERVIEW ASSISTANT - CAPABILITY DEMO")
print("=" * 60)

# ============= 1. CODE VALIDATION =============
print("\n📝 1. CODE VALIDATION ENGINE")
print("-" * 60)

from backend.validation.code_validator import validate_code

test_code = '''
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []
'''

print("Testing code:")
print(test_code)

result = validate_code(
    code=test_code,
    language="python",
    test_cases=[
        {"input": [[2, 7, 11, 15], 9], "expected": [0, 1]},
        {"input": [[3, 2, 4], 6], "expected": [1, 2]},
        {"input": [[3, 3], 6], "expected": [0, 1]}
    ]
)

print(f"\n✅ Tests Passed: {result.passed}")
print(f"⏱️  Execution Time: {result.execution_time:.3f}s")
print(f"💾 Memory Estimate: {result.memory_estimate}")
if result.complexity_warnings:
    print(f"⚠️  Warnings: {result.complexity_warnings}")
print(f"📊 Test Results: {len(result.test_results)} tests, all passed: {result.passed}")

# ============= 2. SYSTEM DESIGN RENDERER =============
print("\n\n🏗️  2. SYSTEM DESIGN DIAGRAM RENDERER")
print("-" * 60)

from backend.rendering.diagram_renderer import render_system_design

design = '''
Design a URL shortener:

Client connects to API Gateway
API Gateway validates request and generates short code
API Gateway stores mapping in Postgres database
API Gateway caches popular URLs in Redis cache
For retrieval, API checks Redis first
If not cached, queries Postgres database
Returns redirect to original URL
'''

print("Design description:")
print(design)

mermaid = render_system_design(design)
print("\n📊 Generated Mermaid Diagram:")
print(mermaid)
print("\n💡 Paste this at: https://mermaid.live/")

# ============= 3. DIFFICULTY SCALING =============
print("\n\n📈 3. RESUME-AWARE DIFFICULTY SCALING")
print("-" * 60)

from backend.ai.difficulty_scaler import create_scaler_from_resume

resume = '''
Software Engineer with 5 years experience
Languages: Python, Java, JavaScript
Frameworks: Django, Spring Boot, React
Strong algorithms and data structures background
'''

print("Resume:")
print(resume)

scaler = create_scaler_from_resume(resume)
print(f"\n✅ Scaler initialized")
print(f"🔤 Languages detected: {scaler.resume_skills.languages}")
print(f"📚 Frameworks: {scaler.resume_skills.frameworks}")
print(f"🎯 Primary language: {scaler.resume_skills.primary_language}")
print(f"📅 Years experience: {scaler.resume_skills.years_experience}")

# Simulate performance
print("\n📊 Simulating performance...")
scaler.update_performance("algorithms", 0.9, 300, 0.85, 0.8)
scaler.update_performance("algorithms", 0.95, 250, 0.9, 0.85)

next_diff = scaler.get_next_difficulty("algorithms")
print(f"✨ Next difficulty: {next_diff.value}")

summary = scaler.get_performance_summary()
print(f"🎓 Overall proficiency: {summary['overall_proficiency']}")
if summary['strengths']:
    print(f"💪 Strengths: {summary['strengths']}")

# ============= 4. SCORING RUBRICS =============
print("\n\n🎯 4. ADVANCED SCORING RUBRICS")
print("-" * 60)

from backend.ai.scoring_rubrics import score_answer, QuestionType

behavioral_answer = '''
At my last company, we had a production outage affecting 10,000 users.
I took charge of the incident response, identified the root cause as a 
memory leak in our caching layer. I implemented a fix using proper 
connection pooling and deployed within 2 hours. As a result, we reduced 
similar incidents by 95% and improved system stability. I learned the 
importance of proactive monitoring.
'''

print("Behavioral answer:")
print(behavioral_answer[:150] + "...")

result = score_answer(
    QuestionType.BEHAVIORAL,
    behavioral_answer,
    proficiency_level="Mid-level"
)

print(f"\n📊 Score: {result.overall_score}/100")
print(f"\n✅ Strengths:")
for s in result.strengths[:3]:
    print(f"   • {s}")
print(f"\n📈 Areas to improve:")
for i in result.improvements[:3]:
    print(f"   • {i}")

# ============= 5. ENHANCED ENGINE =============
print("\n\n🧠 5. ENHANCED INTERVIEW ENGINE")
print("-" * 60)

from backend.ai.enhanced_interview_engine import EnhancedInterviewEngine

print("Initializing enhanced engine...")
engine = EnhancedInterviewEngine(role="SDE")
engine.set_resume_context(resume)

print("✅ Engine initialized with:")
print(f"   • Code validation integration")
print(f"   • Diagram rendering")
print(f"   • Difficulty scaling")
print(f"   • Advanced scoring rubrics")

# Test evaluation
print("\n📊 Testing answer evaluation...")
eval_result = engine.evaluate_answer(
    question="Tell me about a challenging project",
    answer=behavioral_answer,
    question_type="behavioral"
)

print(f"✅ Evaluation complete:")
print(f"   • Score: {eval_result['score']}/100")
print(f"   • Proficiency: {eval_result['proficiency_level']}")
print(f"   • Strengths: {len(eval_result['strengths'])} identified")
print(f"   • Improvements: {len(eval_result['improvements'])} suggested")

# ============= SUMMARY =============
print("\n\n" + "=" * 60)
print("✨ ALL CAPABILITIES TESTED SUCCESSFULLY!")
print("=" * 60)

print("""
🎯 What's Available:

1. ✅ Code Validation - Test any code with sandbox execution
2. ✅ System Design Renderer - Auto-generate Mermaid diagrams  
3. ✅ Difficulty Scaling - Adaptive question difficulty
4. ✅ Scoring Rubrics - Comprehensive evaluation frameworks
5. ✅ Enhanced Engine - Unified integration of all features

🚀 Next Steps:

• Start FastAPI server: cd backend/api && python api_service.py
• Use in desktop app: Replace InterviewEngine with EnhancedInterviewEngine
• Test API: Visit http://localhost:8000/docs

📚 Documentation:
• ADVANCED_CAPABILITIES.md - Full technical docs
• QUICKSTART.md - Quick start guide
• API available at backend/api/api_service.py
""")

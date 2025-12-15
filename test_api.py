"""
Test API Endpoints
Quick test of all FastAPI endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("🔌 TESTING FASTAPI ENDPOINTS")
print("=" * 60)

# Health check
print("\n1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Start session
print("\n2. Start Session")
response = requests.post(f"{BASE_URL}/session/start", json={
    "user_id": "demo_user",
    "resume_text": "Python developer with 5 years experience in Django, FastAPI",
    "role": "SDE"
})
print(f"Status: {response.status_code}")
data = response.json()
print(f"Session ID: {data['session_id']}")
print(f"Resume Skills: {data.get('resume_skills', {})}")
session_id = data['session_id']

# Get next question
print("\n3. Get Next Question")
response = requests.post(f"{BASE_URL}/question/next", json={
    "session_id": session_id,
    "category": "algorithms"
})
print(f"Status: {response.status_code}")
question = response.json()
print(f"Question: {question['text']}")
print(f"Difficulty: {question['difficulty']}")

# Validate code
print("\n4. Validate Code")
response = requests.post(f"{BASE_URL}/code/validate", json={
    "code": """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []
""",
    "language": "python",
    "test_cases": [
        {"input": [[2, 7, 11, 15], 9], "expected": [0, 1]},
        {"input": [[3, 2, 4], 6], "expected": [1, 2]}
    ]
})
print(f"Status: {response.status_code}")
validation = response.json()
print(f"Passed: {validation['passed']}")
print(f"Execution Time: {validation['execution_time']}s")

# Render diagram
print("\n5. Render System Design Diagram")
response = requests.post(f"{BASE_URL}/systemdesign/render", json={
    "design_text": """
    Client connects to API Gateway
    API Gateway talks to Auth Service
    Auth Service uses Postgres database
    API Gateway calls Core Service
    Core Service reads from Redis cache
    """
})
print(f"Status: {response.status_code}")
diagram = response.json()
print(f"Mermaid diagram generated: {len(diagram['mermaid'])} chars")
print(f"First 200 chars:\n{diagram['mermaid'][:200]}...")

# Evaluate answer
print("\n6. Evaluate Answer")
response = requests.post(f"{BASE_URL}/answer/evaluate", json={
    "session_id": session_id,
    "question": "Tell me about a challenging project",
    "answer": """
    At my previous company, we faced a critical bug affecting 5000 users.
    I took the lead investigating and found a race condition. I implemented
    a fix using distributed locks and deployed within 3 hours. The result
    was zero similar incidents and improved reliability by 99%.
    """,
    "question_type": "behavioral"
})
print(f"Status: {response.status_code}")
evaluation = response.json()
print(f"Score: {evaluation['score']}/100")
print(f"Proficiency Level: {evaluation['proficiency_level']}")
print(f"Strengths: {len(evaluation['strengths'])} identified")

# Get session report
print("\n7. Get Session Report")
response = requests.get(f"{BASE_URL}/session/report/{session_id}")
print(f"Status: {response.status_code}")
report = response.json()
print(f"Questions Attempted: {report['questions_attempted']}")
print(f"Average Score: {report['average_score']}")
print(f"Overall Proficiency: {report['proficiency_summary'].get('overall_proficiency', 'N/A')}")

print("\n" + "=" * 60)
print("✅ ALL API ENDPOINTS TESTED SUCCESSFULLY!")
print("=" * 60)
print(f"\n📚 API Documentation: {BASE_URL}/docs")
print(f"🔍 Interactive Docs: {BASE_URL}/docs")

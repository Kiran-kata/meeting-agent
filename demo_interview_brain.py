"""
Interview Brain Demo - Full demonstration of the multi-modal interview assistant.

This demo shows:
1. Screen capture → OCR text extraction
2. Resume loading → Language detection
3. Question detection (from screen + audio)
4. Context merging and prioritization
5. AI-powered response generation

Run: python demo_interview_brain.py
"""
import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


def demo_basic_flow():
    """Demo 1: Basic question → answer flow."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Question → Answer Flow")
    print("="*60)
    
    from backend.ai import InterviewBrain
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return
    
    brain = InterviewBrain(api_key=api_key)
    print("✅ Interview Brain initialized")
    
    # Simulate a coding question
    question = "Write a function to reverse a linked list in Python"
    print(f"\n📝 Question: {question}\n")
    print("-" * 40)
    print("🤖 Response:\n")
    
    for chunk in brain.process_question(question):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 40)


def demo_resume_aware():
    """Demo 2: Resume-aware language selection."""
    print("\n" + "="*60)
    print("DEMO 2: Resume-Aware Language Selection")
    print("="*60)
    
    from backend.ai import InterviewBrain
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return
    
    brain = InterviewBrain(api_key=api_key)
    
    # Sample resume text
    resume_text = """
    JOHN DOE - Software Engineer
    
    SKILLS:
    - Python (5+ years): Django, FastAPI, Pandas, NumPy
    - JavaScript (3 years): React, Node.js, Express
    - SQL: PostgreSQL, MySQL
    - AWS, Docker, Kubernetes
    
    EXPERIENCE:
    Senior Python Developer at TechCorp (2020-Present)
    - Built microservices using FastAPI
    - Implemented ML pipelines with scikit-learn
    
    Full Stack Developer at StartupXYZ (2018-2020)
    - Developed React frontend applications
    - Built REST APIs with Django
    """
    
    # Load resume
    data = brain.load_resume(resume_text)
    print(f"✅ Resume loaded")
    print(f"   Primary language: {data.primary_language}")
    print(f"   Secondary languages: {', '.join(data.secondary_languages)}")
    print(f"   Frameworks: {list(data.frameworks.keys())}")
    
    # Ask a question - should use Python based on resume
    question = "Implement a binary search algorithm"
    print(f"\n📝 Question: {question}")
    print(f"   (Should use Python based on resume)")
    print("-" * 40)
    print("🤖 Response:\n")
    
    for chunk in brain.process_question(question):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 40)


def demo_screen_context():
    """Demo 3: Screen context integration."""
    print("\n" + "="*60)
    print("DEMO 3: Screen Context Integration")
    print("="*60)
    
    from backend.ai import InterviewBrain
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return
    
    brain = InterviewBrain(api_key=api_key)
    
    # Simulate screen content (as if OCR extracted this)
    screen_content = """
    LeetCode - Two Sum
    
    Given an array of integers nums and an integer target,
    return indices of the two numbers such that they add up to target.
    
    You may assume that each input would have exactly one solution,
    and you may not use the same element twice.
    
    Example 1:
    Input: nums = [2,7,11,15], target = 9
    Output: [0,1]
    Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
    """
    
    print("📺 Simulating screen capture with OCR content...")
    print("-" * 40)
    print(screen_content.strip())
    print("-" * 40)
    
    # Add screen content to brain
    brain.add_screen_content(screen_content)
    print("\n✅ Screen content added to context")
    
    # Now process - brain should understand the question from screen
    print("\n🤖 Processing detected question from screen...\n")
    
    for chunk in brain.process_question():
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 40)


def demo_question_detection():
    """Demo 4: Question detection and classification."""
    print("\n" + "="*60)
    print("DEMO 4: Question Detection & Classification")
    print("="*60)
    
    from backend.ai import QuestionDetector, QuestionCategory
    
    detector = QuestionDetector()
    
    # Test various question types
    test_questions = [
        ("Write a function to find the maximum subarray sum", "Coding"),
        ("Tell me about a time you handled a difficult teammate", "Behavioral"),
        ("Design a URL shortening service like bit.ly", "System Design"),
        ("What is the difference between SQL and NoSQL?", "Technical"),
        ("Write a SQL query to find the second highest salary", "SQL"),
    ]
    
    print("\nTesting question detection:\n")
    
    for question, expected in test_questions:
        result = detector.detect_from_text(question, source="test")
        if result:
            status = "✅" if expected.lower() in result.category.value else "⚠️"
            print(f"{status} '{question[:50]}...'")
            print(f"   Category: {result.category.value}")
            print(f"   Difficulty: {result.difficulty.value}")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Keywords: {result.keywords[:5]}")
            print()


def demo_language_selector():
    """Demo 5: Language selector from resume."""
    print("\n" + "="*60)
    print("DEMO 5: Resume Language Extraction")
    print("="*60)
    
    from backend.ai import LanguageSelector
    
    selector = LanguageSelector()
    
    resume = """
    Jane Smith - Full Stack Engineer
    
    Technical Skills:
    - TypeScript/JavaScript (4 years): React, Next.js, Node.js
    - Python (2 years): FastAPI, SQLAlchemy  
    - Go (1 year): Gin framework
    - PostgreSQL, MongoDB, Redis
    
    Experience:
    Lead Frontend Developer at WebCo
    - Built React applications with TypeScript
    - Implemented GraphQL APIs
    """
    
    data = selector.extract_from_resume(resume)
    
    print("\n📄 Resume Analysis Results:\n")
    print(f"Primary Language: {data.primary_language}")
    print(f"All Languages: {list(data.languages.keys())}")
    print(f"Frameworks Found: {data.frameworks}")
    
    print("\n🔍 Language Selection Tests:\n")
    
    questions = [
        "Write a function to sort an array",  # Should pick primary
        "Create a React component for a todo list",  # Should pick JS/TS
        "Implement a REST API endpoint",  # Should pick primary
    ]
    
    for q in questions:
        selected = selector.select_language(q)
        print(f"Q: '{q[:40]}...'")
        print(f"   → Selected: {selected}")
        print()


def demo_full_flow():
    """Demo 6: Complete integrated flow."""
    print("\n" + "="*60)
    print("DEMO 6: Full Integrated Flow")
    print("="*60)
    
    from backend.ai import InterviewBrain
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return
    
    print("\n🚀 Initializing Interview Brain with all components...\n")
    
    brain = InterviewBrain(api_key=api_key)
    
    # Load resume
    resume = """
    Alex Chen - Senior Software Engineer (5 years experience)
    
    Languages: Python (expert), JavaScript, SQL, Go
    Frameworks: Django, FastAPI, React, PostgreSQL
    
    Recent Projects:
    - Built high-performance API serving 10M requests/day
    - Implemented ML pipeline for recommendation system
    """
    
    brain.load_resume(resume)
    print("✅ Resume loaded")
    
    # Simulate screen capture
    screen_text = """
    Interview Question:
    
    Given a binary tree, implement a function to serialize and deserialize it.
    You should implement two functions:
    - serialize(root): Encode a tree to a string
    - deserialize(data): Decode a string to a tree
    """
    
    brain.add_screen_content(screen_text)
    print("✅ Screen content captured")
    
    # Show context summary
    summary = brain.get_current_context_summary()
    print(f"\n📊 Context Summary:")
    print(f"   Question Category: {summary['question_category']}")
    print(f"   Context Sources: {summary['context_sources']}")
    print(f"   Detected Language: {summary['detected_language'] or 'python (from resume)'}")
    
    print("\n" + "-" * 40)
    print("🤖 Generating Response:\n")
    
    for chunk in brain.process_question():
        print(chunk, end="", flush=True)
    
    print("\n\n" + "-" * 40)
    
    # Show final stats
    stats = brain.get_stats()
    print(f"\n📈 Final Stats:")
    print(f"   Questions detected: {stats['questions_detected']}")
    print(f"   Conversation turns: {stats['conversation_turns']}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("🎯 INTERVIEW BRAIN - FULL DEMONSTRATION")
    print("="*60)
    
    demos = [
        ("Basic Q&A", demo_basic_flow),
        ("Resume-Aware", demo_resume_aware),
        ("Screen Context", demo_screen_context),
        ("Question Detection", demo_question_detection),
        ("Language Selection", demo_language_selector),
        ("Full Integration", demo_full_flow),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos)+1}. Run all demos")
    print(f"  0. Exit")
    
    while True:
        try:
            choice = input("\nSelect demo (0-{0}): ".format(len(demos)+1))
            choice = int(choice)
            
            if choice == 0:
                print("Goodbye!")
                break
            elif choice == len(demos) + 1:
                for name, func in demos:
                    try:
                        func()
                    except Exception as e:
                        print(f"❌ Error in {name}: {e}")
                    time.sleep(1)
            elif 1 <= choice <= len(demos):
                demos[choice-1][1]()
            else:
                print("Invalid choice")
                
        except ValueError:
            print("Please enter a number")
        except KeyboardInterrupt:
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()

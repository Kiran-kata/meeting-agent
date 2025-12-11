#!/usr/bin/env python3
"""
Demo script showing Parakeet AI features in action.
Shows all the new interview-focused capabilities.
"""

import sys
import os
import io

# Fix encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from app.parakeet_features import (
    ResumeProfile,
    CodingInterviewDetector,
    MultilingualSupport,
    InterviewPerformanceAnalyzer,
    QuestionAutoDetector,
)


def demo_resume_profile():
    """Demo: Resume and Profile Management"""
    print("\n" + "="*60)
    print("DEMO 1: Resume Profile Management")
    print("="*60)
    
    profile = ResumeProfile()
    
    # Create profile
    profile.create_profile(
        name="Jane Smith",
        email="jane@example.com",
        role="Senior Software Engineer"
    )
    print(f"✓ Profile created: Jane Smith (Senior Software Engineer)")
    
    # Show profile context (this would be injected into LLM prompts)
    context = profile.get_profile_context()
    print(f"✓ Profile context ready for LLM injection")
    print(f"  Context length: {len(context)} chars")


def demo_coding_interview():
    """Demo: Coding Interview Detection"""
    print("\n" + "="*60)
    print("DEMO 2: Coding Interview Detection")
    print("="*60)
    
    detector = CodingInterviewDetector()
    
    # Example LeetCode problem
    leetcode_content = """
    LeetCode - Two Sum
    
    Given an array of integers nums and an integer target, return the 
    indices of the two numbers such that they add up to target.
    
    def twoSum(nums: List[int], target: int) -> List[int]:
        # Your solution here
        pass
    """
    
    result = detector.analyze_screen_content(leetcode_content)
    print(f"✓ Platform detected: {result['platform']}")
    print(f"✓ Is coding interview: {result['is_coding_interview']}")
    print(f"✓ Code visible: {result['code_visible']}")
    print(f"✓ Problem text extracted: {len(result['problem_text'])} chars")


def demo_multilingual():
    """Demo: Multilingual Support"""
    print("\n" + "="*60)
    print("DEMO 3: Multilingual Support (52+ Languages)")
    print("="*60)
    
    ml = MultilingualSupport()
    
    languages = ['en', 'es', 'fr', 'de', 'ja', 'zh', 'ar', 'hi']
    
    for lang_code in languages:
        success = ml.set_language(lang_code)
        if success:
            lang_name = ml.SUPPORTED_LANGUAGES[lang_code]
            instruction = ml.get_language_instruction()
            print(f"✓ {lang_code:5} -> {lang_name:20} | {instruction}")
    
    print(f"✓ Total supported languages: {len(ml.SUPPORTED_LANGUAGES)}")


def demo_performance_analysis():
    """Demo: Interview Performance Analysis"""
    print("\n" + "="*60)
    print("DEMO 4: Interview Performance Analysis")
    print("="*60)
    
    analyzer = InterviewPerformanceAnalyzer()
    
    # Simulate interview
    analyzer.start_interview()
    print(f"✓ Interview started")
    
    # Add some Q&A pairs
    qa_pairs = [
        ("Tell me about yourself", "I'm a software engineer with 5 years of experience...", 15.2),
        ("What's your strongest skill?", "I'm particularly strong in backend systems design...", 12.8),
        ("Describe a challenging project", "One challenging project involved optimizing database queries...", 28.5),
        ("How do you handle conflicts?", "I believe in open communication and collaboration...", 18.3),
        ("Why do you want this role?", "I'm excited about this role because...", 10.5),
    ]
    
    for question, answer, time_taken in qa_pairs:
        analyzer.add_qa_pair(question, answer, time_taken)
    
    print(f"✓ Logged {len(qa_pairs)} Q&A pairs")
    
    # Generate analysis
    analysis = analyzer.end_interview()
    
    print(f"\n📊 Interview Metrics:")
    print(f"   Duration: {analysis['interview_duration_minutes']:.1f} minutes")
    print(f"   Questions: {analysis['total_questions']}")
    print(f"   Avg Answer Time: {analysis['average_answer_time_seconds']:.1f} seconds")
    print(f"   Efficiency: {analysis['interview_efficiency']}")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(analysis['recommendations'][:3], 1):
        print(f"   {i}. {rec}")


def demo_question_categorization():
    """Demo: Automatic Question Categorization"""
    print("\n" + "="*60)
    print("DEMO 5: Question Auto-Detection & Categorization")
    print("="*60)
    
    detector = QuestionAutoDetector()
    
    test_questions = [
        ("Tell me about a time you failed", "behavioral"),
        ("How would you design a database?", "technical"),
        ("What would you do if you disagreed with your manager?", "situational"),
        ("How would you solve the Two Sum problem?", "problem_solving"),
    ]
    
    for question, expected_category in test_questions:
        detected_category = detector.categorize_question(question)
        template = detector.get_response_template(detected_category)
        
        match = "✓" if detected_category == expected_category else "⚠"
        print(f"{match} '{question[:40]}...'")
        print(f"   Category: {detected_category} | Template: {template}")


def demo_stealth_mode():
    """Demo: Stealth Mode Features"""
    print("\n" + "="*60)
    print("DEMO 6: Stealth Mode (Privacy Features)")
    print("="*60)
    
    print("✓ Stealth mode includes:")
    print("   • Hidden from screen share")
    print("   • Invisible in dock/taskbar")
    print("   • Hidden from task manager")
    print("   • No visibility in alt-tab")
    print("   • Cursor undetectable")
    print("   • Window fully invisible when enabled")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("PARAKEET AI FEATURES DEMO")
    print("="*60)
    print("Demonstrating all Parakeet AI-inspired features:")
    
    try:
        demo_resume_profile()
        demo_coding_interview()
        demo_multilingual()
        demo_performance_analysis()
        demo_question_categorization()
        demo_stealth_mode()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nThe agent is now ready with Parakeet AI features:")
        print("  • Resume-matched interview responses")
        print("  • Coding interview support (LeetCode, HackerRank, etc.)")
        print("  • 52+ language support")
        print("  • Performance analysis & recommendations")
        print("  • Smart question categorization")
        print("  • Advanced privacy/stealth features")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

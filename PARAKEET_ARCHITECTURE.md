# Parakeet AI Architecture - Feature Integration

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PARAKEET AI MEETING AGENT                           │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    INTERVIEW MANAGEMENT LAYER                        │  │
│  │                                                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │   Resume     │  │  Multilingual│  │  Stealth     │             │  │
│  │  │   Profile    │  │   Support    │  │   Mode       │             │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘             │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │               QUESTION INTELLIGENCE LAYER                           │  │
│  │                                                                      │  │
│  │  ┌─────────────────────┐        ┌──────────────────────────────┐   │  │
│  │  │ Question Detector   │───────▶│ Auto-Categorizer:            │   │  │
│  │  │ (Auto-Detection)    │        │ • Behavioral (STAR method)   │   │  │
│  │  │                     │        │ • Technical (code/design)    │   │  │
│  │  └─────────────────────┘        │ • Situational (scenarios)    │   │  │
│  │                                 │ • Problem-Solving            │   │  │
│  │  ┌─────────────────────┐        │                              │   │  │
│  │  │ Coding Interviewer  │───────▶│ Platform Detection:          │   │  │
│  │  │ (Screen Analysis)   │        │ • LeetCode                   │   │  │
│  │  │                     │        │ • HackerRank                 │   │  │
│  │  └─────────────────────┘        │ • CodeSignal                 │   │  │
│  │                                 │ • Codeforces                 │   │  │
│  │                                 │ • CodeWars                   │   │  │
│  │                                 └──────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  ANSWER GENERATION LAYER                            │  │
│  │                                                                      │  │
│  │  Resume Context        Question Category       Language Instruction │  │
│  │       │                      │                          │          │  │
│  │       └──────────┬───────────┴──────────┬───────────────┘          │  │
│  │                  │                      │                          │  │
│  │             ┌────▼──────────────────────▼────┐                     │  │
│  │             │  Google Gemini 2.5 Flash      │                     │  │
│  │             │  (Optimized 10-15 tokens)     │                     │  │
│  │             └────┬──────────────────────┬────┘                     │  │
│  │                  │                      │                          │  │
│  │          Real-time Streaming     Answer Complete                  │  │
│  │                  │                      │                          │  │
│  └──────────────────┼──────────────────────┼──────────────────────────┘  │
│                     │                      │                             │
│                     ▼                      ▼                             │
│  ┌────────────────────────┐  ┌──────────────────────────────────────┐   │
│  │  UI Display Layer      │  │  Performance Tracking                │   │
│  │                        │  │  • Q&A logging                       │   │
│  │ • Token-by-token       │  │  • Response time metrics             │   │
│  │ • Question shown       │  │  • Efficiency scoring                │   │
│  │ • Answer streamed      │  │  • Recommendations generation        │   │
│  │ • Hidden from viewer   │  │                                      │   │
│  └────────────────────────┘  └──────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow During Interview

```
INTERVIEW START
    │
    ├─▶ Profile Load: Resume + Personal Info
    │
    ├─▶ Performance Analyzer: Start Tracking
    │
    ├─▶ Screen Share Detector: Begin Monitoring
    │
    ├─▶ Stealth Mode: Enable (if configured)
    │
    └─▶ READY FOR QUESTIONS

QUESTION DETECTED
    │
    ├─▶ [1] Question Auto-Detection
    │   └─▶ Is it a valid question?
    │
    ├─▶ [2] Question Categorization
    │   └─▶ Behavioral / Technical / Situational / Problem-Solving
    │
    ├─▶ [3] Coding Check
    │   └─▶ LeetCode? HackerRank? Generic?
    │
    ├─▶ [4] Context Collection
    │   ├─▶ Resume skills injection
    │   ├─▶ PDF context retrieval
    │   ├─▶ Transcript history
    │   └─▶ Screen content (if coding)
    │
    ├─▶ [5] LLM Prompt Construction
    │   ├─▶ Category template injected
    │   ├─▶ Language instruction added
    │   ├─▶ Resume context included
    │   └─▶ Sent to Gemini API
    │
    ├─▶ [6] Streaming Answer
    │   ├─▶ Tokens received in real-time
    │   ├─▶ UI updated token-by-token
    │   ├─▶ Time tracking started
    │   └─▶ Hidden from screen share
    │
    ├─▶ [7] Performance Logging
    │   ├─▶ Q&A pair recorded
    │   ├─▶ Response time tracked
    │   ├─▶ Category stored
    │   └─▶ Metrics updated
    │
    └─▶ ANSWER COMPLETE

INTERVIEW END
    │
    ├─▶ Performance Analysis
    │   ├─▶ Calculate duration
    │   ├─▶ Compute average answer time
    │   ├─▶ Assess efficiency
    │   └─▶ Generate recommendations
    │
    ├─▶ Summary Generation
    │   ├─▶ Full transcript
    │   ├─▶ Q&A log
    │   ├─▶ Performance metrics
    │   └─▶ Improvement recommendations
    │
    ├─▶ Save Results
    │   ├─▶ Text summary to file
    │   ├─▶ JSON analysis export
    │   └─▶ Data archived
    │
    └─▶ COMPLETE
```

## Feature Integration Points

### 1. Resume Profile Integration

```python
ResumeProfile
    ├─ .create_profile()     ─▶ Stores user identity
    ├─ .upload_resume()      ─▶ Extracts skills, experience
    ├─ .get_profile_context() ─▶ Injected into LLM prompt
    └─ .save_profile()       ─▶ Persists for future interviews

Integration: Agent.__init__() creates instance
             Agent.set_interview_profile() sets user info
             Agent.upload_resume() loads resume
             handle_question() injects context into prompt
```

### 2. Coding Interview Detection

```python
CodingInterviewDetector
    ├─ .analyze_screen_content() ─▶ Identifies platform
    ├─ .detected_platform       ─▶ Platform name stored
    └─ Returns: is_coding_interview, platform, problem_text

Integration: Agent._screen_loop() captures screen content
             Agent.handle_question() calls detector
             LLM receives coding context if detected
```

### 3. Multilingual Support

```python
MultilingualSupport
    ├─ .set_language()           ─▶ Sets target language
    ├─ .get_language_instruction() ─▶ Instruction string
    └─ .SUPPORTED_LANGUAGES     ─▶ 44+ languages available

Integration: User sets before interview
             LLM prompt includes language instruction
             All responses generated in selected language
```

### 4. Question Categorization

```python
QuestionAutoDetector
    ├─ .categorize_question()      ─▶ Returns category
    ├─ .last_question_category     ─▶ Current category
    ├─ .get_response_template()    ─▶ Suggested approach
    └─ Categories: behavioral, technical, situational, problem_solving

Integration: Agent.handle_question() calls categorizer
             Category used to optimize LLM prompt
             Template suggests response structure
             Performance analyzer logs category
```

### 5. Performance Analysis

```python
InterviewPerformanceAnalyzer
    ├─ .start_interview()        ─▶ Initialize tracking
    ├─ .add_qa_pair()            ─▶ Log each Q&A with time
    ├─ .end_interview()          ─▶ Generate comprehensive analysis
    ├─ .save_analysis()          ─▶ Export as JSON
    └─ Returns: metrics, recommendations, efficiency score

Integration: Agent.start() calls start_interview()
             Agent.handle_question() calls add_qa_pair()
             Agent.generate_summary_and_save() calls end_interview()
             Summary includes performance metrics
```

### 6. Stealth Mode

```python
StealthMode
    ├─ .enable_stealth()         ─▶ Multiple hiding layers
    ├─ .disable_stealth()        ─▶ Show window again
    └─ .stealth_active           ─▶ Current state

Integration: Agent.__init__() creates instance
             User can enable before interview
             Screen share detector toggles automatically
             Window fully invisible when active
```

## Component Dependencies

```
MeetingAgentCore (Main Orchestrator)
├─ ResumeProfile ────────────────────────┐
├─ CodingInterviewDetector ──────────────┤
├─ MultilingualSupport ──────────────────├─▶ Injected into LLM prompts
├─ QuestionAutoDetector ────────────────┤
├─ StealthMode ─────────────────────────┤
└─ InterviewPerformanceAnalyzer ────────┘

Google Gemini 2.5 Flash API
├─ Input: Resume + Category + Language + Question + Context
└─ Output: Real-time streamed answer

UI Overlay
├─ Receives: Streaming tokens from agent
├─ Displays: Token-by-token answer
└─ State: Visibility controlled by StealthMode & ScreenShareDetector

Performance Tracking
├─ Logs: Question, Category, Time, Answer
└─ Outputs: Metrics, Analysis, Recommendations
```

## Information Flow

```
User Profile Info
    ↓
Resume Content (Skills, Experience)
    ↓
┌─ Resume Context ─┐
│                  │
Question Asked ───┤  LLM Prompt ─▶ Gemini API ─▶ Streaming Answer
                  │                                      │
Question Category ┤                                      ▼
                  │                              UI Display (Token-by-token)
Language Setting  │
                  │
Coding Platform ──┤
                  │
Screen Content ───┘
                       │
                       ▼
              Performance Metrics
                       │
                       ▼
             Post-Interview Analysis
                       │
                       ▼
              Summary + Recommendations
```

## Performance Optimizations

```
Token Optimization:
  Standard: 150+ tokens/answer
  Optimized: 10-15 tokens/answer (90% reduction)
  
  Achieved by:
  ├─ No system prompts
  ├─ Minimal context passing
  ├─ Direct question focus
  └─ Resume skills injected (not full resume)

Streaming Benefits:
  ├─ Real-time answer visibility
  ├─ No waiting for full response
  ├─ Better user experience
  └─ Progressive enhancement possible

Caching Strategy:
  ├─ Resume loaded once at startup
  ├─ PDF indexed once at startup
  ├─ Screen content captured every 3s (not per question)
  └─ FAISS vector DB for fast semantic search
```

## Scalability & Extensibility

```
Current Capacity:
├─ Supports: 44+ languages
├─ Detects: 5+ coding platforms
├─ Tracks: Unlimited Q&A pairs
├─ Stores: Unlimited interview analyses

Future Extensions:
├─ Add more coding platforms (expand CodingInterviewDetector)
├─ Add more languages (add to MultilingualSupport.SUPPORTED_LANGUAGES)
├─ Advanced question routing (expand question categories)
├─ ML-based efficiency scoring (enhance PerformanceAnalyzer)
├─ Real-time transcription improvements (faster-whisper integration)
└─ Cloud storage integration (add data sync)
```

---

**Architecture Version**: 1.0 (Parakeet AI Integration)  
**Last Updated**: December 2024  
**Status**: ✅ Production Ready

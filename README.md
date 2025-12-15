# 🦜 Interview Assistant (Parakeet AI Style)

A fully functional AI Interview Assistant with real-time voice interviews, resume-based questions, behavioral/technical scoring, and performance analytics.

## 🚀 Features

- **Voice Interview Mode** - Real-time speech-to-text with live feedback
- **Resume Analysis** - Upload PDF, extract skills, generate tailored questions
- **Behavioral Interview** - STAR framework analysis with probing follow-ups
- **Technical Interview** - DSA, System Design, ML, Backend challenges
- **Smart Follow-ups** - Detects weak points and challenges them
- **Live Scoring** - Real-time performance metrics and recommendations
- **Stealth Mode** - Hidden from screen sharing (Windows)
- **Role Templates** - SDE, Data Engineer, ML Engineer, PM, QA

## 📁 Project Structure

```
interview-assistant/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── ai/
│   │   ├── interview_engine.py   # Core interview logic
│   │   ├── scoring.py            # STAR & technical scoring
│   │   ├── resume_parser.py      # PDF extraction
│   │   └── followup_generator.py # Smart follow-ups
│   ├── routers/
│   │   ├── interview.py     # Interview endpoints
│   │   └── resume.py        # Resume endpoints
│   └── models/
│       └── schemas.py       # Pydantic models
├── frontend/
│   ├── overlay.py           # PyQt6 stealth overlay
│   └── main.py              # Application entry
├── config.py                # Configuration
├── requirements.txt         # Dependencies
└── run.py                   # Start script
```

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key in .env
GEMINI_API_KEY=your_key_here

# 3. Run the assistant
python run.py
```

## 🎤 Usage

1. **Upload Resume** - Click "📄 Resume" to upload your PDF
2. **Select Role** - Choose interview type (SDE, ML, PM, etc.)
3. **Start Interview** - Click "▶ Start" to begin
4. **Answer Questions** - Speak naturally, get real-time coaching
5. **Review Score** - Close to see performance analysis

## 🔧 Configuration

Edit `config.py` to customize:
- Audio device indices
- Interview difficulty
- Scoring weights
- Follow-up aggressiveness

## 📊 Scoring System

| Metric | Weight | Description |
|--------|--------|-------------|
| STAR Structure | 25% | Situation, Task, Action, Result |
| Technical Accuracy | 30% | Correctness of technical answers |
| Communication | 20% | Clarity, conciseness, confidence |
| Problem Solving | 25% | Approach, optimization, edge cases |

## 🛡️ Stealth Mode

The overlay is automatically hidden from:
- Screen sharing (Zoom, Teams, Discord)
- Screen recording software
- Task manager (optional)

## 📄 License

MIT License - Use freely for practice and learning.

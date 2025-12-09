# Meeting Agent 🤖

An intelligent AI-powered meeting assistant that captures real-time audio, detects questions, extracts screen content, and generates comprehensive meeting summaries using **Google Gemini API**.

## Features ✨

- **Real-time Audio Capture** - Listen to both meeting audio and your microphone
- **Smart Transcription** - Use Gemini's audio-to-text for accurate speech recognition
- **Intelligent Q&A** - Automatically detect questions and get AI-powered answers
- **PDF Document Analysis** - Upload PDFs and analyze them during meetings ⭐ NEW
- **Screen Analysis** - Capture and OCR text from your screen with Gemini vision
- **PDF Search** - Index and search through reference documents
- **Audio Narration** - Get spoken answers using Windows text-to-speech ⭐ NEW
- **Meeting Summaries** - Generate structured summaries with action items
- **Always-on-Top Overlay** - Draggable, transparent overlay window to see behind it
- **Apple-Inspired UI** - Modern, sleek dark theme design with PDF upload button

## Quick Start 🚀

### 1. Prerequisites

- Python 3.8+
- Google Gemini API key (get one at https://aistudio.google.com/app/apikey)
- Tesseract OCR (optional, for screen text extraction)

### 2. Setup Virtual Environment

```powershell
cd %USERPROFILE%\Documents\meeting-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Gemini API Key

1. Get your API key from: https://aistudio.google.com/app/apikey
2. Edit `.env` file:
   ```
   GEMINI_API_KEY=your-actual-key-here
   TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```
3. Save the file

### 5. Configure Audio Devices (Important!)

Check which audio devices you have:

```powershell
.venv\Scripts\python.exe -c "import sounddevice as sd; print(sd.query_devices())"
```

Update `app/main.py`:
```python
MEETING_DEVICE_INDEX = 9    # Your meeting audio (Stereo Mix, virtual cable, etc.)
MIC_DEVICE_INDEX = 2        # Your microphone
```

### 6. Run the Agent

```powershell
.venv\Scripts\python.exe -m app.main
```

You should see a dark overlay window appear in the top-left corner with:
- 📄 **Add PDF** button (blue) - Upload documents before meeting
- 🟢 **Start** button (green) - Begin recording
- 🔴 **Stop** button (red) - End recording and generate summary
- 📊 Status indicator showing Recording/Stopped

## Usage Guide

### Basic Meeting Flow

1. **Prepare with PDFs** (Optional):
   - Click "📄 Add PDF" button
   - Select any PDF documents you want analyzed
   - Agent will search these documents when answering questions

2. **Start Recording**:
   - Click "▶ Start" button
   - Agent begins listening to meeting audio and screen

3. **During Meeting**:
   - Agent detects questions automatically
   - Combines context from:
     - Meeting transcript
     - Your uploaded PDFs
     - Current screen content
   - Answers are **spoken aloud** + displayed
   - Q&A is logged for summary

4. **End Meeting**:
   - Click "⏹ Stop" button
   - Meeting summary is generated
   - Summary saved to `meeting_summaries/summary_*.txt`

### PDF Features

**Add PDFs Before Meeting:**
```
1. Click "📄 Add PDF" button
2. Select a PDF file
3. File is indexed for question answering
4. Can add multiple PDFs
5. Start meeting when ready
```

**During Meeting:**
- Questions automatically search uploaded PDFs
- Relevant PDF content is included in answers
- Answers cite PDF sections
- Voice narration speaks all answers

**After Meeting:**
- Summary includes PDF-sourced Q&A
- Can add more PDFs and start a new meeting

### Example: Policy Discussion Meeting

```
1. Click "📄 Add PDF" → Load "company-policies.pdf"
2. Click "📄 Add PDF" → Load "employee-handbook.pdf"
3. Click "▶ Start"

During Meeting:
- Q: "What's our vacation policy?"
- Agent searches PDFs → Finds policy section
- Answer combines PDF content + meeting context
- Answer is SPOKEN aloud

4. Click "⏹ Stop"
   - Summary includes all policy Q&A
   - PDF content included in summary
   - Saved to meeting_summaries/
```

## Project Structure

```
meeting-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration & Gemini API setup
│   ├── overlay.py              # PyQt6 UI overlay (draggable & transparent)
│   ├── agent.py                # Core meeting agent logic
│   ├── llm_client.py           # Gemini API integration
│   ├── audio_meeting.py        # Meeting audio capture
│   ├── audio_mic.py            # Microphone audio capture
│   ├── screen_capture.py       # Screen capture & OCR
│   ├── question_detector.py    # Question detection with Gemini
│   ├── context_manager.py      # Meeting context tracking
│   ├── pdf_index.py            # PDF indexing & search
│   └── ...
├── data/                       # Reference PDFs and data
├── logs/                       # Application logs
├── meeting_summaries/          # Generated summaries
├── .env                        # API keys (create this)
├── requirements.txt            # Python dependencies (uses google-generativeai)
└── README.md                   # This file
```

## How to Use

### During a Meeting

1. **Start the Agent**
   ```powershell
   .venv\Scripts\python.exe -m app.main
   ```

2. **Move the Overlay** - Drag the overlay window around to position it where you need
   - It's transparent so you can see your meeting in the background
   - Click and drag the "Meeting Agent" title bar to move it

3. **Add Reference PDFs** (optional)
   - Place PDF files in the `data/` folder
   - The agent will index them and use them for context

4. **Ask Questions** - Questions are automatically detected from the meeting audio
   - The agent will provide answers based on meeting context and PDFs

5. **End the Meeting**
   - Click the ✕ button to close the overlay
   - A comprehensive summary will be generated and saved

### Summary Output

Meeting summaries are saved to `meeting_summaries/` with:
- **Main Topics** - What was discussed
- **Key Decisions** - What was decided
- **Action Items** - Who needs to do what
- **Open Questions** - Unresolved issues

## Audio Device Configuration

### Finding Your Devices

Run this to see all available devices:
```powershell
.venv\Scripts\python.exe -c "import sounddevice as sd; devices = sd.query_devices(); print(devices)"
```

Look for:
- **Meeting Audio**: "Stereo Mix" (captures system audio), "Loopback", or "Virtual Cable"
- **Microphone**: Your actual microphone device

### Common Setups

**Windows with Stereo Mix:**
```python
MEETING_DEVICE_INDEX = 24   # Stereo Mix
MIC_DEVICE_INDEX = 2        # Your microphone
```

**With Virtual Audio Cable:**
```python
MEETING_DEVICE_INDEX = 3    # Virtual Cable
MIC_DEVICE_INDEX = 1        # Microphone
```

## Troubleshooting 🔧

### "GEMINI_API_KEY NOT CONFIGURED"
- Check your `.env` file has the API key
- Get a free key from: https://aistudio.google.com/app/apikey
- Restart the application after updating `.env`

### No Audio Being Captured
- Run the device query command above
- Update `MEETING_DEVICE_INDEX` and `MIC_DEVICE_INDEX` in `main.py`
- Check your audio device is working (test in audio settings)

### "Tesseract not found"
- Install: https://github.com/UB-Mannheim/tesseract/wiki
- Or update `TESSERACT_PATH` in `.env` if installed elsewhere

### Gemini API Rate Limiting
- Free tier has rate limits (~15 requests per minute)
- For production use, consider upgrading to paid tier
- Check usage: https://aistudio.google.com/app/apikey

### Audio Quality Issues
- Check your microphone and meeting audio device are enabled
- Try different `SAMPLE_RATE` values in `config.py` (default: 16000)

## Keyboard Shortcuts

- **Drag to Move**: Click and drag the "Meeting Agent" title
- **✕ Button**: Close the overlay and generate summary
- **Ctrl+C**: Force quit the application (in terminal)

## Advanced Configuration

Edit `app/config.py` to customize:

```python
SAMPLE_RATE = 16000         # Audio sample rate
CHANNELS = 1                # Mono audio
CHUNK_DURATION_SECONDS = 8  # Chunk size for transcription
GEMINI_MODEL = "gemini-1.5-flash"  # Fast model for real-time use
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `google-generativeai` | Gemini API access (text, vision, audio) |
| `pyqt6` | Modern overlay UI |
| `sounddevice` | Audio capture |
| `mss` | Screen capture |
| `pytesseract` | OCR text extraction |
| `pygetwindow` | Active window detection |
| `PyPDF2` | PDF parsing |
| `faiss-cpu` | Vector search for PDFs |
| `numpy` | Audio processing |
| `pillow` | Image processing |

## Tips & Best Practices 💡

1. **Position the Overlay** - Place it where you can see it without blocking important content
2. **Use Reference PDFs** - Add relevant documents to `data/` for better answers
3. **Monitor Logs** - Check `logs/meeting_agent.log` for detailed debug info
4. **Save Summaries** - Meeting summaries are automatically saved for future reference
5. **Device Testing** - Test your audio devices before important meetings
6. **Free Tier Usage** - The free Gemini API is great for testing; upgrade for production

## License

MIT License - Feel free to use and modify

## Support

For issues or questions:
1. Check the logs: `logs/meeting_agent.log`
2. Verify API key is valid at: https://aistudio.google.com/app/apikey
3. Test audio devices separately
4. Check that all dependencies are installed

---

**Made with ❤️ for better meetings - Now powered by Google Gemini**

# Meeting Agent - Setup Guide

## Prerequisites

- Python 3.8+
- OpenAI API key
- Tesseract OCR (for text extraction from screen)

## Step 1: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Sign in with your OpenAI account (create one if needed)
3. Click **"Create new secret key"**
4. Copy the key (it will start with `sk-`)
5. ⚠️ Save it securely - you won't be able to see it again

## Step 2: Configure .env File

1. Open `.env` file in the project root
2. Replace the placeholder:
   ```
   OPENAI_API_KEY=sk-proj-your-api-key-here
   ```
   With your actual key:
   ```
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
   ```
3. Save the file

## Step 3: Install Tesseract (Optional but Recommended)

For screen text extraction (OCR):

### Windows
1. Download installer: [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (default location: `C:\Program Files\Tesseract-OCR`)
3. Verify installation:
   ```powershell
   tesseract --version
   ```

## Step 4: Set Up Virtual Environment

```powershell
cd %USERPROFILE%\Documents\meeting-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Step 5: Configure Audio Devices

Check available audio devices:

```powershell
.venv\Scripts\python.exe -c "import sounddevice as sd; print(sd.query_devices())"
```

Update `app/main.py` with correct device indices:

```python
MEETING_DEVICE_INDEX = 9   # Your meeting audio device
MIC_DEVICE_INDEX = 2       # Your microphone
```

## Step 6: Run the Agent

```powershell
.venv\Scripts\python.exe -m app.main
```

You should see:
- ✅ A dark overlay window with "Meeting Agent" title
- ✅ Logs in terminal showing `[MEETING]` and `[MIC]` audio capture
- ✅ Screen capture and OCR processing

## Troubleshooting

### "OPENAI_API_KEY not configured!"
- Verify `.env` file has your actual API key (not placeholder)
- Key should start with `sk-`
- Restart the application after updating

### No audio being captured
- Run device query to find correct indices
- Update `MEETING_DEVICE_INDEX` and `MIC_DEVICE_INDEX` in `app/main.py`

### "Tesseract not found"
- Install Tesseract-OCR from the link above
- Or update `TESSERACT_PATH` in `.env` if installed elsewhere

### FFmpeg warning
- Non-critical warning for audio export
- Install ffmpeg if you need to export audio: `pip install ffmpeg-python`

## Features

- 🎤 Real-time audio transcription from meetings and microphone
- 🖥️ Screen capture and OCR text extraction
- 📊 Question detection from meeting transcript
- 📄 PDF document indexing and search
- 🤖 AI-powered context management and summaries
- 💾 Automatic meeting summary generation

## Next Steps

1. Place reference PDFs in the `data/` folder
2. Run a test meeting to verify everything works
3. Adjust audio device indices if needed
4. Close the overlay window to generate meeting summary

---

**Need help?** Check the logs in `logs/meeting_agent.log` for detailed error messages.

# Technical Specifications: Meeting AI Assistants
## Comprehensive Research & Implementation Guide

**Last Updated:** December 11, 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Screen Hiding & Interface Management](#screen-hiding--interface-management)
3. [Real-Time Answer Generation](#real-time-answer-generation)
4. [Context Window Management](#context-window-management)
5. [Common Tech Stacks](#common-tech-stacks)
6. [Open-Source Alternatives](#open-source-alternatives)
7. [Implementation Patterns](#implementation-patterns)
8. [Code Examples](#code-examples)

---

## Executive Summary

Meeting AI assistants like Cluely AI and Parquet.AI operate through specialized architectures combining:
- **Real-time audio transcription** with sub-second latency
- **Screen share detection prevention** using overlay techniques
- **WebSocket streaming** for instant data delivery
- **Vector databases** for context retrieval
- **Multi-service microservices** architecture

This document provides detailed technical specifications, implementation patterns, and open-source alternatives for building meeting AI assistants.

---

## Screen Hiding & Interface Management

### How Meeting AIs Hide Interface from Screen Share

#### 1. **Browser Extension-Based Approach**

**Technology Stack:**
- Chrome Extensions API (`chrome.tabs`, `chrome.windows`)
- Content Scripts for DOM manipulation
- Service Worker architecture (Manifest V3)
- CSS `visibility: hidden` / `display: none` tricks
- Window layering (z-index manipulation)

**Implementation Pattern:**

```javascript
// manifest.json (Chrome Extension V3)
{
  "manifest_version": 3,
  "name": "Meeting AI Assistant",
  "permissions": [
    "tabs",
    "webNavigation",
    "activeTab",
    "scripting"
  ],
  "host_permissions": [
    "https://meet.google.com/*",
    "https://teams.microsoft.com/*",
    "https://zoom.us/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["https://meet.google.com/*"],
      "js": ["content.js"],
      "run_at": "document_start"
    }
  ]
}
```

#### 2. **Screen Share Detection Methods**

**a) Display Media API Detection:**
```javascript
// Detect when user starts screen sharing
navigator.mediaDevices.getDisplayMedia().then(stream => {
  const screenTrack = stream.getVideoTracks()[0];
  
  // Monitor screen share state
  screenTrack.onended = () => {
    console.log("Screen share ended");
  };
  
  // Auto-hide overlay when screen share detected
  document.getElementById('meeting-ai-overlay').style.visibility = 'hidden';
});
```

**b) Canvas/WebGL Rendering Approach:**
- Render UI to off-screen canvas
- Use `requestAnimationFrame` for updates
- Never render to visible DOM during share
- Detect via `getDisplayMedia()` state change

**c) Native Implementation (Desktop Apps):**
- Use platform APIs to detect active screen share
- Windows: Windows.Graphics.Capture
- macOS: AVCaptureSession monitoring
- Linux: X11/Wayland window detection

#### 3. **Overlay Window Management**

**Desktop Application Approach (Python + Tkinter/Qt):**

```python
import tkinter as tk
from tkinter import Frame, Label, Button
import win32gui
import win32con

class MeetingAIOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-topmost', True)  # Always on top
        self.root.attributes('-alpha', 0.95)     # Transparency
        
        # Make window click-through (Windows)
        self.set_click_through()
        
    def set_click_through(self):
        """Make window transparent to clicks"""
        hwnd = win32gui.FindWindow(None, self.root.title())
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        style |= win32con.WS_EX_LAYERED
        style |= win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        
    def auto_hide_on_stream(self):
        """Hide when screen share detected"""
        self.root.withdraw()  # Hide
        # Re-show after share ends (via polling or events)
```

#### 4. **Browser-Based Overlay Without Extension**

**Technique: Floating DIV with Fixed Positioning**

```css
/* CSS for always-visible overlay */
#meeting-ai-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 400px;
  height: 300px;
  z-index: 999999;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #e0e0e0;
  
  /* Prevent from being captured by screen share */
  -webkit-user-select: none;
  user-select: none;
  pointer-events: auto;
}

/* Hide when CSS media query detects screen share */
@media (prefers-contrast: more) {
  #meeting-ai-container {
    visibility: hidden;
  }
}
```

**JavaScript: Detect Screen Share & Auto-Hide**

```javascript
class ScreenShareDetector {
  constructor() {
    this.isScreenSharing = false;
    this.monitorScreenShare();
  }
  
  async monitorScreenShare() {
    // Method 1: Monitor getDisplayMedia
    const originalGetDisplayMedia = navigator.mediaDevices.getDisplayMedia;
    navigator.mediaDevices.getDisplayMedia = async (constraints) => {
      const stream = await originalGetDisplayMedia.call(navigator.mediaDevices, constraints);
      this.isScreenSharing = true;
      this.hideOverlay();
      
      stream.getVideoTracks()[0].onended = () => {
        this.isScreenSharing = false;
        this.showOverlay();
      };
      
      return stream;
    };
    
    // Method 2: Poll video permission state (Chrome 113+)
    const permissions = await navigator.permissions.query({
      name: 'camera'
    });
    
    permissions.addEventListener('change', () => {
      if (permissions.state === 'denied') {
        this.hideOverlay();
      }
    });
  }
  
  hideOverlay() {
    document.getElementById('meeting-ai-container').style.visibility = 'hidden';
  }
  
  showOverlay() {
    document.getElementById('meeting-ai-container').style.visibility = 'visible';
  }
}
```

#### 5. **Database Architecture for Meeting State**

**Real-time State Tracking:**

```sql
-- PostgreSQL schema for meeting state
CREATE TABLE meeting_sessions (
    id UUID PRIMARY KEY,
    platform VARCHAR(50),  -- 'google_meet', 'teams', 'zoom'
    meeting_code VARCHAR(100),
    user_id UUID REFERENCES users(id),
    is_screen_sharing BOOLEAN DEFAULT FALSE,
    ui_visibility_state VARCHAR(50),  -- 'visible', 'hidden', 'minimized'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE ui_events (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES meeting_sessions(id),
    event_type VARCHAR(50),  -- 'screen_share_start', 'screen_share_end'
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Index for fast queries
CREATE INDEX idx_sessions_user_platform ON meeting_sessions(user_id, platform);
```

---

## Real-Time Answer Generation

### Architecture Overview

Meeting AI assistants use a **streaming pipeline** architecture:

```
Audio Input → Transcription (WhisperX/Groq) 
           → Question Detection (QA Model)
           → Context Retrieval (Vector DB)
           → LLM Streaming (Groq/OpenAI)
           → WebSocket Output → UI
```

### 1. **Real-Time Transcription Services**

#### WhisperX (Open Source)
```python
import whisperx
import asyncio

class RealtimeTranscriber:
    def __init__(self, device="cuda"):
        self.device = device
        self.model = whisperx.load_model("large-v2", device=device, compute_type="float16")
        
    async def transcribe_audio_stream(self, audio_chunks):
        """Process audio chunks in real-time with 70x speedup"""
        segments = []
        
        for chunk in audio_chunks:
            # Batch inference for 70x realtime speed
            result = self.model.transcribe(chunk, batch_size=16)
            
            # Align with wav2vec2 for accurate word timing
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"], 
                device=self.device
            )
            result = whisperx.align(
                result["segments"], 
                model_a, 
                metadata, 
                chunk, 
                self.device
            )
            
            # Speaker diarization
            diarize_model = whisperx.DiarizationPipeline(device=self.device)
            diarize_segments = diarize_model(chunk)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            
            segments.extend(result["segments"])
            yield result  # Stream results as they arrive
```

#### Groq API (Fast Inference)
```python
import groq

class GroqLiveTranscriber:
    def __init__(self, api_key):
        self.client = groq.Groq(api_key=api_key)
    
    async def stream_transcription(self, audio_file_path):
        """Sub-second transcription with Groq LPU"""
        with open(audio_file_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",  # Groq-optimized
                response_format="verbose_json",  # Get word-level timestamps
                language="en"
            )
            return transcript
```

### 2. **Question Detection**

**Pattern 1: Keyword-Based Detection**

```python
import re
from typing import Tuple

class QuestionDetector:
    QUESTION_PATTERNS = [
        r'\b(what|when|where|who|why|how|can|could|would|should)\b',
        r'[?!]\s*$',  # Ends with ? or !
        r'\b(do you|does|did|is|are|am)\b.*\?'  # Interrogative structure
    ]
    
    def detect_question(self, text: str) -> Tuple[bool, str]:
        """Detect if text is a question"""
        text_lower = text.lower().strip()
        
        # Confidence scoring
        confidence = 0
        
        # Pattern matching
        for pattern in self.QUESTION_PATTERNS:
            if re.search(pattern, text_lower):
                confidence += 0.3
        
        # Punctuation analysis
        if text_lower.endswith('?'):
            confidence += 0.7
        
        # Return result and confidence
        return confidence > 0.5, text
    
    def extract_question_context(self, transcript_segments, question_idx):
        """Extract context around question"""
        context_window = 3  # Previous 3 segments
        context = ' '.join([
            segment['text'] 
            for segment in transcript_segments[max(0, question_idx-context_window):question_idx+1]
        ])
        return context
```

**Pattern 2: ML-Based Detection (HuggingFace)**

```python
from transformers import pipeline

class MLQuestionDetector:
    def __init__(self):
        self.question_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
    
    def detect_question(self, text: str) -> bool:
        """Use ML to detect questions vs statements"""
        result = self.question_classifier(
            text,
            ["question", "statement"],
            multi_label=False
        )
        return result["labels"][0] == "question" and result["scores"][0] > 0.7
```

### 3. **Streaming Answer Generation**

**Implementation with Groq (Ultra-Fast Inference)**

```python
import groq
from typing import AsyncGenerator

class StreamingAnswerGenerator:
    def __init__(self, api_key: str):
        self.client = groq.Groq(api_key=api_key)
        
    async def generate_answer_stream(
        self, 
        question: str, 
        context: str,
        conversation_history: list
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response token-by-token"""
        
        system_prompt = """You are a helpful meeting assistant. 
        Provide concise, direct answers based on the meeting context.
        Keep responses under 2-3 sentences."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {
                "role": "user",
                "content": f"""Meeting Context: {context}
                
Question: {question}

Provide a brief, specific answer based on the context."""
            }
        ]
        
        # Stream with Groq (70x faster than standard LLMs)
        with self.client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.3,  # Low temperature for factual answers
            max_tokens=150,
            stream=True  # Enable streaming
        ) as response:
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    await asyncio.sleep(0.01)  # Yield to event loop
```

### 4. **WebSocket Streaming to Frontend**

**Server-Side (FastAPI)**

```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import asyncio
import json

app = FastAPI()
transcriber = RealtimeTranscriber()
answer_gen = StreamingAnswerGenerator(api_key="your_api_key")

@app.websocket("/ws/meeting/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    await websocket.accept()
    
    try:
        while True:
            # Receive audio chunk from client
            data = await websocket.receive_bytes()
            
            # Step 1: Transcribe
            async for transcription in transcriber.transcribe_audio_stream([data]):
                await websocket.send_json({
                    "type": "transcription",
                    "text": transcription.get("text", ""),
                    "timestamp": transcription.get("start")
                })
                
                # Step 2: Detect question
                is_question, _ = question_detector.detect_question(transcription["text"])
                
                if is_question:
                    # Step 3: Generate answer stream
                    full_answer = ""
                    async for token in answer_gen.generate_answer_stream(
                        question=transcription["text"],
                        context="...",
                        conversation_history=[]
                    ):
                        full_answer += token
                        
                        # Send token as it arrives
                        await websocket.send_json({
                            "type": "answer_token",
                            "token": token,
                            "full_answer": full_answer
                        })
                        
                        # Keep connection alive
                        await asyncio.sleep(0.01)
                        
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

**Client-Side (JavaScript)**

```javascript
class MeetingAIClient {
  constructor(meetingId) {
    this.meetingId = meetingId;
    this.ws = new WebSocket(`ws://localhost:8000/ws/meeting/${meetingId}`);
    this.ws.binaryType = "arraybuffer";
    
    this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
  }
  
  handleMessage(message) {
    switch (message.type) {
      case "transcription":
        this.displayTranscription(message.text, message.timestamp);
        break;
      case "answer_token":
        this.appendAnswerToken(message.token);
        break;
    }
  }
  
  async sendAudioChunk(audioData) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(audioData);
    }
  }
  
  displayTranscription(text, timestamp) {
    const transcriptDiv = document.getElementById('transcription');
    transcriptDiv.innerHTML += `<p><strong>${new Date(timestamp*1000).toLocaleTimeString()}:</strong> ${text}</p>`;
  }
  
  appendAnswerToken(token) {
    const answerDiv = document.getElementById('answer');
    answerDiv.innerHTML += token;
  }
}

// Usage
const client = new MeetingAIClient("meeting-123");

// Capture audio from meeting
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const processor = new AudioWorkletProcessor();
    stream.getTracks()[0].onended = () => processor.stop();
    processor.ondata = chunk => client.sendAudioChunk(chunk);
  });
```

---

## Context Window Management

### 1. **Sliding Window Context Approach**

```python
from collections import deque
from datetime import datetime, timedelta

class MeetingContextManager:
    def __init__(self, max_tokens=4096, retention_minutes=30):
        self.max_tokens = max_tokens
        self.retention_minutes = retention_minutes
        self.segments = deque(maxlen=500)  # Keep 500 segments max
        self.vector_db = None  # Will connect to Pinecone/Weaviate
        
    def add_segment(self, speaker: str, text: str, timestamp: float):
        """Add transcription segment"""
        self.segments.append({
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp,
            "embedding": self.embed_text(text)  # Store vector
        })
        
        # Cleanup old segments
        self.cleanup_old_segments()
        
    def get_context_window(self, query: str, window_tokens: int = 2000) -> str:
        """Retrieve relevant context using vector similarity"""
        
        # 1. Vector search for relevant segments
        query_embedding = self.embed_text(query)
        relevant_segments = self.vector_search(query_embedding, top_k=5)
        
        # 2. Add chronological context around relevant segments
        context_segments = []
        for segment in relevant_segments:
            # Get segments within 1 minute of each relevant segment
            idx = list(self.segments).index(segment)
            window_start = max(0, idx - 3)
            window_end = min(len(self.segments), idx + 3)
            context_segments.extend(list(self.segments)[window_start:window_end])
        
        # 3. Deduplicate and order chronologically
        unique_segments = {}
        for seg in context_segments:
            timestamp = seg["timestamp"]
            if timestamp not in unique_segments:
                unique_segments[timestamp] = seg
        
        # 4. Format as context string
        context = self.format_context(unique_segments.values())
        
        # 5. Truncate if exceeds token limit
        if self.estimate_tokens(context) > window_tokens:
            context = self.truncate_context(context, window_tokens)
        
        return context
    
    def vector_search(self, embedding: list, top_k: int = 5):
        """Search vector database for similar segments"""
        # Using Pinecone or Weaviate
        results = self.vector_db.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        return results
    
    def cleanup_old_segments(self):
        """Remove segments older than retention period"""
        cutoff_time = datetime.now() - timedelta(minutes=self.retention_minutes)
        
        while self.segments and self.segments[0]["timestamp"] < cutoff_time.timestamp():
            self.segments.popleft()
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token count (1 token ≈ 4 chars)"""
        return len(text) // 4
    
    def embed_text(self, text: str) -> list:
        """Get embedding using OpenAI or Sentence-Transformers"""
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model.encode(text).tolist()
```

### 2. **Vector Database Integration (Pinecone)**

```python
import pinecone
import time

class VectorContextDB:
    def __init__(self, api_key: str, environment: str):
        pinecone.init(api_key=api_key, environment=environment)
        
        # Create index if not exists
        index_name = "meeting-context"
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=384,  # Sentence-Transformers dimension
                metric="cosine"
            )
        
        self.index = pinecone.Index(index_name)
    
    def upsert_segment(self, segment_id: str, embedding: list, text: str, metadata: dict):
        """Store embedding and metadata"""
        self.index.upsert(
            vectors=[
                (
                    segment_id,
                    embedding,
                    {
                        "text": text,
                        **metadata,
                        "timestamp": time.time()
                    }
                )
            ]
        )
    
    def query_similar(self, embedding: list, top_k: int = 5, meeting_id: str = None):
        """Query for similar segments with optional filtering"""
        filter_dict = {"meeting_id": {"$eq": meeting_id}} if meeting_id else None
        
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        return [
            {
                "text": match["metadata"]["text"],
                "score": match["score"],
                "timestamp": match["metadata"]["timestamp"]
            }
            for match in results["matches"]
        ]
```

### 3. **Weaviate Alternative (Self-Hosted)**

```python
import weaviate
from weaviate.classes.query import MetadataQuery

class WeaviateContextDB:
    def __init__(self, url: str = "http://localhost:8080"):
        self.client = weaviate.connect_to_local(
            host=url.split("://")[1].split(":")[0],
            port=int(url.split(":")[-1])
        )
        
    def create_schema(self):
        """Create meeting context schema"""
        self.client.collections.create(
            name="MeetingSegment",
            vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_transformers(),
            properties=[
                weaviate.classes.config.Property(
                    name="text",
                    data_type=weaviate.classes.config.DataType.TEXT
                ),
                weaviate.classes.config.Property(
                    name="speaker",
                    data_type=weaviate.classes.config.DataType.TEXT
                ),
                weaviate.classes.config.Property(
                    name="timestamp",
                    data_type=weaviate.classes.config.DataType.NUMBER
                ),
                weaviate.classes.config.Property(
                    name="meeting_id",
                    data_type=weaviate.classes.config.DataType.TEXT
                ),
            ]
        )
    
    def upsert_segment(self, segment: dict):
        """Add segment to Weaviate"""
        collection = self.client.collections.get("MeetingSegment")
        collection.data.create(properties=segment)
    
    def hybrid_search(self, query: str, meeting_id: str, top_k: int = 5):
        """Hybrid search (semantic + keyword)"""
        collection = self.client.collections.get("MeetingSegment")
        
        response = collection.query.hybrid(
            query=query,
            alpha=0.75,  # 75% semantic, 25% keyword
            where=weaviate.classes.query.Filter.by_property("meeting_id").equal(meeting_id),
            limit=top_k
        )
        
        return [
            {
                "text": obj.properties["text"],
                "speaker": obj.properties["speaker"],
                "timestamp": obj.properties["timestamp"]
            }
            for obj in response.objects
        ]
```

---

## Common Tech Stacks

### Complete Meeting AI Stack Comparison

| Component | Commercial | Open Source | Notes |
|-----------|-----------|-----------|-------|
| **Transcription** | Groq API, OpenAI API | WhisperX, Whisper | Groq: 70x speedup with LPU |
| **Audio Capture** | - | PyAudio, pydub | Python: sounddevice |
| **Screen Sharing Platform** | Zoom API, Teams Bot API, Google Meet API | Vexa (self-hosted) | Bot-based or extension-based |
| **LLM Inference** | Groq, OpenAI, Anthropic | Ollama, LiteLLM | Groq dominates for speed |
| **Vector DB** | Pinecone | Weaviate, Milvus, ChromaDB | Context retrieval for RAG |
| **Real-time Transport** | WebSocket (both) | Socket.io, gRPC | WebSocket standard |
| **Browser Extension** | Custom | Chrome/Firefox native | Content scripts + service worker |
| **Desktop App** | Custom | Electron, Tauri | Cross-platform |

### Recommended Production Stack

```
Frontend: React/Vue.js with TypeScript
├── WebSocket client (native)
├── Audio capture (Web Audio API)
└── Overlay UI (fixed positioning)

Backend: Python/Node.js
├── API Gateway (FastAPI/Express)
├── WebSocket server (Socket.io or native)
├── Audio processing (WhisperX)
├── LLM inference (Groq API)
└── Vector database (Pinecone/Weaviate)

Data Layer:
├── PostgreSQL (metadata, users, sessions)
├── Vector DB (Pinecone/Weaviate)
└── Redis (caching, real-time state)

Infrastructure:
├── Docker containers
├── Kubernetes orchestration
├── Load balancing (nginx)
└── CDN for static assets
```

---

## Open-Source Alternatives

### 1. **Vexa.ai** (Most Complete)
**GitHub:** `Vexa-ai/vexa`

**Features:**
- Real-time bot for Google Meet & Teams
- WebSocket streaming transcripts
- Self-hostable (Docker)
- Multi-language transcription

**Architecture:**
```
Python 58.9% | TypeScript 18.7% | JavaScript 6.3%

Services:
- api-gateway: REST/WebSocket routing
- bot-manager: Lifecycle management
- vexa-bot: Joins meetings, captures audio
- WhisperLive: Real-time transcription service
- transcription-collector: Processing & storage
```

**Deployment:**
```bash
git clone https://github.com/Vexa-ai/vexa.git
cd vexa

# CPU deployment
make all

# GPU deployment
make all TARGET=gpu

# Hosted: https://vexa.ai
```

### 2. **H3xAssist**
**GitHub:** `ih3xcode/h3xassist` & `Userdev1905/h3xassist`

**Features:**
- Python backend + Next.js frontend
- Zoom, Teams, Google Meet support
- FastAPI for real-time APIs
- Playwright for browser automation

**Tech Stack:**
- Backend: Python + FastAPI + Playwright
- Frontend: Next.js + TypeScript
- Transcription: WhisperX
- Speaker Diarization: Pyannote

### 3. **Nojoin** (Self-Hosted, Privacy-Focused)
**GitHub:** `Valtora/Nojoin`

**Features:**
- Local GPU-accelerated transcription (Whisper)
- Speaker diarization (Pyannote)
- Rust companion app
- No cloud dependencies

**Technologies:**
- Rust + TypeScript
- GPU: CUDA/cuDNN
- Audio: Local processing

### 4. **TreeHacks-ZoneOut** (Hackathon Winner)
**GitHub:** `NxtGenLegend/TreeHacks-ZoneOut`

**Features:**
- Multimodal RAG (video + audio + text)
- Zoom API integration
- WebSocket real-time updates
- VLM for visual context

**Tech Stack:**
- JavaScript/Node.js
- WebSocket for real-time
- Zoom SDK
- Vision models (GPT-4V)

### 5. **Joinly** (AI Agent Framework)
**GitHub:** `joinly-ai/joinly`

**Features:**
- MCP (Model Context Protocol) server
- Meeting-aware AI agents
- Transcription + analysis
- Multi-LLM support

---

## Implementation Patterns

### Pattern 1: Polling Architecture (Simplest)

```python
import asyncio
import time

class PollingMeetingAI:
    """Simple polling approach - least responsive"""
    
    async def monitor_meeting(self, meeting_id: str, interval: int = 2):
        while True:
            # Poll every 2 seconds
            transcript = await self.get_meeting_transcript(meeting_id)
            
            # Check for new questions
            new_segments = self.extract_new_segments(transcript)
            
            for segment in new_segments:
                if self.is_question(segment):
                    answer = await self.generate_answer(segment)
                    await self.send_to_ui(answer)
            
            await asyncio.sleep(interval)
```

**Pros:** Simple, no dependencies  
**Cons:** High latency, server load, battery drain

---

### Pattern 2: WebSocket Streaming (Recommended)

```python
# See WebSocket section above
# Sub-second latency, bidirectional communication
```

**Pros:** Real-time, efficient, scalable  
**Cons:** Requires WebSocket support

---

### Pattern 3: Message Queue (Scalable)

```python
import aio_pika

class QueuedMeetingAI:
    """Message queue for handling spikes"""
    
    async def start(self):
        connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
        channel = await connection.channel()
        
        # Create queues
        transcript_queue = await channel.declare_queue('transcripts')
        answer_queue = await channel.declare_queue('answers')
        
        # Consumer
        async with transcript_queue.iterator() as iter:
            async for message in iter:
                async with message.process():
                    segment = json.loads(message.body)
                    
                    if self.is_question(segment):
                        answer = await self.generate_answer(segment)
                        
                        await answer_queue.channel.basic_publish(
                            aio_pika.Message(body=json.dumps(answer)),
                            routing_key='answers'
                        )
```

**Pros:** Handles traffic spikes, decoupled services  
**Cons:** Higher complexity, additional infrastructure

---

## Code Examples

### Complete End-to-End Example

**1. Audio Capture (Browser)**

```javascript
class AudioCaptureManager {
  constructor(meetingId, websocketUrl) {
    this.meetingId = meetingId;
    this.ws = new WebSocket(websocketUrl);
    this.audioContext = null;
    this.mediaStream = null;
  }
  
  async startCapture() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: false  // Preserve volume levels
        }
      });
      
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      source.connect(processor);
      processor.connect(this.audioContext.destination);
      
      processor.onaudioprocess = (e) => {
        const audioData = e.inputBuffer.getChannelData(0);
        this.ws.send(audioData);
      };
    } catch (error) {
      console.error("Audio capture failed:", error);
    }
  }
  
  stopCapture() {
    this.mediaStream.getTracks().forEach(track => track.stop());
    this.audioContext.close();
  }
}
```

**2. Backend Processing (Python)**

```python
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
import whisperx
import asyncio

app = FastAPI()

# Initialize models once
transcriber = None
answer_gen = None
context_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global transcriber, answer_gen, context_manager
    transcriber = whisperx.load_model("large-v2", device="cuda")
    answer_gen = StreamingAnswerGenerator(api_key="gsk_...")
    context_manager = MeetingContextManager(max_tokens=4096)
    yield
    # Shutdown
    del transcriber, answer_gen

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws/meeting/{meeting_id}")
async def websocket_handler(websocket: WebSocket, meeting_id: str):
    await websocket.accept()
    
    audio_buffer = bytearray()
    
    try:
        while True:
            # Receive audio chunk
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            
            # Process when buffer reaches 1 second of audio
            if len(audio_buffer) >= 32000:  # ~1 second at 16kHz
                audio_chunk = bytes(audio_buffer)
                audio_buffer.clear()
                
                # Transcribe
                result = transcriber.transcribe(audio_chunk)
                
                for segment in result.get("segments", []):
                    text = segment["text"]
                    speaker = segment.get("speaker", "Unknown")
                    
                    # Send transcription
                    await websocket.send_json({
                        "type": "transcription",
                        "speaker": speaker,
                        "text": text,
                        "timestamp": segment["start"]
                    })
                    
                    # Add to context
                    context_manager.add_segment(speaker, text, segment["start"])
                    
                    # Check if question
                    if question_detector.detect_question(text)[0]:
                        # Get context
                        context = context_manager.get_context_window(text)
                        
                        # Generate streaming answer
                        async for token in answer_gen.generate_answer_stream(
                            question=text,
                            context=context,
                            conversation_history=[]
                        ):
                            await websocket.send_json({
                                "type": "answer",
                                "token": token
                            })
                            await asyncio.sleep(0.01)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()
```

**3. UI Rendering (React)**

```javascript
import React, { useEffect, useState, useRef } from 'react';

function MeetingAIOverlay({ meetingId }) {
  const [transcription, setTranscription] = useState([]);
  const [answer, setAnswer] = useState('');
  const wsRef = useRef(null);
  const overlayRef = useRef(null);
  
  useEffect(() => {
    // Connect WebSocket
    wsRef.current = new WebSocket(`ws://localhost:8000/ws/meeting/${meetingId}`);
    
    wsRef.current.onmessage = async (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'transcription') {
        setTranscription(prev => [...prev, {
          speaker: message.speaker,
          text: message.text,
          timestamp: new Date(message.timestamp * 1000)
        }]);
      } else if (message.type === 'answer') {
        setAnswer(prev => prev + message.token);
      }
    };
    
    return () => wsRef.current?.close();
  }, [meetingId]);
  
  // Auto-hide on screen share
  useEffect(() => {
    const handleScreenShare = async () => {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia();
        overlayRef.current.style.visibility = 'hidden';
        stream.getTracks()[0].onended = () => {
          overlayRef.current.style.visibility = 'visible';
        };
      } catch (e) {
        // Screen share was cancelled
      }
    };
    
    window.addEventListener('keydown', (e) => {
      if (e.key === 's' && e.ctrlKey) handleScreenShare();
    });
  }, []);
  
  return (
    <div 
      ref={overlayRef}
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        width: 400,
        maxHeight: 500,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: 8,
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        overflow: 'auto',
        zIndex: 999999,
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
    >
      {/* Transcription */}
      <div style={{ padding: 16, borderBottom: '1px solid #e0e0e0' }}>
        <h3 style={{ margin: '0 0 10px 0', fontSize: 14 }}>Meeting Transcript</h3>
        <div style={{ fontSize: 12, maxHeight: 150, overflow: 'auto' }}>
          {transcription.map((item, i) => (
            <p key={i} style={{ margin: '4px 0' }}>
              <strong>{item.speaker}:</strong> {item.text}
            </p>
          ))}
        </div>
      </div>
      
      {/* Answer */}
      {answer && (
        <div style={{ padding: 16, backgroundColor: '#f5f5f5' }}>
          <h3 style={{ margin: '0 0 10px 0', fontSize: 14 }}>AI Response</h3>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.4 }}>{answer}</p>
        </div>
      )}
    </div>
  );
}

export default MeetingAIOverlay;
```

---

## Performance Benchmarks

| Operation | Technology | Latency | Notes |
|-----------|-----------|---------|-------|
| **Audio Capture to Transcription** | WhisperX + CUDA | 1-2s | Batched, 70x speedup |
| **Transcription to WebSocket** | Native WebSocket | <10ms | Network dependent |
| **Question Detection** | ML (BART) | 100-200ms | Lightweight model |
| **Context Retrieval** | Pinecone | 50-100ms | Vector search |
| **LLM Answer Generation** | Groq | 200-500ms | Token streaming |
| **Total End-to-End** | All combined | 1.5-3s | Sub-second possible with optimizations |

---

## Security Considerations

### 1. **Screen Share Detection Privacy**

```python
# Validate screen share state server-side
class ScreenShareValidator:
    async def validate_ui_visibility(self, session_id: str) -> bool:
        """Verify UI is hidden during screen share"""
        session = await get_session(session_id)
        return session["ui_visibility_state"] == "hidden"
```

### 2. **Audio Encryption**

```python
# TLS 1.3 for WebSocket (WSS)
# AES-256 for stored audio segments
from cryptography.fernet import Fernet

class AudioEncryption:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt_segment(self, audio_bytes):
        return self.cipher.encrypt(audio_bytes)
    
    def decrypt_segment(self, encrypted_bytes):
        return self.cipher.decrypt(encrypted_bytes)
```

### 3. **API Key Management**

```python
# Use environment variables, not hardcoded
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
```

---

## Deployment Checklist

- [ ] Audio capture with noise cancellation enabled
- [ ] Real-time transcription with <2s latency
- [ ] Question detection with >90% accuracy
- [ ] Context retrieval from vector database
- [ ] Streaming LLM responses with token buffering
- [ ] WebSocket connection with automatic reconnect
- [ ] Screen share auto-hide functionality
- [ ] Database schema for meeting sessions
- [ ] API authentication & rate limiting
- [ ] Monitoring & error logging
- [ ] GDPR-compliant data retention
- [ ] End-to-end encryption for audio

---

## References & Resources

### Key Projects
- **Vexa.ai:** https://github.com/Vexa-ai/vexa
- **WhisperX:** https://github.com/m-bain/whisperX
- **Groq API:** https://groq.com
- **Weaviate:** https://weaviate.io
- **Pinecone:** https://pinecone.io

### Documentation
- Chrome Extensions: https://developer.chrome.com/docs/extensions
- FastAPI WebSocket: https://fastapi.tiangolo.com/advanced/websockets
- Zoom/Teams/Meet APIs: Official developer platforms

---

**Document Version:** 1.0  
**Last Updated:** December 11, 2025  
**Author:** Technical Research Team

"""
Parakeet-Style Audio Processing
Transcript-driven, deterministic, speaker-gated system
"""
import logging
import threading
import queue
import time
import numpy as np
import sounddevice as sd
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class Speaker(Enum):
    """Speaker types with priority order"""
    INTERVIEWER = 3  # Highest priority
    USER = 2
    NOISE = 1


@dataclass
class TranscriptEvent:
    """Finalized transcript event - the ONLY thing the system reasons on"""
    speaker: Speaker
    text: str
    confidence: float
    timestamp: str
    
    def to_dict(self):
        return {
            "speaker": self.speaker.name,
            "text": self.text,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


class ParakeetAudioProcessor:
    """
    Parakeet-style audio processor
    
    CRITICAL INVARIANT: No transcript event → no reasoning → no answer
    
    Processing stages:
    1. Audio Frame (16 kHz mono, 20-30ms chunks)
    2. Voice Activity Detection (VAD)
    3. Speaker Attribution
    4. Overlap Resolution (INTERVIEWER > USER > NOISE)
    5. Sentence Finalization (buffer until speech ends)
    6. Transcript Event Emission
    """
    
    def __init__(self, device_index: int = 1):
        """
        Initialize Parakeet audio processor
        
        Args:
            device_index: Audio device (1 = Microphone Array)
        """
        self.device_index = device_index
        self.sample_rate = 16000  # 16 kHz mono (standard)
        self.frame_duration = 30  # 30 ms chunks
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        # Voice Activity Detection (Energy-based - simple but effective)
        self.vad_threshold = 500  # Energy threshold for speech detection
        
        # Speech buffer and state
        self.audio_buffer = []
        self.speech_frames = []
        self.silence_threshold = 200  # ms of silence to finalize
        self.silence_frames = 0
        self.min_speech_frames = 10  # Minimum frames for valid speech
        
        # Speaker state
        self.current_speaker = None
        self.speaker_confidence = 0.0
        
        # Threading
        self.running = False
        self.audio_queue = queue.Queue()
        self.capture_thread = None
        self.process_thread = None
        
        # Callbacks
        self.on_transcript_event: Optional[Callable[[TranscriptEvent], None]] = None
        
        logger.info(f"Parakeet audio initialized: 16kHz, {self.frame_duration}ms frames, Energy-based VAD")
    
    def start(self, on_transcript: Callable[[TranscriptEvent], None]):
        """
        Start audio processing pipeline
        
        Args:
            on_transcript: Callback for finalized transcript events
        """
        self.on_transcript_event = on_transcript
        self.running = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        logger.info("Parakeet audio pipeline started")
    
    def stop(self):
        """Stop audio processing"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1)
        if self.process_thread:
            self.process_thread.join(timeout=1)
        logger.info("Parakeet audio pipeline stopped")
    
    def _capture_loop(self):
        """Audio capture loop - 16 kHz mono, chunked"""
        try:
            with sd.InputStream(
                device=self.device_index,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.frame_size,
                dtype=np.int16
            ) as stream:
                logger.info(f"Audio stream opened: device={self.device_index}")
                
                while self.running:
                    # Read frame (30ms chunk)
                    frame, overflowed = stream.read(self.frame_size)
                    if overflowed:
                        logger.warning("Audio buffer overflow")
                    
                    # Convert to bytes for VAD
                    frame_bytes = frame.tobytes()
                    self.audio_queue.put(frame_bytes)
                    
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            self.running = False
    
    def _process_loop(self):
        """
        Processing loop - VAD → Speaker → Finalization → Transcript Event
        
        PARAKEET RULE: Only emit transcript when speech has ENDED
        """
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        while self.running:
            try:
                # Get audio frame (blocking with timeout)
                try:
                    frame_bytes = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Stage 1: Voice Activity Detection
                is_speech = self._detect_voice_activity(frame_bytes)
                
                if is_speech:
                    # Speech detected - add to buffer
                    self.speech_frames.append(frame_bytes)
                    self.silence_frames = 0
                    
                    # Stage 2: Speaker Attribution (simple heuristic for now)
                    # In production: use speaker diarization model
                    self._attribute_speaker(frame_bytes)
                    
                else:
                    # Silence detected
                    if len(self.speech_frames) > 0:
                        self.silence_frames += 1
                        
                        # Check if speech has ended (200ms silence)
                        silence_ms = self.silence_frames * self.frame_duration
                        if silence_ms >= self.silence_threshold:
                            # Stage 3: Finalize and emit transcript
                            self._finalize_speech(recognizer)
                
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def _detect_voice_activity(self, frame_bytes: bytes) -> bool:
        """
        Voice Activity Detection using energy-based method
        
        Simple but effective: measures RMS energy of audio frame
        Speech typically has higher energy than background noise
        
        Returns:
            True if speech detected, False if silence/noise
        """
        try:
            # Convert bytes to numpy array
            frame = np.frombuffer(frame_bytes, dtype=np.int16)
            
            # Calculate RMS energy
            rms_energy = np.sqrt(np.mean(frame**2))
            
            # Speech if energy above threshold
            is_speech = rms_energy > self.vad_threshold
            
            return is_speech
        except Exception as e:
            # logger.debug(f"VAD error: {e}")
            return False
    
    def _attribute_speaker(self, frame_bytes: bytes):
        """
        Speaker Attribution
        
        Simple heuristic for now:
        - High energy + low pitch = INTERVIEWER
        - Lower energy = USER
        
        In production: Use speaker diarization (pyannote.audio)
        """
        # Convert to numpy for energy calculation
        frame = np.frombuffer(frame_bytes, dtype=np.int16)
        energy = np.abs(frame).mean()
        
        # Simple threshold-based attribution
        # TODO: Replace with ML-based speaker diarization
        if energy > 1000:  # High energy
            self.current_speaker = Speaker.INTERVIEWER
            self.speaker_confidence = 0.85
        else:
            self.current_speaker = Speaker.USER
            self.speaker_confidence = 0.75
    
    def _finalize_speech(self, recognizer):
        """
        Stage 4: Finalize speech and emit transcript event
        
        CRITICAL: This is the ONLY place transcripts are created
        """
        if len(self.speech_frames) < self.min_speech_frames:
            # Too short - discard
            self.speech_frames = []
            self.silence_frames = 0
            return
        
        try:
            # Combine frames into audio data
            audio_data = b''.join(self.speech_frames)
            
            # Convert to AudioData for speech recognition
            import speech_recognition as sr
            audio = sr.AudioData(audio_data, self.sample_rate, 2)
            
            # Transcribe
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                
                if text and len(text.strip()) > 0:
                    # Get timestamp
                    timestamp = time.strftime("%H:%M:%S", time.localtime())
                    
                    # Create transcript event
                    event = TranscriptEvent(
                        speaker=self.current_speaker,
                        text=text.strip(),
                        confidence=self.speaker_confidence,
                        timestamp=timestamp
                    )
                    
                    # Emit event
                    if self.on_transcript_event:
                        self.on_transcript_event(event)
                    
                    logger.info(f"📝 Transcript: [{event.speaker.name}] {text[:50]}...")
                    
            except sr.UnknownValueError:
                # Speech not understood - ignore
                pass
            except sr.RequestError as e:
                logger.error(f"Recognition service error: {e}")
        
        except Exception as e:
            logger.error(f"Finalization error: {e}")
        
        finally:
            # Reset buffer
            self.speech_frames = []
            self.silence_frames = 0
    
    def resolve_overlap(self, speakers: list) -> Speaker:
        """
        Stage 3: Overlap Resolution
        
        PARAKEET RULE: INTERVIEWER > USER > NOISE
        If both speak, USER is discarded, INTERVIEWER survives
        
        Args:
            speakers: List of detected speakers
            
        Returns:
            Winning speaker
        """
        if not speakers:
            return Speaker.NOISE
        
        # Return highest priority speaker
        return max(speakers, key=lambda s: s.value)

"""
Audio Listener - Real-time speech transcription
"""
import logging
import threading
import queue
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from typing import Callable, Optional

from config import AUDIO_DEVICE_INDEX, SAMPLE_RATE, CHUNK_DURATION

logger = logging.getLogger(__name__)


class AudioListener:
    """
    Real-time audio listener with speech-to-text transcription.
    Listens to system audio (meeting) and transcribes in chunks.
    """
    
    def __init__(self, device_index: int = AUDIO_DEVICE_INDEX):
        """
        Initialize audio listener.
        
        Args:
            device_index: Audio input device index
        """
        self.device_index = device_index
        self.sample_rate = SAMPLE_RATE
        self.chunk_duration = CHUNK_DURATION
        
        self.recognizer = sr.Recognizer()
        self.audio_queue = queue.Queue()
        
        self.running = False
        self.listen_thread = None
        self.process_thread = None
        
        self.on_transcript: Optional[Callable[[str], None]] = None
        self.full_transcript = ""
    
    def start(self, on_transcript: Callable[[str], None]):
        """
        Start listening and transcribing.
        
        Args:
            on_transcript: Callback for each transcription chunk
        """
        self.on_transcript = on_transcript
        self.running = True
        self.full_transcript = ""
        
        # Start listener thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        # Start processor thread
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        logger.info(f"Audio listener started on device {self.device_index}")
    
    def stop(self):
        """Stop listening."""
        self.running = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        if self.process_thread:
            self.process_thread.join(timeout=2)
        logger.info("Audio listener stopped")
    
    def _listen_loop(self):
        """Continuously capture audio chunks."""
        chunk_samples = int(self.sample_rate * self.chunk_duration)
        
        try:
            with sd.InputStream(
                device=self.device_index,
                channels=1,
                samplerate=self.sample_rate,
                dtype=np.float32,
            ) as stream:
                while self.running:
                    audio_data, _ = stream.read(chunk_samples)
                    
                    # Convert to int16 for speech recognition
                    audio_int16 = (audio_data * 32767).astype(np.int16)
                    
                    # Queue the audio chunk
                    self.audio_queue.put(audio_int16.tobytes())
                    
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            self.running = False
    
    def _process_loop(self):
        """Process audio chunks and transcribe."""
        while self.running:
            try:
                # Get audio chunk (with timeout)
                audio_bytes = self.audio_queue.get(timeout=1)
                
                # Create AudioData for recognition
                audio_data = sr.AudioData(
                    audio_bytes,
                    self.sample_rate,
                    2  # 2 bytes per sample (int16)
                )
                
                # Transcribe
                try:
                    text = self.recognizer.recognize_google(audio_data)
                    if text and text.strip():
                        self.full_transcript += " " + text
                        if self.on_transcript:
                            self.on_transcript(text)
                        logger.info(f"✓ Transcribed: {text}")
                except sr.UnknownValueError:
                    logger.debug("No speech detected in chunk")
                    pass  # No speech detected
                except sr.RequestError as e:
                    logger.warning(f"Speech recognition API error: {e}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def get_full_transcript(self) -> str:
        """Get the full transcript so far."""
        return self.full_transcript.strip()
    
    @staticmethod
    def list_devices():
        """List available audio devices."""
        devices = sd.query_devices()
        print("\nAvailable Audio Devices:")
        print("-" * 50)
        for i, device in enumerate(devices):
            input_channels = device.get('max_input_channels', 0)
            if input_channels > 0:
                print(f"[{i}] {device['name']} (inputs: {input_channels})")
        print("-" * 50)
        return devices

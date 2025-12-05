import threading
import queue
import time
import logging
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
from pydub import AudioSegment

from .llm_client import transcribe_audio_bytes

logger = logging.getLogger(__name__)


class MicAudioListener:
    """
    Listens to your microphone.
    We use this only to include your speech in the transcript (optional).
    We do NOT trigger answers from this stream.
    """

    def __init__(
        self,
        samplerate: int = 16000,
        channels: int = 1,
        device: Optional[int] = None,
    ) -> None:
        self.samplerate = samplerate
        self.channels = channels
        self.device = device
        self.q: queue.Queue = queue.Queue()
        self.stop_flag = False
        self.stream = None
        self.worker_thread = None
        self.transcript_callback: Optional[Callable[[str], None]] = None

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"[MIC] Audio status warning: {status}")
        self.q.put(indata.copy())

    def start(self):
        self.stop_flag = False
        try:
            logger.info(f"[MIC] Starting audio listener on device {self.device}...")
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=self._audio_callback,
                device=self.device,
            )
            self.stream.start()
            logger.info(f"[MIC] Audio stream started successfully")
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
        except Exception as e:
            logger.error(f"[MIC] Error starting audio stream: {e}")
            raise

    def stop(self):
        self.stop_flag = True
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def _worker_loop(self):
        buffer = []
        last_flush = time.time()
        SEGMENT_SECONDS = 8

        while not self.stop_flag:
            try:
                data = self.q.get(timeout=1)
                buffer.append(data)
                elapsed = time.time() - last_flush
                if elapsed >= SEGMENT_SECONDS:
                    if buffer:
                        chunk = np.concatenate(buffer, axis=0)
                        buffer = []
                        last_flush = time.time()
                        text = self._transcribe_chunk(chunk)
                        if text and self.transcript_callback:
                            self.transcript_callback(text)
            except queue.Empty:
                continue

    def _transcribe_chunk(self, audio_np: np.ndarray) -> str:
        audio_np = (audio_np * 32767).astype(np.int16)
        seg = AudioSegment(
            audio_np.tobytes(),
            frame_rate=self.samplerate,
            sample_width=2,
            channels=self.channels,
        )
        buf = seg.export(format="wav")
        wav_bytes = buf.read()
        buf.close()
        text = transcribe_audio_bytes(wav_bytes)
        return text

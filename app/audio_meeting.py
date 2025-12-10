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


class MeetingAudioListener:
    """
    Listens to the meeting audio device, transcribes in small chunks,
    and calls transcript_callback(text) for each new chunk.

    This is the ONLY audio that will trigger answers.
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
            logger.warning(f"[MEETING] Audio status warning: {status}")
        self.q.put(indata.copy())

    def start(self):
        self.stop_flag = False
        try:
            # Validate device before attempting to open stream
            device_to_use = self.device
            
            if device_to_use is not None:
                try:
                    devices = sd.query_devices()
                    if isinstance(devices, dict):
                        # Single device returned
                        pass
                    elif isinstance(devices, list) and device_to_use < len(devices):
                        dev_info = devices[device_to_use]
                        if dev_info['max_input_channels'] == 0:
                            logger.warning(f"[MEETING] Device {device_to_use} has no input channels, using default")
                            device_to_use = None
                    else:
                        logger.warning(f"[MEETING] Device {device_to_use} not found, using default")
                        device_to_use = None
                except Exception as dev_err:
                    logger.warning(f"[MEETING] Could not validate device: {dev_err}, using default")
                    device_to_use = None
            
            logger.info(f"[MEETING] Starting audio listener on device {device_to_use}...")
            self.stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=self._audio_callback,
                device=device_to_use,
            )
            self.stream.start()
            logger.info(f"[MEETING] Audio stream started successfully on device {device_to_use}")
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
        except Exception as e:
            logger.error(f"[MEETING] Error starting audio stream: {e}", exc_info=True)
            raise

    def stop(self):
        self.stop_flag = True
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def _worker_loop(self):
        buffer = []
        last_flush = time.time()
        SEGMENT_SECONDS = 8  # adjust if you like
        audio_frames_received = 0

        while not self.stop_flag:
            try:
                data = self.q.get(timeout=1)
                buffer.append(data)
                audio_frames_received += 1
                
                elapsed = time.time() - last_flush
                if elapsed >= SEGMENT_SECONDS:
                    if buffer:
                        try:
                            logger.info(f"[MEETING] Processing {audio_frames_received} audio frames")
                            chunk = np.concatenate(buffer, axis=0)
                            buffer = []
                            audio_frames_received = 0
                            last_flush = time.time()
                            text = self._transcribe_chunk(chunk)
                            if text and self.transcript_callback:
                                logger.info(f"[MEETING] Transcribed: {text[:100]}...")
                                try:
                                    self.transcript_callback(text)
                                except Exception as cb_err:
                                    logger.error(f"[MEETING] Callback error: {cb_err}", exc_info=True)
                        except Exception as proc_err:
                            logger.error(f"[MEETING] Processing error: {proc_err}", exc_info=True)
                            buffer = []  # Clear buffer to prevent accumulation
                            audio_frames_received = 0
                            last_flush = time.time()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[MEETING] Error in worker loop: {e}", exc_info=True)
                # Don't raise - keep the loop alive even if there's an error

    def _transcribe_chunk(self, audio_np: np.ndarray) -> str:
        # float32 -> int16 -> wav bytes
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

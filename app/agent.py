import os
import time
import threading

from .pdf_index import PDFIndex
from .screen_capture import capture_screen_image, capture_screen_text
from .audio_meeting import MeetingAudioListener
from .audio_mic import MicAudioListener
from .context_manager import ContextManager
from .question_detector import is_question
from .llm_client import ask_llm_with_context, summarize_meeting


class MeetingAgentCore:
    def __init__(self, overlay_widget, meeting_device_index=None, mic_device_index=None):
        self.overlay = overlay_widget
        self.context = ContextManager()
        self.pdf_index = PDFIndex()
        self.pdf_index.build()

        self.last_screen_text = ""
        self.last_screen_image = None
        self.screen_lock = threading.Lock()

        # Audio listeners
        self.meeting_listener = MeetingAudioListener(device=meeting_device_index)
        self.meeting_listener.transcript_callback = self.on_meeting_transcript

        self.mic_listener = MicAudioListener(device=mic_device_index)
        self.mic_listener.transcript_callback = self.on_mic_transcript

        self.running = False
        self.screen_thread = None

    # --- Start / stop ---

    def start(self):
        self.running = True
        self.meeting_listener.start()
        self.mic_listener.start()
        self.screen_thread = threading.Thread(target=self._screen_loop, daemon=True)
        self.screen_thread.start()

    def stop(self):
        self.running = False
        self.meeting_listener.stop()
        self.mic_listener.stop()

    # --- Screen polling ---

    def _screen_loop(self):
        while self.running:
            try:
                img = capture_screen_image()
                text = capture_screen_text()
                with self.screen_lock:
                    self.last_screen_image = img
                    self.last_screen_text = text
            except Exception as e:
                print("Screen capture error:", e)
            time.sleep(3)

    # --- Transcript callbacks ---

    def on_meeting_transcript(self, text: str):
        """
        Called when a new transcription segment is obtained
        from the MEETING audio (other people).
        We use this to trigger answers.
        """
        clean = text.strip()
        if not clean:
            return

        self.context.add_transcript(clean, source="meeting")
        print("[MEETING]", clean)

        if is_question(clean):
            self.handle_question(clean)

    def on_mic_transcript(self, text: str):
        """
        Called when your microphone speech is transcribed.
        We log it to transcript for context, but NEVER trigger answers.
        """
        clean = text.strip()
        if not clean:
            return

        self.context.add_transcript(clean, source="mic")
        print("[MIC]", clean)
        # IMPORTANT: no question detection here; your questions are ignored.

    # --- Question answering ---

    def handle_question(self, question: str):
        """
        Called when someone else in the meeting asks a question.
        """
        with self.screen_lock:
            screen_text = self.last_screen_text or ""
            screen_img = self.last_screen_image

        pdf_chunks = self.pdf_index.query(question, k=5)
        pdf_context = "\n\n---\n\n".join(pdf_chunks) if pdf_chunks else ""

        transcript_context = self.context.get_recent_transcript()

        try:
            answer = ask_llm_with_context(
                question=question,
                transcript_context=transcript_context,
                screen_text=screen_text,
                pdf_context=pdf_context,
                screen_image=screen_img,
            )
        except Exception as e:
            answer = f"Error while generating answer: {e}"

        self.context.log_qa(question, answer)
        self.overlay.show_answer(answer)

    # --- Summary ---

    def generate_summary_and_save(self) -> str:
        full_transcript = self.context.get_full_transcript()
        qa_log = self.context.get_qa_log()
        summary = summarize_meeting(full_transcript, qa_log)

        os.makedirs("meeting_summaries", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.join("meeting_summaries", f"summary_{timestamp}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(summary)
        return path

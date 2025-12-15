"""
Main Application - Parakeet-Style Interview Assistant
Transcript-driven, deterministic, speaker-gated system
"""
import sys
import os
import logging
import threading

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.overlay import StealthOverlay
from backend.audio.parakeet_audio import ParakeetAudioProcessor, TranscriptEvent, Speaker
from backend.audio.decision_engine import ParakeetDecisionEngine, ParakeetAnswerFormatter
from backend.ai.interview_engine import InterviewEngine
from backend.ai.resume_parser import ResumeParser
from backend.capture.screen_capture import ScreenCapture
from backend.capture.ocr_processor import OCRProcessor
from config import AUDIO_DEVICE_INDEX

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class ParakeetInterviewAssistant:
    """
    Parakeet-Style Interview Assistant
    
    CORE PRINCIPLE: No transcript event → no reasoning → no answer
    
    Architecture:
    1. Audio → VAD → Speaker → Finalization → TranscriptEvent
    2. TranscriptEvent → Decision Gate → Answer Generation
    3. Cooldown prevents double answers
    """
    
    def __init__(self):
        # UI
        self.overlay = StealthOverlay()
        
        # Parakeet components
        self.audio_processor = ParakeetAudioProcessor(AUDIO_DEVICE_INDEX)
        self.decision_engine = ParakeetDecisionEngine()
        
        # AI engine
        self.engine = InterviewEngine()
        self.resume_parser = ResumeParser()
        
        # Screen capture
        self.screen_capture = ScreenCapture()
        self.ocr = OCRProcessor()
        self.screen_timer = None
        self.last_screen_text = ""
        
        # State
        self.current_role = "SDE"
        self.is_paused = False
        self.resume_context = ""
        
        self._connect_signals()
        self._setup_shortcuts()
        
        logger.info("Parakeet Interview Assistant initialized")
    
    def _connect_signals(self):
        """Connect UI signals"""
        self.overlay.start_requested.connect(self._on_start)
        self.overlay.resume_selected.connect(self._on_resume_selected)
        self.overlay.role_changed.connect(self._on_role_changed)
        self.overlay.close_requested.connect(self._on_close)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            "Ctrl+Shift+H": self._toggle_visibility,
            "Ctrl+Shift+P": self._toggle_pause,
            "Ctrl+Shift+C": self._clear_transcript,
            "Ctrl+Shift+Up": lambda: self.overlay.adjust_font_size(True),
            "Ctrl+Shift+Down": lambda: self.overlay.adjust_font_size(False),
            "Ctrl+Shift+Right": lambda: self.overlay.adjust_opacity(True),
            "Ctrl+Shift+Left": lambda: self.overlay.adjust_opacity(False),
            "Ctrl+Shift+Q": self._emergency_hide
        }
        
        for key, handler in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self.overlay)
            shortcut.activated.connect(handler)
        
        logger.info("Keyboard shortcuts initialized: Ctrl+Shift+[H,P,C,Up,Down,Left,Right,Q]")
    
    def _on_start(self):
        """
        Start the Parakeet system
        
        Pipeline:
        Audio → VAD → Transcript Events → Decision Gate → Answers
        """
        logger.info("🚀 Starting Parakeet system")
        
        # Start audio processor with transcript callback
        self.audio_processor.start(self._on_transcript_event)
        
        # Start screen capture (for context changes)
        self.screen_timer = QTimer()
        self.screen_timer.timeout.connect(self._capture_screen)
        self.screen_timer.start(2000)
        
        # Start cooldown checker
        self.cooldown_timer = QTimer()
        self.cooldown_timer.timeout.connect(self.decision_engine.check_cooldown_timeout)
        self.cooldown_timer.start(500)
        
        self.overlay.show_message("▶ Parakeet system active\n\nListening for questions...")
        logger.info("Parakeet system started")
    
    def _on_transcript_event(self, event: TranscriptEvent):
        """
        CRITICAL: Main transcript event handler
        
        This is the ONLY entry point for reasoning
        
        Flow:
        1. Display transcript
        2. Update speaker state
        3. Check decision gate
        4. Generate answer if gate passes
        
        Args:
            event: Finalized transcript event
        """
        if self.is_paused:
            return
        
        # Log event
        logger.info(f"📝 Transcript Event: [{event.speaker.name}] {event.text}")
        
        # Display in UI
        self.overlay.add_transcript_line(event.speaker.name, event.text)
        
        # Update decision engine state
        if event.speaker == Speaker.INTERVIEWER:
            self.decision_engine.on_interviewer_spoke()
        
        # Decision Gate: Should we generate an answer?
        if self.decision_engine.should_generate_answer(event):
            self._generate_answer(event)
    
    def _generate_answer(self, event: TranscriptEvent):
        """
        Generate answer for question
        
        PARAKEET FORMAT:
        1. Problem restatement
        2. Approach explanation
        3. Step-by-step logic
        4. Code (if applicable)
        5. Complexity
        
        Args:
            event: Transcript event containing the question
        """
        logger.info(f"🤖 Generating answer for: {event.text[:50]}...")
        
        # Show question in UI
        self.overlay.show_question(event.text)
        
        # Activate cooldown IMMEDIATELY
        self.decision_engine.activate_cooldown()
        
        # Generate answer in background thread
        thread = threading.Thread(
            target=self._generate_answer_worker,
            args=(event.text,),
            daemon=True
        )
        thread.start()
    
    def _generate_answer_worker(self, question: str):
        """
        Worker thread for answer generation
        
        Uses structured prompt template
        """
        try:
            # Format prompt using Parakeet template
            prompt = ParakeetAnswerFormatter.format_prompt(
                question=question,
                resume_context=self.resume_context
            )
            
            # Generate answer (streaming)
            for chunk in self.engine.generate_answer_streaming(question, self.last_screen_text):
                self.overlay.append_answer(chunk)
            
            logger.info("✅ Answer generation complete")
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            self.overlay.append_answer(f"\n\n⚠ Error: {e}")
    
    def _capture_screen(self):
        """
        Capture screen for context
        
        If screen changes significantly → release cooldown
        """
        if self.is_paused:
            return
        
        try:
            frame = self.screen_capture.capture_frame()
            if frame is None:
                return
            
            try:
                result = self.ocr.process_image(frame.image)
                if result and result.text:
                    text = result.text.strip()
                    
                    if text and len(text) > 20:
                        # Check if screen changed
                        if self._screen_changed(text):
                            logger.info(f"📺 Screen changed: {text[:50]}...")
                            self.last_screen_text = text
                            
                            # Release cooldown on screen change
                            self.decision_engine.on_screen_changed()
                            
            except Exception as ocr_error:
                if "tesseract" in str(ocr_error).lower():
                    if self.screen_timer:
                        self.screen_timer.stop()
                    return
                        
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
    
    def _screen_changed(self, new_text: str) -> bool:
        """Check if screen content changed significantly"""
        if not self.last_screen_text:
            return True
        
        # Simple similarity check
        common = set(new_text.split()) & set(self.last_screen_text.split())
        total = set(new_text.split()) | set(self.last_screen_text.split())
        if not total:
            return False
        
        similarity = len(common) / len(total)
        return similarity < 0.7  # Less than 70% similar = changed
    
    def _on_resume_selected(self, pdf_path: str):
        """Handle resume upload"""
        logger.info(f"Loading resume: {pdf_path}")
        
        result = self.resume_parser.parse_pdf(pdf_path)
        if result:
            self.resume_context = result.get("text", "")
            self.engine.set_resume_context(self.resume_context)
            skill_count = result.get("skill_count", 0)
            self.overlay.show_message(
                f"✓ Resume loaded\n"
                f"  Skills found: {skill_count}\n\n"
                f"Select role and click Start"
            )
        else:
            self.overlay.show_message("⚠ Could not parse resume")
    
    def _on_role_changed(self, role: str):
        """Handle role change"""
        self.current_role = role
        self.engine = InterviewEngine(role)
        if self.resume_context:
            self.engine.set_resume_context(self.resume_context)
        logger.info(f"Role changed to: {role}")
    
    def _toggle_visibility(self):
        """Toggle overlay visibility"""
        if self.overlay.isVisible():
            self.overlay.hide()
            logger.info("Overlay hidden")
        else:
            self.overlay.show()
            logger.info("Overlay shown")
    
    def _toggle_pause(self):
        """Toggle pause/resume"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            logger.info("⏸ System PAUSED")
            self.overlay.show_message("⏸ PAUSED\n\nPress Ctrl+Shift+P to resume")
        else:
            logger.info("▶ System RESUMED")
            self.overlay.show_message("▶ RESUMED\n\nListening for questions...")
    
    def _clear_transcript(self):
        """Clear transcript"""
        self.overlay.clear_transcript()
        logger.info("Transcript cleared")
    
    def _emergency_hide(self):
        """Emergency hide"""
        self.overlay.hide()
        if self.screen_timer:
            self.screen_timer.stop()
        self.audio_processor.stop()
        logger.info("🚨 EMERGENCY HIDE")
    
    def _on_close(self):
        """Cleanup on close"""
        logger.info("Shutting down Parakeet system")
        self.audio_processor.stop()
        if self.screen_timer:
            self.screen_timer.stop()
        QApplication.quit()
    
    def run(self):
        """Run the application"""
        self.overlay.show()
        logger.info("Parakeet Interview Assistant ready")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    assistant = ParakeetInterviewAssistant()
    assistant.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

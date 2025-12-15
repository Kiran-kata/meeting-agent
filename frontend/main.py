"""
Main Application - Interview Assistant Entry Point
"""
import sys
import os
import logging
import asyncio
import threading
import time

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.overlay import StealthOverlay
from frontend.audio_listener import AudioListener
from backend.ai.interview_engine import InterviewEngine
from backend.ai.resume_parser import ResumeParser
from backend.ai.scoring import ScoringEngine
from backend.ai.followup_generator import FollowUpGenerator
from backend.capture.screen_capture import ScreenCapture
from backend.capture.ocr_processor import OCRProcessor
from config import AUDIO_DEVICE_INDEX

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class InterviewAssistant:
    """
    Main Interview Assistant application.
    Coordinates UI, audio, screen capture, AI engine, and scoring.
    """
    
    def __init__(self):
        self.overlay = StealthOverlay()
        self.audio = AudioListener(AUDIO_DEVICE_INDEX)
        self.engine = InterviewEngine()
        self.resume_parser = ResumeParser()
        self.scoring = ScoringEngine()
        self.followup = FollowUpGenerator()
        
        # Screen capture components
        self.screen_capture = ScreenCapture()
        self.ocr = OCRProcessor()
        self.screen_timer = None
        self.last_screen_text = ""
        
        self.current_role = "SDE"
        self.transcript_buffer = ""
        self.screen_buffer = ""
        self.processing_question = False
        self.is_paused = False
        
        self._connect_signals()
        self._setup_shortcuts()
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        self.overlay.start_requested.connect(self._on_start)
        self.overlay.resume_selected.connect(self._on_resume_selected)
        self.overlay.role_changed.connect(self._on_role_changed)
        self.overlay.close_requested.connect(self._on_close)
    
    def _setup_shortcuts(self):
        """Setup global keyboard shortcuts for stealth operation."""
        # Ctrl+Shift+H - Hide/Show overlay
        hide_shortcut = QShortcut(QKeySequence("Ctrl+Shift+H"), self.overlay)
        hide_shortcut.activated.connect(self._toggle_visibility)
        
        # Ctrl+Shift+P - Pause/Resume listening
        pause_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self.overlay)
        pause_shortcut.activated.connect(self._toggle_pause)
        
        # Ctrl+Shift+C - Clear transcript
        clear_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self.overlay)
        clear_shortcut.activated.connect(self._clear_transcript)
        
        # Ctrl+Shift+Up - Increase font size
        font_up_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Up"), self.overlay)
        font_up_shortcut.activated.connect(lambda: self.overlay.adjust_font_size(True))
        
        # Ctrl+Shift+Down - Decrease font size
        font_down_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Down"), self.overlay)
        font_down_shortcut.activated.connect(lambda: self.overlay.adjust_font_size(False))
        
        # Ctrl+Shift+Right - Increase opacity
        opacity_up_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Right"), self.overlay)
        opacity_up_shortcut.activated.connect(lambda: self.overlay.adjust_opacity(True))
        
        # Ctrl+Shift+Left - Decrease opacity
        opacity_down_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Left"), self.overlay)
        opacity_down_shortcut.activated.connect(lambda: self.overlay.adjust_opacity(False))
        
        # Ctrl+Shift+Q - Emergency hide (instant invisibility)
        emergency_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Q"), self.overlay)
        emergency_shortcut.activated.connect(self._emergency_hide)
        
        logger.info("Keyboard shortcuts initialized: Ctrl+Shift+[H,P,C,Up,Down,Left,Right,Q]")
    
    def _toggle_visibility(self):
        """Toggle overlay visibility."""
        if self.overlay.isVisible():
            self.overlay.hide()
            logger.info("Overlay hidden (Ctrl+Shift+H)")
        else:
            self.overlay.show()
            logger.info("Overlay shown (Ctrl+Shift+H)")
    
    def _toggle_pause(self):
        """Toggle pause/resume listening."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            logger.info("Listening PAUSED (Ctrl+Shift+P)")
            self.overlay.show_message("⏸ PAUSED\\n\\nPress Ctrl+Shift+P to resume")
        else:
            logger.info("Listening RESUMED (Ctrl+Shift+P)")
            self.overlay.show_message("▶ RESUMED\\n\\nListening for questions...")
    
    def _clear_transcript(self):
        """Clear transcript buffer and display."""
        self.transcript_buffer = ""
        self.overlay.clear_transcript()
        logger.info("Transcript cleared (Ctrl+Shift+C)")
    
    def _emergency_hide(self):
        """Emergency hide - instant invisibility."""
        self.overlay.hide()
        if self.screen_timer:
            self.screen_timer.stop()
        if self.audio:
            self.audio.stop()
        logger.info("EMERGENCY HIDE activated (Ctrl+Shift+Q)")
    
    def _on_start(self):
        """Handle start button click."""
        logger.info("Interview started")
        self.scoring = ScoringEngine()  # Reset scoring
        self.transcript_buffer = ""
        self.screen_buffer = ""
        
        # Start audio listener
        self.audio.start(self._on_transcript)
        
        # Start screen capture timer (every 2 seconds)
        self.screen_timer = QTimer()
        self.screen_timer.timeout.connect(self._capture_screen)
        self.screen_timer.start(2000)  # 2 second intervals
        logger.info("Screen capture started (2s intervals)")
    
    def _on_resume_selected(self, pdf_path: str):
        """Handle resume upload."""
        logger.info(f"Loading resume: {pdf_path}")
        
        result = self.resume_parser.parse_pdf(pdf_path)
        if result:
            self.engine.set_resume_context(result.get("text", ""))
            skill_count = result.get("skill_count", 0)
            self.overlay.show_message(
                f"✓ Resume loaded\n"
                f"  Skills found: {skill_count}\n\n"
                f"Select role and click Start"
            )
        else:
            self.overlay.show_message("⚠ Could not parse resume")
    
    def _on_role_changed(self, role: str):
        """Handle role selection change."""
        self.current_role = role
        self.engine = InterviewEngine(role)
        # Re-apply resume context if available
        if self.resume_parser.resume_text:
            self.engine.set_resume_context(self.resume_parser.resume_text)
        logger.info(f"Role changed to: {role}")
    
    def _capture_screen(self):
        """Capture screen and extract text via OCR."""
        if self.processing_question:
            return
        
        try:
            # Capture screen
            frame = self.screen_capture.capture_frame()
            if frame is None:
                return
            
            # Run OCR (skip if tesseract not installed)
            try:
                result = self.ocr.process_image(frame.image)
                if result and result.text:
                    text = result.text.strip()
                    
                    # Only process if text changed significantly
                    if text and len(text) > 20 and text != self.last_screen_text:
                        # Check if this is new content (not just same screen)
                        if self._is_new_content(text, self.last_screen_text):
                            logger.info(f"📺 Screen OCR ({len(text)} chars): {text[:100]}...")
                            self.screen_buffer = text
                            self.last_screen_text = text
                            
                            # Check for question on screen
                            self._check_screen_for_question()
            except Exception as ocr_error:
                # OCR failed (tesseract not installed) - disable screen timer
                if "tesseract" in str(ocr_error).lower():
                    logger.warning("Tesseract not installed - disabling screen capture. Install with: pip install pytesseract")
                    if self.screen_timer:
                        self.screen_timer.stop()
                    return
                raise
                        
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
    
    def _is_new_content(self, new_text: str, old_text: str) -> bool:
        """Check if screen content has meaningfully changed."""
        if not old_text:
            return True
        # Simple check: if more than 30% different
        common = set(new_text.split()) & set(old_text.split())
        total = set(new_text.split()) | set(old_text.split())
        if not total:
            return False
        similarity = len(common) / len(total)
        return similarity < 0.7  # Less than 70% similar = new content
    
    def _check_screen_for_question(self):
        """Check if screen contains a coding question."""
        if not self.screen_buffer or self.processing_question or self.is_paused:
            return
        
        # Quick indicators that screen has a coding question
        coding_indicators = [
            'function', 'def ', 'class ', 'return', 'algorithm',
            'implement', 'write a', 'given', 'input:', 'output:',
            'example', 'constraint', 'leetcode', 'hackerrank',
            'time complexity', 'space complexity', 'array', 'string',
            'solve', 'find', 'calculate', 'determine'
        ]
        
        screen_lower = self.screen_buffer.lower()
        matches = sum(1 for ind in coding_indicators if ind in screen_lower)
        
        if matches >= 2:  # At least 2 indicators
            logger.info(f"🎯 Detected coding question on screen! ({matches} indicators)")
            self.processing_question = True
            
            # Show screen detection indicator
            self.overlay.set_screen_detected(True)
            
            # Process the screen content as a question from SCREEN
            thread = threading.Thread(
                target=self._process_question,
                args=(self.screen_buffer, "screen"),
                daemon=True
            )
            thread.start()
    
    def _on_transcript(self, text: str):
        """Handle new transcript chunk."""
        if self.is_paused:
            return
        
        logger.info(f"📝 Received transcript: {text}")
        self.transcript_buffer += " " + text
        
        # Add to live transcript display (assume USER by default, will detect INTERVIEWER in question detection)
        self.overlay.add_transcript_line("USER", text)
        
        # Check for question in buffer
        if not self.processing_question:
            self._check_for_question()
    
    def _check_for_question(self):
        """Check if transcript contains a question and process it."""
        if len(self.transcript_buffer) < 20 or self.is_paused:
            return
        
        logger.info(f"🔍 Checking buffer ({len(self.transcript_buffer)} chars): {self.transcript_buffer[-100:]}")
        
        # Try to detect question
        question = self.engine.detect_question(self.transcript_buffer)
        
        if question:
            self.processing_question = True
            
            # Mark last transcript line as INTERVIEWER (question detected)
            if self.overlay.transcript_lines:
                self.overlay.transcript_lines[-1]["speaker"] = "INTERVIEWER"
            
            self.transcript_buffer = ""  # Clear buffer
            
            # Process question in background
            thread = threading.Thread(
                target=self._process_question,
                args=(question, "audio"),
                daemon=True
            )
            thread.start()
    
    def _process_question(self, question: str, source: str = "audio"):
        """Process detected question and generate answer."""
        try:
            logger.info(f"Processing question from {source}: {question[:50]}...")
            
            # Show question in UI
            self.overlay.show_question(question)
            
            # Determine speaker - assume INTERVIEWER unless we detect USER patterns
            # Simple heuristic: if question came from screen, it's INTERVIEWER
            speaker = "INTERVIEWER"
            if source == "audio":
                # Could add voice detection here, for now assume all audio is INTERVIEWER
                speaker = "INTERVIEWER"
            
            # Get screen context
            screen_context = self.screen_buffer if self.screen_buffer else ""
            
            # Generate streaming answer
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            full_answer = ""
            
            async def stream_answer():
                nonlocal full_answer
                async for chunk in self.engine.generate_answer_stream(
                    question=question,
                    resume_context=self.resume_parser.get_context_for_answer(),
                    screen_context=screen_context,
                    speaker=speaker
                ):
                    full_answer += chunk
                    # Update UI
                    self.overlay.append_answer(chunk)
            
            loop.run_until_complete(stream_answer())
            loop.close()
            
            # Score the answer
            score_result = self.scoring.score_answer(
                question, 
                full_answer,
                "behavioral" if "tell me" in question.lower() else "technical"
            )
            
            # Show score
            self.overlay.show_score(
                int(score_result.overall_score * 100),
                score_result.feedback
            )
            
            logger.info(f"Answer generated, score: {score_result.overall_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            self.overlay.append_answer(f"\n\n⚠ Error: {str(e)}")
        finally:
            self.processing_question = False
            # Hide screen indicator after processing
            self.overlay.set_screen_detected(False)
    
    def _on_close(self):
        """Handle app close."""
        logger.info("Closing interview assistant")
        
        # Stop screen capture timer
        if self.screen_timer:
            self.screen_timer.stop()
        
        # Stop audio
        self.audio.stop()
        
        # Show final score if we have any
        summary = self.scoring.get_session_summary()
        if summary.get("questions_answered", 0) > 0:
            logger.info(f"Session summary: {summary}")
            
            # Save session
            self._save_session(summary)
    
    def _save_session(self, summary: dict):
        """Save session data."""
        import json
        from datetime import datetime
        
        os.makedirs("sessions", exist_ok=True)
        filename = f"sessions/interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Session saved to {filename}")
    
    def run(self):
        """Start the application."""
        self.overlay.show_message(
            "🎯 Interview Assistant Ready\n\n"
            "1. Upload your resume (PDF)\n"
            "2. Select interview role\n"
            "3. Click Start to begin\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "KEYBOARD SHORTCUTS:\n"
            "Ctrl+Shift+H - Hide/Show\n"
            "Ctrl+Shift+P - Pause/Resume\n"
            "Ctrl+Shift+C - Clear transcript\n"
            "Ctrl+Shift+↑/↓ - Font size\n"
            "Ctrl+Shift+←/→ - Opacity\n"
            "Ctrl+Shift+Q - Emergency hide\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Transparent UI • Always on top\n"
            "Screen capture enabled"
        )
        self.overlay.show()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    
    assistant = InterviewAssistant()
    assistant.run()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

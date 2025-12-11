import os
import time
import threading
import logging
import asyncio

from .pdf_index import PDFIndex
from .screen_capture import capture_screen_image, capture_screen_text
from .audio_meeting import MeetingAudioListener
from .audio_mic import MicAudioListener
from .context_manager import ContextManager
from .question_detector import is_question
from .llm_client import ask_llm_with_context, summarize_meeting
from .streaming_llm import ask_llm_streaming
from .screen_share_detector import HiddenOverlayManager
from .narration import Narrator
from .parakeet_features import (
    ResumeProfile,
    CodingInterviewDetector,
    MultilingualSupport,
    InterviewPerformanceAnalyzer,
    QuestionAutoDetector,
    StealthMode
)

logger = logging.getLogger(__name__)


class MeetingAgentCore:
    def __init__(self, overlay_widget, meeting_device_index=None, mic_device_index=None):
        self.overlay = overlay_widget
        self.context = ContextManager()
        self.pdf_index = PDFIndex()
        self.pdf_index.build()

        self.last_screen_text = ""
        self.last_screen_image = None
        self.screen_lock = threading.Lock()

        # Text-to-speech narrator
        self.narrator = Narrator()
        
        # Advanced screen share hiding (Cluely AI style)
        self.screen_share_manager = HiddenOverlayManager(overlay_widget)

        # Parakeet AI-inspired features
        self.resume_profile = ResumeProfile()
        self.coding_detector = CodingInterviewDetector()
        self.multilingual = MultilingualSupport()
        self.performance_analyzer = InterviewPerformanceAnalyzer()
        self.question_detector = QuestionAutoDetector()
        self.stealth_mode = StealthMode(overlay_widget)

        # Audio listeners
        self.meeting_listener = MeetingAudioListener(device=meeting_device_index)
        self.meeting_listener.transcript_callback = self.on_meeting_transcript

        self.mic_listener = MicAudioListener(device=mic_device_index)
        self.mic_listener.transcript_callback = self.on_mic_transcript

        self.running = False
        self.screen_thread = None

    # --- PDF Management ---

    def add_pdf_file(self, pdf_path: str):
        """
        Add a PDF file to the index for use during meeting.
        Also tries to load it as a resume for profile context.
        
        Args:
            pdf_path: Full path to the PDF file
        """
        success = self.pdf_index.add_pdf(pdf_path)
        if success:
            logger.info(f"PDF file loaded: {pdf_path}")
            
            # If no resume loaded yet, try this as resume
            if not self.resume_profile.resume_text:
                self.resume_profile.upload_resume(pdf_path)
        else:
            logger.error(f"Failed to load PDF: {pdf_path}")
    
    def set_interview_profile(self, name: str, email: str = "", role: str = ""):
        """
        Set up interview profile with personal information.
        Parakeet AI feature: Profile-matched interview responses.
        """
        self.resume_profile.create_profile(name, email, role)
        logger.info(f"Interview profile created: {name}")
    
    def upload_resume(self, pdf_path: str) -> bool:
        """
        Upload resume for experience-matched answers.
        Parakeet AI feature: Context matching from resume.
        """
        success = self.resume_profile.upload_resume(pdf_path)
        if success:
            self.pdf_index.add_pdf(pdf_path)
        return success

    # --- Start / stop ---

    def start(self):
        try:
            self.running = True
            logger.info("Starting meeting agent...")
            
            # Start performance analysis
            self.performance_analyzer.start_interview()
            logger.info("Interview performance tracking started")
            
            # Start advanced screen share detection
            self.screen_share_manager.start()
            logger.info("Screen share detection started")
            
            self.meeting_listener.start()
            logger.info("Meeting listener started")
            self.mic_listener.start()
            logger.info("Mic listener started")
            self.screen_thread = threading.Thread(target=self._screen_loop, daemon=True)
            self.screen_thread.start()
            logger.info("Screen thread started - agent ready")
        except Exception as e:
            logger.error(f"Error starting agent: {e}", exc_info=True)
            self.running = False
            raise

    def stop(self):
        try:
            self.running = False
            
            # Stop screen share detection
            self.screen_share_manager.stop()
            logger.info("Screen share detection stopped")
            
            if self.meeting_listener:
                self.meeting_listener.stop()
            if self.mic_listener:
                self.mic_listener.stop()
            logger.info("Agent stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping agent: {e}", exc_info=True)

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
        Uses streaming for real-time answer generation like Parakeet.AI.
        Includes interview performance tracking and multilingual support.
        """
        def answer_thread():
            try:
                # Categorize question (Parakeet AI feature)
                question_category = self.question_detector.categorize_question(question)
                logger.info(f"Question category: {question_category}")
                
                with self.screen_lock:
                    screen_text = self.last_screen_text or ""
                    screen_img = self.last_screen_image

                # Check for coding interview (Parakeet AI feature)
                coding_info = self.coding_detector.analyze_screen_content(screen_text, screen_img)
                if coding_info["is_coding_interview"]:
                    logger.info(f"Coding interview detected: {coding_info['platform']}")

                pdf_chunks = self.pdf_index.query(question, k=5)
                pdf_context = "\n\n---\n\n".join(pdf_chunks) if pdf_chunks else ""

                # Add resume context for personalized answers (Parakeet AI feature)
                resume_context = self.resume_profile.get_profile_context()
                if resume_context:
                    pdf_context = resume_context + "\n\n---\n\n" + pdf_context

                transcript_context = self.context.get_recent_transcript()

                try:
                    # Display question immediately
                    self.overlay.show_question(question)
                    logger.info(f"Question detected: {question[:50]}...")
                    
                    # Stream the answer in real-time
                    streaming_answer = ""
                    answer_start_time = time.time()
                    
                    async def on_chunk(chunk: str):
                        """Called for each streaming chunk"""
                        nonlocal streaming_answer
                        streaming_answer += chunk
                        # Update UI with partial answer
                        self.overlay.append_answer_chunk(chunk)
                    
                    # Run async streaming in executor to avoid blocking
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        answer = loop.run_until_complete(
                            ask_llm_streaming(
                                question=question,
                                pdf_context=pdf_context,
                                transcript_context=transcript_context,
                                callback=on_chunk,
                            )
                        )
                    finally:
                        loop.close()
                    
                    answer_time = time.time() - answer_start_time
                    logger.info(f"Streaming answer complete: {answer[:100]}... (took {answer_time:.1f}s)")
                    
                    # Track performance (Parakeet AI feature)
                    self.performance_analyzer.add_qa_pair(question, answer, answer_time)
                    
                    # Narrate the complete answer (non-blocking, runs in background)
                    self.narrator.narrate(answer, blocking=False)
                    
                    self.context.log_qa(question, answer)
                    
                except Exception as e:
                    error_msg = f"Error while generating answer: {e}"
                    logger.error(f"Error generating answer: {e}", exc_info=True)
                    self.overlay.show_qa_pair(question, error_msg)
                    
            except Exception as e:
                logger.error(f"Error in answer_thread: {e}", exc_info=True)
        
        # Spawn thread so we don't block the audio listener
        thread = threading.Thread(target=answer_thread, daemon=True)
        thread.start()

    # --- Summary ---

    def generate_summary_and_save(self) -> str:
        """
        Generate comprehensive interview summary with performance analysis.
        Parakeet AI feature: Post-interview insights and recommendations.
        """
        full_transcript = self.context.get_full_transcript()
        qa_log = self.context.get_qa_log()
        
        # Generate interview performance analysis (Parakeet AI feature)
        analysis = self.performance_analyzer.end_interview()
        
        # Check if we have any meaningful content
        if not full_transcript or not full_transcript.strip():
            fallback_msg = """INTERVIEW SUMMARY
================

No audio was captured during this interview.

Possible reasons:
- Audio device not properly configured
- Gemini API quota exceeded (check https://ai.dev/usage?tab=rate-limit)
- No audio was actually present

To troubleshoot:
1. Run: python -c "import sounddevice as sd; print(sd.query_devices())"
2. Check MEETING_DEVICE_INDEX in main.py (currently device 0)
3. Verify Gemini API key is valid and has quota available
4. Test audio devices separately using test_audio_devices.py
"""
            os.makedirs("meeting_summaries", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            path = os.path.join("meeting_summaries", f"summary_{timestamp}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(fallback_msg)
            
            # Narrate the summary info
            narration_text = "No audio was captured during this interview. Please check your audio device configuration."
            self.narrator.narrate(narration_text, blocking=False)
            logger.warning("No transcript available for summary generation")
            return path
        
        try:
            summary = summarize_meeting(full_transcript, qa_log)
            
            # Append performance analysis to summary
            summary_with_analysis = f"""{summary}

PERFORMANCE ANALYSIS (Powered by Parakeet AI)
==============================================

Interview Duration: {analysis.get('interview_duration_minutes', 0)} minutes
Total Questions: {analysis.get('total_questions', 0)}
Average Answer Time: {analysis.get('average_answer_time_seconds', 0)} seconds
Interview Efficiency: {analysis.get('interview_efficiency', 'N/A')}

RECOMMENDATIONS FOR IMPROVEMENT:
{chr(10).join('- ' + r for r in analysis.get('recommendations', []))}

Summary Generated: {analysis.get('generated_at', 'Unknown')}
"""
            
            os.makedirs("meeting_summaries", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            path = os.path.join("meeting_summaries", f"summary_{timestamp}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(summary_with_analysis)
            
            # Also save detailed analysis as JSON
            self.performance_analyzer.save_analysis(analysis, f"analysis_{timestamp}.json")
            
            logger.info(f"Summary with analysis saved to {path}")
            
            # Narrate a brief summary completion message
            self.narrator.narrate(
                f"Interview summary generated. {analysis.get('total_questions', 0)} questions answered in {analysis.get('interview_duration_minutes', 0):.1f} minutes.",
                blocking=False
            )
            
            return path
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            fallback_msg = f"""INTERVIEW SUMMARY - ERROR
=======================

Could not generate AI-powered summary due to an error:
{str(e)}

RAW TRANSCRIPT:
{full_transcript}

Q&A LOG:
{qa_log}

PERFORMANCE METRICS:
- Interview Duration: {analysis.get('interview_duration_minutes', 0)} minutes
- Total Questions: {analysis.get('total_questions', 0)}
- Average Answer Time: {analysis.get('average_answer_time_seconds', 0)} seconds

Please try again later or check your API configuration.
"""
            os.makedirs("meeting_summaries", exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            path = os.path.join("meeting_summaries", f"summary_{timestamp}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(fallback_msg)
            
            self.narrator.narrate("Could not generate summary. Check the file for details.", blocking=False)
            return path
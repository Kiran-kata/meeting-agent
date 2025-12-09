"""
Text-to-Speech Narration Module
Provides voice narration for meeting agent responses
"""
import logging
import threading
import pyttsx3

logger = logging.getLogger(__name__)


class Narrator:
    """Handles text-to-speech narration of agent responses"""
    
    def __init__(self):
        self.engine = pyttsx3.init()
        # Configure voice settings
        self.engine.setProperty('rate', 150)  # Speed: 150 words per minute
        self.engine.setProperty('volume', 0.8)  # Volume: 80%
        self.narration_thread = None
    
    def narrate(self, text: str, blocking: bool = False):
        """
        Narrate text using text-to-speech.
        
        Args:
            text: Text to narrate
            blocking: If True, waits for narration to complete. If False, runs in background.
        """
        if not text or not text.strip():
            return
        
        try:
            if blocking:
                # Run synchronously
                self.engine.say(text)
                self.engine.runAndWait()
                logger.info(f"Narrated: {text[:50]}...")
            else:
                # Run in background thread
                if self.narration_thread and self.narration_thread.is_alive():
                    # Don't interrupt ongoing narration
                    logger.debug("Narration already in progress, skipping")
                    return
                
                self.narration_thread = threading.Thread(
                    target=self._narrate_async,
                    args=(text,),
                    daemon=True
                )
                self.narration_thread.start()
        except Exception as e:
            logger.error(f"Error narrating text: {e}")
    
    def _narrate_async(self, text: str):
        """Internal method for async narration"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            logger.info(f"Narrated (async): {text[:50]}...")
        except Exception as e:
            logger.error(f"Error in async narration: {e}")
    
    def stop(self):
        """Stop any ongoing narration"""
        try:
            self.engine.stop()
            logger.info("Narration stopped")
        except Exception as e:
            logger.error(f"Error stopping narration: {e}")
    
    def set_rate(self, rate: int):
        """Set speaking rate (words per minute)"""
        try:
            self.engine.setProperty('rate', rate)
            logger.info(f"Narration rate set to {rate} wpm")
        except Exception as e:
            logger.error(f"Error setting narration rate: {e}")
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        try:
            volume = max(0.0, min(1.0, volume))
            self.engine.setProperty('volume', volume)
            logger.info(f"Narration volume set to {volume}")
        except Exception as e:
            logger.error(f"Error setting narration volume: {e}")

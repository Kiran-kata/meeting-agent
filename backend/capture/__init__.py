"""
Capture Module - Screen capture and OCR components
"""
from .screen_capture import ScreenCapture, CaptureRegion, ScreenFrame, HotkeyManager
from .ocr_processor import OCRProcessor, OCRResult, CodeDetector
from .context_buffer import ContextBuffer, ContextEntry, ConflictResolver

__all__ = [
    'ScreenCapture', 'CaptureRegion', 'ScreenFrame', 'HotkeyManager',
    'OCRProcessor', 'OCRResult', 'CodeDetector',
    'ContextBuffer', 'ContextEntry', 'ConflictResolver'
]

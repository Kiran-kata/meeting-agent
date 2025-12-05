import mss
from PIL import Image
import pytesseract
import pygetwindow as gw
import logging

from .config import TESSERACT_PATH

logger = logging.getLogger(__name__)
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def get_active_window_bbox() -> tuple:
    """
    Get the bounding box (x, y, width, height) of the active window.
    
    Returns:
        Tuple of (x, y, width, height) or None if unable to get active window.
    """
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            x, y, right, bottom = active_window.left, active_window.top, active_window.right, active_window.bottom
            width = right - x
            height = bottom - y
            return {"left": x, "top": y, "width": width, "height": height}
        return None
    except Exception as e:
        logger.warning(f"Could not get active window: {e}. Falling back to primary monitor.")
        return None


def capture_screen_image(active_window_only: bool = True) -> Image.Image:
    """
    Capture screen as a PIL image.
    
    Args:
        active_window_only: If True, capture only the active window. If False, capture primary monitor.
    
    Returns:
        PIL Image object.
    """
    with mss.mss() as sct:
        if active_window_only:
            bbox = get_active_window_bbox()
            if bbox:
                shot = sct.grab(bbox)
                img = Image.frombytes("RGB", shot.size, shot.rgb)
                logger.info("Captured active window")
                return img
            else:
                logger.warning("Active window bbox unavailable, falling back to primary monitor.")
        
        # Fallback to primary monitor
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.rgb)
        logger.info("Captured primary monitor")
        return img


def capture_screen_text(active_window_only: bool = True) -> str:
    """
    Capture screen text using OCR.
    
    Args:
        active_window_only: If True, extract text from active window only.
    
    Returns:
        Extracted text string.
    """
    try:
        img = capture_screen_image(active_window_only=active_window_only)
        text = pytesseract.image_to_string(img)
        logger.info(f"Extracted {len(text)} characters from screen")
        return text
    except Exception as e:
        logger.error(f"Error extracting screen text: {e}")
        return ""

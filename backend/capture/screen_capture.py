"""
Screen Capture Module - Cross-platform screen capture with privacy controls
Captures entire screen at configurable FPS for real-time context detection.
"""
import logging
import threading
import queue
import time
from typing import Optional, Callable, Tuple, List
from dataclasses import dataclass
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Try to import mss (preferred) or fall back to pyautogui
try:
    import mss
    CAPTURE_METHOD = "mss"
except ImportError:
    try:
        import pyautogui
        CAPTURE_METHOD = "pyautogui"
    except ImportError:
        CAPTURE_METHOD = None
        logger.error("No screen capture library available. Install mss or pyautogui.")


@dataclass
class CaptureRegion:
    """Defines a screen capture region."""
    x: int = 0
    y: int = 0
    width: int = 0  # 0 = full screen
    height: int = 0  # 0 = full screen
    monitor: int = 1  # Monitor index (1 = primary)


@dataclass  
class ScreenFrame:
    """A captured screen frame with metadata."""
    image: Image.Image
    timestamp: float
    region: CaptureRegion
    frame_id: int


class ScreenCapture:
    """
    High-performance screen capture with privacy controls.
    Supports Windows, Mac, and Linux.
    """
    
    def __init__(
        self,
        fps: float = 1.0,
        region: Optional[CaptureRegion] = None,
        max_queue_size: int = 10
    ):
        """
        Initialize screen capture.
        
        Args:
            fps: Frames per second (1-2 recommended)
            region: Capture region (None = full screen)
            max_queue_size: Max frames to buffer
        """
        self.fps = fps
        self.interval = 1.0 / fps
        self.region = region or CaptureRegion()
        self.max_queue_size = max_queue_size
        
        self.frame_queue: queue.Queue[ScreenFrame] = queue.Queue(maxsize=max_queue_size)
        self.running = False
        self.paused = False
        self.capture_thread: Optional[threading.Thread] = None
        self.frame_counter = 0
        
        # Privacy filters
        self.excluded_regions: List[Tuple[int, int, int, int]] = []  # (x, y, w, h)
        
        # Callbacks
        self.on_frame: Optional[Callable[[ScreenFrame], None]] = None
        
        if CAPTURE_METHOD is None:
            raise RuntimeError("No screen capture library available")
        
        logger.info(f"Screen capture initialized with {CAPTURE_METHOD}, {fps} FPS")
    
    def start(self, on_frame: Optional[Callable[[ScreenFrame], None]] = None):
        """Start capturing screen."""
        self.on_frame = on_frame
        self.running = True
        self.paused = False
        
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("Screen capture started")
    
    def stop(self):
        """Stop capturing."""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        logger.info("Screen capture stopped")
    
    def pause(self):
        """Pause capturing (privacy control)."""
        self.paused = True
        logger.info("Screen capture paused")
    
    def resume(self):
        """Resume capturing."""
        self.paused = False
        logger.info("Screen capture resumed")
    
    def add_excluded_region(self, x: int, y: int, width: int, height: int):
        """Add a region to exclude from capture (privacy filter)."""
        self.excluded_regions.append((x, y, width, height))
        logger.info(f"Added excluded region: ({x}, {y}, {width}, {height})")
    
    def clear_excluded_regions(self):
        """Clear all excluded regions."""
        self.excluded_regions = []
    
    def _capture_loop(self):
        """Main capture loop."""
        if CAPTURE_METHOD == "mss":
            self._capture_loop_mss()
        else:
            self._capture_loop_pyautogui()
    
    def _capture_loop_mss(self):
        """Capture using mss (faster)."""
        with mss.mss() as sct:
            # Get monitor info
            monitor = sct.monitors[self.region.monitor]
            
            # Build capture area
            if self.region.width > 0 and self.region.height > 0:
                capture_area = {
                    "left": self.region.x,
                    "top": self.region.y,
                    "width": self.region.width,
                    "height": self.region.height
                }
            else:
                capture_area = monitor
            
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                start_time = time.time()
                
                try:
                    # Capture screen
                    screenshot = sct.grab(capture_area)
                    
                    # Convert to PIL Image
                    img = Image.frombytes(
                        "RGB",
                        (screenshot.width, screenshot.height),
                        screenshot.rgb
                    )
                    
                    # Apply privacy filters
                    img = self._apply_privacy_filters(img)
                    
                    # Create frame
                    self.frame_counter += 1
                    frame = ScreenFrame(
                        image=img,
                        timestamp=time.time(),
                        region=self.region,
                        frame_id=self.frame_counter
                    )
                    
                    # Add to queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait(frame)
                    except queue.Full:
                        # Drop oldest frame
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame)
                        except:
                            pass
                    
                    # Call callback
                    if self.on_frame:
                        self.on_frame(frame)
                    
                except Exception as e:
                    logger.error(f"Capture error: {e}")
                
                # Maintain FPS
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)
                time.sleep(sleep_time)
    
    def _capture_loop_pyautogui(self):
        """Capture using pyautogui (fallback)."""
        import pyautogui
        
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue
            
            start_time = time.time()
            
            try:
                # Capture screen
                if self.region.width > 0 and self.region.height > 0:
                    screenshot = pyautogui.screenshot(
                        region=(
                            self.region.x,
                            self.region.y,
                            self.region.width,
                            self.region.height
                        )
                    )
                else:
                    screenshot = pyautogui.screenshot()
                
                # Apply privacy filters
                img = self._apply_privacy_filters(screenshot)
                
                # Create frame
                self.frame_counter += 1
                frame = ScreenFrame(
                    image=img,
                    timestamp=time.time(),
                    region=self.region,
                    frame_id=self.frame_counter
                )
                
                # Add to queue
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except:
                        pass
                
                if self.on_frame:
                    self.on_frame(frame)
                    
            except Exception as e:
                logger.error(f"Capture error: {e}")
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            time.sleep(sleep_time)
    
    def _apply_privacy_filters(self, img: Image.Image) -> Image.Image:
        """Apply privacy filters by blacking out excluded regions."""
        if not self.excluded_regions:
            return img
        
        from PIL import ImageDraw
        
        draw = ImageDraw.Draw(img)
        for (x, y, w, h) in self.excluded_regions:
            draw.rectangle([x, y, x + w, y + h], fill="black")
        
        return img
    
    def get_latest_frame(self) -> Optional[ScreenFrame]:
        """Get the most recent frame without blocking."""
        frame = None
        while not self.frame_queue.empty():
            try:
                frame = self.frame_queue.get_nowait()
            except queue.Empty:
                break
        return frame
    
    def capture_frame(self) -> Optional[ScreenFrame]:
        """Capture a single frame synchronously (for on-demand capture)."""
        try:
            if CAPTURE_METHOD == "mss":
                with mss.mss() as sct:
                    monitor = sct.monitors[self.region.monitor]
                    
                    if self.region.width > 0 and self.region.height > 0:
                        capture_area = {
                            "left": self.region.x,
                            "top": self.region.y,
                            "width": self.region.width,
                            "height": self.region.height
                        }
                    else:
                        capture_area = monitor
                    
                    screenshot = sct.grab(capture_area)
                    img = Image.frombytes(
                        "RGB",
                        (screenshot.width, screenshot.height),
                        screenshot.rgb
                    )
            else:
                import pyautogui
                if self.region.width > 0 and self.region.height > 0:
                    img = pyautogui.screenshot(
                        region=(self.region.x, self.region.y, 
                               self.region.width, self.region.height)
                    )
                else:
                    img = pyautogui.screenshot()
            
            # Apply privacy filters
            img = self._apply_privacy_filters(img)
            
            self.frame_counter += 1
            return ScreenFrame(
                image=img,
                timestamp=time.time(),
                region=self.region,
                frame_id=self.frame_counter
            )
            
        except Exception as e:
            logger.error(f"Single capture error: {e}")
            return None
    
    def get_frame_bytes(self, frame: ScreenFrame, format: str = "PNG") -> bytes:
        """Convert frame to bytes for transmission."""
        buffer = io.BytesIO()
        frame.image.save(buffer, format=format)
        return buffer.getvalue()


# Hotkey support for pause/resume
class HotkeyManager:
    """Manage hotkeys for screen capture control."""
    
    def __init__(self, capture: ScreenCapture):
        self.capture = capture
        self.listener = None
    
    def start(self, pause_key: str = "f9", stop_key: str = "f10"):
        """Start listening for hotkeys."""
        try:
            from pynput import keyboard
            
            def on_press(key):
                try:
                    if hasattr(key, 'name'):
                        if key.name == pause_key:
                            if self.capture.paused:
                                self.capture.resume()
                            else:
                                self.capture.pause()
                        elif key.name == stop_key:
                            self.capture.stop()
                except Exception as e:
                    logger.error(f"Hotkey error: {e}")
            
            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            logger.info(f"Hotkeys enabled: {pause_key}=pause/resume, {stop_key}=stop")
            
        except ImportError:
            logger.warning("pynput not installed - hotkeys disabled")
    
    def stop(self):
        """Stop hotkey listener."""
        if self.listener:
            self.listener.stop()

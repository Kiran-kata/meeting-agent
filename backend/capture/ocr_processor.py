"""
OCR Processor - GPU-accelerated text extraction from screen captures
Supports Tesseract and PaddleOCR for high-accuracy text recognition.
"""
import logging
import threading
import queue
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from PIL import Image
import time

logger = logging.getLogger(__name__)

# Try to import OCR engines
OCR_ENGINE = None

try:
    import pytesseract
    OCR_ENGINE = "tesseract"
except ImportError:
    pass

if OCR_ENGINE is None:
    try:
        from paddleocr import PaddleOCR
        OCR_ENGINE = "paddle"
    except ImportError:
        pass

if OCR_ENGINE is None:
    try:
        import easyocr
        OCR_ENGINE = "easyocr"
    except ImportError:
        logger.warning("No OCR engine available. Install pytesseract, paddleocr, or easyocr.")


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    regions: List[Dict]  # List of {text, bbox, confidence}
    timestamp: float
    frame_id: int
    processing_time: float


class OCRProcessor:
    """
    GPU-accelerated OCR processor for screen captures.
    Automatically detects and uses best available engine.
    """
    
    def __init__(
        self,
        engine: Optional[str] = None,
        language: str = "en",
        gpu: bool = True
    ):
        """
        Initialize OCR processor.
        
        Args:
            engine: OCR engine ('tesseract', 'paddle', 'easyocr', or None for auto)
            language: Language code
            gpu: Use GPU acceleration if available
        """
        self.engine_name = engine or OCR_ENGINE
        self.language = language
        self.use_gpu = gpu
        
        self.engine = None
        self._init_engine()
        
        # Processing queue
        self.input_queue: queue.Queue = queue.Queue(maxsize=5)
        self.output_queue: queue.Queue = queue.Queue(maxsize=10)
        
        self.running = False
        self.process_thread: Optional[threading.Thread] = None
        
        logger.info(f"OCR initialized with {self.engine_name}, GPU={gpu}")
    
    def _init_engine(self):
        """Initialize the OCR engine."""
        if self.engine_name == "tesseract":
            # Tesseract uses pytesseract wrapper
            import pytesseract
            
            # Set Tesseract path for Windows
            import os
            if os.name == 'nt':  # Windows
                # Try common installation paths
                possible_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    r"C:\Users\kiran\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"Tesseract found at: {path}")
                        break
                else:
                    logger.warning("Tesseract not found in standard paths. Make sure it's in PATH.")
            
            self.engine = pytesseract
            
        elif self.engine_name == "paddle":
            from paddleocr import PaddleOCR
            self.engine = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                use_gpu=self.use_gpu,
                show_log=False
            )
            
        elif self.engine_name == "easyocr":
            import easyocr
            self.engine = easyocr.Reader(
                ['en'],
                gpu=self.use_gpu,
                verbose=False
            )
        else:
            raise RuntimeError(f"Unknown OCR engine: {self.engine_name}")
    
    def start(self):
        """Start background OCR processing."""
        self.running = True
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        logger.info("OCR processor started")
    
    def stop(self):
        """Stop OCR processing."""
        self.running = False
        if self.process_thread:
            self.process_thread.join(timeout=2)
        logger.info("OCR processor stopped")
    
    def process_image(self, image: Image.Image, frame_id: int = 0) -> OCRResult:
        """
        Process a single image synchronously.
        
        Args:
            image: PIL Image to process
            frame_id: Optional frame identifier
            
        Returns:
            OCRResult with extracted text
        """
        start_time = time.time()
        
        if self.engine_name == "tesseract":
            result = self._process_tesseract(image)
        elif self.engine_name == "paddle":
            result = self._process_paddle(image)
        elif self.engine_name == "easyocr":
            result = self._process_easyocr(image)
        else:
            result = {"text": "", "regions": [], "confidence": 0.0}
        
        processing_time = time.time() - start_time
        
        return OCRResult(
            text=result["text"],
            confidence=result["confidence"],
            regions=result["regions"],
            timestamp=time.time(),
            frame_id=frame_id,
            processing_time=processing_time
        )
    
    def _process_tesseract(self, image: Image.Image) -> Dict:
        """Process with Tesseract."""
        import pytesseract
        
        # Get detailed data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        regions = []
        full_text = []
        confidences = []
        
        for i, text in enumerate(data['text']):
            if text.strip():
                conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
                if conf > 30:  # Filter low confidence
                    regions.append({
                        "text": text,
                        "bbox": (
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        ),
                        "confidence": conf / 100.0
                    })
                    full_text.append(text)
                    confidences.append(conf)
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "text": " ".join(full_text),
            "regions": regions,
            "confidence": avg_conf / 100.0
        }
    
    def _process_paddle(self, image: Image.Image) -> Dict:
        """Process with PaddleOCR."""
        import numpy as np
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Run OCR
        result = self.engine.ocr(img_array, cls=True)
        
        regions = []
        full_text = []
        confidences = []
        
        if result and result[0]:
            for line in result[0]:
                bbox, (text, conf) = line
                regions.append({
                    "text": text,
                    "bbox": bbox,
                    "confidence": conf
                })
                full_text.append(text)
                confidences.append(conf)
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "text": " ".join(full_text),
            "regions": regions,
            "confidence": avg_conf
        }
    
    def _process_easyocr(self, image: Image.Image) -> Dict:
        """Process with EasyOCR."""
        import numpy as np
        
        img_array = np.array(image)
        result = self.engine.readtext(img_array)
        
        regions = []
        full_text = []
        confidences = []
        
        for (bbox, text, conf) in result:
            regions.append({
                "text": text,
                "bbox": bbox,
                "confidence": conf
            })
            full_text.append(text)
            confidences.append(conf)
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "text": " ".join(full_text),
            "regions": regions,
            "confidence": avg_conf
        }
    
    def queue_image(self, image: Image.Image, frame_id: int = 0):
        """Add image to processing queue."""
        try:
            self.input_queue.put_nowait((image, frame_id))
        except queue.Full:
            # Drop oldest
            try:
                self.input_queue.get_nowait()
                self.input_queue.put_nowait((image, frame_id))
            except:
                pass
    
    def get_result(self, timeout: float = 0.1) -> Optional[OCRResult]:
        """Get next OCR result from queue."""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _process_loop(self):
        """Background processing loop."""
        while self.running:
            try:
                image, frame_id = self.input_queue.get(timeout=0.5)
                result = self.process_image(image, frame_id)
                
                try:
                    self.output_queue.put_nowait(result)
                except queue.Full:
                    try:
                        self.output_queue.get_nowait()
                        self.output_queue.put_nowait(result)
                    except:
                        pass
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"OCR processing error: {e}")


class CodeDetector:
    """Detect and extract code from OCR text."""
    
    # Code indicators
    CODE_PATTERNS = [
        "def ", "class ", "import ", "from ", "return ",  # Python
        "function ", "const ", "let ", "var ", "=>",  # JavaScript
        "public ", "private ", "void ", "int ", "String ",  # Java
        "func ", "package ", "type ",  # Go
        "#include", "std::", "int main",  # C/C++
        "SELECT ", "FROM ", "WHERE ", "INSERT ",  # SQL
    ]
    
    # Syntax characters common in code
    CODE_CHARS = ["{", "}", "()", "[];", "=>", "->", "::", "//", "/*", "*/"]
    
    @classmethod
    def is_code(cls, text: str) -> bool:
        """Check if text appears to be code."""
        text_upper = text.upper()
        
        # Check for code patterns
        for pattern in cls.CODE_PATTERNS:
            if pattern.upper() in text_upper:
                return True
        
        # Check for syntax characters
        code_char_count = sum(1 for char in cls.CODE_CHARS if char in text)
        if code_char_count >= 2:
            return True
        
        # Check for indentation patterns
        lines = text.split('\n')
        indented_lines = sum(1 for line in lines if line.startswith('    ') or line.startswith('\t'))
        if indented_lines >= 3:
            return True
        
        return False
    
    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect programming language from code text."""
        text_lower = text.lower()
        
        # Language detection patterns
        patterns = {
            "python": ["def ", "import ", "from ", "print(", "__init__", "self."],
            "javascript": ["function ", "const ", "let ", "var ", "=>", "console.log"],
            "java": ["public class", "public static", "System.out", "void main"],
            "cpp": ["#include", "std::", "cout", "cin", "int main"],
            "go": ["func ", "package ", "fmt.", "import ("],
            "sql": ["select ", "from ", "where ", "insert ", "update "],
            "html": ["<html", "<div", "<script", "</"],
            "css": ["{", "}", "color:", "margin:", "padding:"],
        }
        
        scores = {}
        for lang, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "unknown"
    
    @classmethod
    def extract_code_blocks(cls, text: str) -> List[Dict]:
        """Extract code blocks from text."""
        blocks = []
        lines = text.split('\n')
        
        current_block = []
        in_code = False
        
        for line in lines:
            is_code_line = (
                line.startswith('    ') or
                line.startswith('\t') or
                any(p in line for p in cls.CODE_PATTERNS[:5])
            )
            
            if is_code_line:
                if not in_code:
                    in_code = True
                    current_block = []
                current_block.append(line)
            else:
                if in_code and current_block:
                    code_text = '\n'.join(current_block)
                    blocks.append({
                        "code": code_text,
                        "language": cls.detect_language(code_text)
                    })
                    current_block = []
                in_code = False
        
        # Don't forget last block
        if current_block:
            code_text = '\n'.join(current_block)
            blocks.append({
                "code": code_text,
                "language": cls.detect_language(code_text)
            })
        
        return blocks

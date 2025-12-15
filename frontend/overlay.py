"""
Stealth Overlay - PyQt6 UI with screen capture protection
"""
import ctypes
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QFont

from config import WINDOW_WIDTH, WINDOW_HEIGHT, STEALTH_MODE, ROLE_TEMPLATES

logger = logging.getLogger(__name__)


class StealthOverlay(QWidget):
    """
    Stealth overlay window - invisible to screen sharing.
    Clean, minimal UI for interview assistance.
    """
    
    # Signals
    start_requested = pyqtSignal()
    resume_selected = pyqtSignal(str)
    role_changed = pyqtSignal(str)
    close_requested = pyqtSignal()
    
    # Thread-safe UI update signals
    question_detected = pyqtSignal(str)  # For showing questions
    answer_chunk_ready = pyqtSignal(str)  # For appending answer chunks
    score_ready = pyqtSignal(int, str)  # For showing scores
    transcript_line_ready = pyqtSignal(str, str)  # speaker, text
    screen_indicator_changed = pyqtSignal(bool)  # show/hide screen detection
    
    def __init__(self):
        super().__init__()
        
        # Window flags for always-on-top, frameless, tool window
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.move(20, 20)
        
        # State
        self.drag_position = QPoint()
        self.is_recording = False
        self.stealth_active = False
        self.transcript_lines = []  # Store transcript history
        self.screen_detected = False
        self.opacity_level = 0.85
        self.font_size = 11
        
        self._setup_ui()
        self._connect_internal_signals()
        
    def _connect_internal_signals(self):
        """Connect internal signals for thread-safe UI updates."""
        self.question_detected.connect(self._show_question_ui)
        self.answer_chunk_ready.connect(self._append_answer_ui)
        self.score_ready.connect(self._show_score_ui)
        self.transcript_line_ready.connect(self._add_transcript_line_ui)
        self.screen_indicator_changed.connect(self._update_screen_indicator_ui)
        
    def _setup_ui(self):
        """Build the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Content area
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setFont(QFont("Consolas", 11))
        self.content.setStyleSheet("""
            QTextEdit {
                background: rgba(10, 10, 15, 0.15);
                color: #ffffff;
                border: none;
                padding: 12px;
                selection-background-color: rgba(255, 255, 255, 0.2);
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.content)
        
        # Controls
        controls = self._create_controls()
        main_layout.addWidget(controls)
        
        # Status bar
        status = self._create_status_bar()
        main_layout.addWidget(status)
    
    def _create_header(self) -> QWidget:
        """Create header with title and close button."""
        header = QWidget()
        header.setStyleSheet("background: rgba(25, 25, 35, 0.88);")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 8, 8)
        
        # Title
        title = QLabel("Interview Assistant")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setCursor(Qt.CursorShape.OpenHandCursor)
        layout.addWidget(title)
        
        # Screen detection indicator
        self.screen_indicator = QLabel("")
        self.screen_indicator.setFont(QFont("Segoe UI", 10))
        self.screen_indicator.setStyleSheet("color: #00ffcc; padding: 0 8px;")
        self.screen_indicator.setVisible(False)
        layout.addWidget(self.screen_indicator)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255,100,100,0.5); }
        """)
        close_btn.clicked.connect(self.close_requested.emit)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return header
    
    def _create_controls(self) -> QWidget:
        """Create control buttons."""
        controls = QWidget()
        controls.setStyleSheet("background: rgba(20, 20, 30, 0.88);")
        
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Resume button
        self.resume_btn = QPushButton("📄 Resume")
        self.resume_btn.setFixedHeight(32)
        self.resume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.resume_btn.setStyleSheet(self._button_style("#0066cc"))
        self.resume_btn.clicked.connect(self._on_resume_click)
        layout.addWidget(self.resume_btn)
        
        # Role selector
        self.role_selector = QComboBox()
        self.role_selector.addItems(list(ROLE_TEMPLATES.keys()))
        self.role_selector.setFixedHeight(32)
        self.role_selector.setStyleSheet("""
            QComboBox {
                background: rgba(60, 60, 80, 0.9);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; }
        """)
        self.role_selector.currentTextChanged.connect(self.role_changed.emit)
        layout.addWidget(self.role_selector)
        
        # Start button
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFixedHeight(32)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet(self._button_style("#22aa44"))
        self.start_btn.clicked.connect(self._on_start_click)
        layout.addWidget(self.start_btn)
        
        layout.addStretch()
        
        return controls
    
    def _create_status_bar(self) -> QWidget:
        """Create status bar."""
        status = QWidget()
        status.setStyleSheet("background: rgba(15, 15, 25, 0.88);")
        
        layout = QHBoxLayout(status)
        layout.setContentsMargins(12, 4, 12, 4)
        
        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #888; font-size: 8px;")
        layout.addWidget(self.status_dot)
        
        self.status_text = QLabel("Ready")
        self.status_text.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
        
        # Stealth indicator
        self.stealth_label = QLabel("🔒 Stealth")
        self.stealth_label.setStyleSheet("color: #ff9500; font-size: 11px;")
        self.stealth_label.setVisible(False)
        layout.addWidget(self.stealth_label)
        
        return status
    
    def _button_style(self, color: str) -> str:
        """Generate button stylesheet."""
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {color}dd; }}
            QPushButton:pressed {{ background: {color}bb; }}
            QPushButton:disabled {{ background: {color}66; color: #888; }}
        """
    
    def _on_resume_click(self):
        """Handle resume button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Resume PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.resume_selected.emit(file_path)
            self.show_message(f"✓ Resume loaded")
    
    def _on_start_click(self):
        """Handle start button click."""
        self.is_recording = True
        self.start_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.role_selector.setEnabled(False)
        
        self.status_dot.setStyleSheet("color: #22aa44; font-size: 8px;")
        self.status_text.setText("Listening...")
        self.status_text.setStyleSheet("color: #22aa44; font-size: 11px;")
        
        self.content.clear()
        self.start_requested.emit()
    
    def show_message(self, message: str):
        """Display a message in the content area."""
        self.content.setPlainText(message)
    
    def add_transcript_line(self, speaker: str, text: str):
        """Add a transcript line - thread-safe."""
        self.transcript_line_ready.emit(speaker, text)
    
    def _add_transcript_line_ui(self, speaker: str, text: str):
        """Internal: Add transcript line to UI."""
        self.transcript_lines.append({"speaker": speaker, "text": text})
        
        # Keep only last 10 lines
        if len(self.transcript_lines) > 10:
            self.transcript_lines = self.transcript_lines[-10:]
        
        # Build transcript HTML
        html_lines = []
        for line in self.transcript_lines:
            if line["speaker"] == "INTERVIEWER":
                html_lines.append(
                    f'<div style="margin-bottom: 6px;">' +
                    f'<span style="color: #ffffff; font-weight: 600;">{line["speaker"]}:</span> ' +
                    f'<span style="color: #ffffff;">{line["text"]}</span>' +
                    f'</div>'
                )
            else:
                html_lines.append(
                    f'<div style="margin-bottom: 6px;">' +
                    f'<span style="color: #aaaaaa; font-weight: 400;">{line["speaker"]}:</span> ' +
                    f'<span style="color: #aaaaaa;">{line["text"]}</span>' +
                    f'</div>'
                )
        
        transcript_html = ''.join(html_lines)
        self.content.setHtml(f'<div style="font-size: {self.font_size}px;">{transcript_html}</div>')
    
    def set_screen_detected(self, detected: bool):
        """Show/hide screen detection indicator - thread-safe."""
        self.screen_indicator_changed.emit(detected)
    
    def _update_screen_indicator_ui(self, detected: bool):
        """Internal: Update screen indicator in UI."""
        self.screen_detected = detected
        if detected:
            self.screen_indicator.setText("📺 Screen text detected")
            self.screen_indicator.setVisible(True)
        else:
            self.screen_indicator.setVisible(False)
    
    def clear_transcript(self):
        """Clear transcript history."""
        self.transcript_lines = []
        self.content.clear()
    
    def adjust_opacity(self, increase: bool):
        """Adjust overlay opacity."""
        if increase:
            self.opacity_level = min(0.98, self.opacity_level + 0.05)
        else:
            self.opacity_level = max(0.10, self.opacity_level - 0.05)
        
        # Update stylesheet with new opacity
        self.content.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(10, 10, 15, {self.opacity_level * 0.2});
                color: #ffffff;
                border: none;
                padding: 12px;
                selection-background-color: rgba(255, 255, 255, 0.2);
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }}
        """)
    
    def adjust_font_size(self, increase: bool):
        """Adjust font size."""
        if increase:
            self.font_size = min(16, self.font_size + 1)
        else:
            self.font_size = max(8, self.font_size - 1)
        
        self.content.setFont(QFont("Consolas", self.font_size))
    
    def show_question(self, question: str):
        """Display detected question - can be called from any thread."""
        self.question_detected.emit(question)
    
    def _show_question_ui(self, question: str):
        """Internal: Display detected question in UI (main thread only)."""
        # Clear transcript and show question in coding-optimized layout
        self.content.clear()
        self.content.setHtml(f"""
            <div style="font-size: {self.font_size}px;">
            <p style="color: #ffcc00; font-weight: bold; margin-bottom: 8px;">📌 QUESTION:</p>
            <p style="color: #ffffff; margin-left: 10px; margin-bottom: 16px; line-height: 1.5;">{question}</p>
            <p style="color: #66ff66; font-weight: bold; margin-top: 12px;">💡 SUGGESTED ANSWER:</p>
            </div>
        """)
    
    def append_answer(self, chunk: str):
        """Append answer chunk (for streaming) - can be called from any thread."""
        self.answer_chunk_ready.emit(chunk)
    
    def _append_answer_ui(self, chunk: str):
        """Internal: Append answer chunk in UI (main thread only)."""
        cursor = self.content.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.content.setTextCursor(cursor)
        self.content.verticalScrollBar().setValue(
            self.content.verticalScrollBar().maximum()
        )
    
    def show_score(self, score: int, feedback: str):
        """Display score and feedback - can be called from any thread."""
        self.score_ready.emit(score, feedback)
    
    def _show_score_ui(self, score: int, feedback: str):
        """Internal: Display score in UI (main thread only)."""
        self.content.append(f"""
<br>
<div style="border-top: 1px solid rgba(255,255,255,0.2); margin-top: 12px; padding-top: 12px;">
<p style="color: #ffcc00; font-weight: bold;">📊 Score: {score}/100</p>
<p style="color: #cccccc; font-size: {self.font_size - 1}px; line-height: 1.4;">{feedback}</p>
</div>
        """)
    
    # --- Window Events ---
    
    def showEvent(self, event):
        """Enable stealth mode when shown."""
        super().showEvent(event)
        if STEALTH_MODE:
            QTimer.singleShot(100, self._enable_stealth)
    
    def _enable_stealth(self):
        """Enable stealth mode - hide from screen capture."""
        try:
            hwnd = int(self.winId())
            WDA_EXCLUDEFROMCAPTURE = 0x11
            result = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            
            if result:
                self.stealth_active = True
                self.stealth_label.setVisible(True)
                logger.info("Stealth mode enabled")
            else:
                logger.warning("Stealth mode not available")
        except Exception as e:
            logger.error(f"Stealth mode error: {e}")
    
    def mousePressEvent(self, event):
        """Handle window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

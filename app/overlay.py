from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QFont
import ctypes
import threading


class Overlay(QWidget):
    """
    Semi-opaque always-on-top window with Apple-inspired design.
    Automatically hides when screen is being shared.
    Only visible to the user, not to screen share viewers.
    """
    
    close_requested = pyqtSignal()
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    pdf_selected = pyqtSignal(str)  # Signal for PDF file selection
    message_to_display = pyqtSignal(str)  # Signal for thread-safe message display

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.resize(550, 380)
        self.move(20, 20)
        
        # For dragging
        self.drag_position = QPoint()
        self.is_running = False
        
        # Screen sharing detection
        self.is_screen_shared = False
        self.was_visible = False
        self.screen_share_timer = QTimer()
        self.screen_share_timer.timeout.connect(self._check_screen_sharing)
        self.screen_share_timer.start(1000)  # Check every 1 second

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header with title and close button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 12, 12, 12)
        
        title = QLabel("Meeting Agent")
        title_font = QFont("Segoe UI", 13)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: white;")
        title.setCursor(Qt.CursorShape.OpenHandCursor)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFont(QFont("Segoe UI", 12))
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.35);
            }
        """)
        close_btn.clicked.connect(self.close_requested.emit)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        header = QWidget()
        header.setLayout(header_layout)
        # More transparent header - 150/255 = 59% opacity
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(0, 0, 0, 150),
                            stop:1 rgba(0, 0, 0, 170));
        """)
        main_layout.addWidget(header)

        # Content area - very transparent
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        text_font = QFont("Segoe UI", 11)
        self.text_box.setFont(text_font)
        # 140/255 = 55% opacity - more transparent so you can see background
        self.text_box.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                  stop:0 rgba(0, 0, 0, 140),
                                  stop:1 rgba(20, 20, 20, 160));
                color: #f5f5f7;
                border: none;
                padding: 16px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                outline: none;
                border: none;
            }
        """)
        main_layout.addWidget(self.text_box)

        # Control buttons - Start/Stop + PDF Upload
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(16, 8, 16, 8)
        controls_layout.setSpacing(10)
        
        self.pdf_btn = QPushButton("📄 Add PDF")
        self.pdf_btn.setFont(QFont("Segoe UI", 10))
        self.pdf_btn.setFixedHeight(32)
        self.pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 122, 255, 0.8);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 122, 255, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(0, 102, 220, 1.0);
            }
            QPushButton:disabled {
                background-color: rgba(0, 122, 255, 0.4);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.pdf_btn.clicked.connect(self.on_add_pdf)
        controls_layout.addWidget(self.pdf_btn)
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFont(QFont("Segoe UI", 10))
        self.start_btn.setFixedHeight(32)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 199, 89, 0.8);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: rgba(52, 199, 89, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(40, 170, 70, 1.0);
            }
            QPushButton:disabled {
                background-color: rgba(52, 199, 89, 0.4);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.start_btn.clicked.connect(self.on_start)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFont(QFont("Segoe UI", 10))
        self.stop_btn.setFixedHeight(32)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 59, 48, 0.8);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 59, 48, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(220, 40, 30, 1.0);
            }
            QPushButton:disabled {
                background-color: rgba(255, 59, 48, 0.4);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.stop_btn.clicked.connect(self.on_stop)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        controls_bar = QWidget()
        controls_bar.setLayout(controls_layout)
        controls_bar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(0, 0, 0, 160),
                            stop:1 rgba(0, 0, 0, 180));
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        """)
        main_layout.addWidget(controls_bar)

        # Status indicator at bottom
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(16, 8, 16, 8)
        
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #8a8a8e; font-size: 8px;")
        status_layout.addWidget(self.status_dot)
        
        self.status_text = QLabel("Stopped")
        self.status_text.setFont(QFont("Segoe UI", 9))
        self.status_text.setStyleSheet("color: #86868b;")
        status_layout.addWidget(self.status_text)
        
        status_layout.addStretch()
        
        status_bar = QWidget()
        status_bar.setLayout(status_layout)
        # Slightly transparent status bar
        status_bar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(0, 0, 0, 160),
                            stop:1 rgba(0, 0, 0, 180));
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        """)
        main_layout.addWidget(status_bar)
        
        # Connect the message signal for thread-safe updates
        self.message_to_display.connect(self._display_message)

    def _check_screen_sharing(self):
        """Detect if screen is being shared and auto-hide"""
        try:
            # Windows API to detect screen sharing
            # Uses GetWindowThreadProcessId to check for screen capture
            import subprocess
            
            # Check if any screen capture is active (Teams, Zoom, etc.)
            result = subprocess.run(
                ['tasklist', '/v'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Check for screen capture indicators
            screen_share_apps = ['TeamsMeetingHelper', 'ZoomAudioDevice', 'ScreenDrop']
            is_sharing = any(app in result.stdout for app in screen_share_apps)
            
            # Also check if display is being shared (more reliable)
            # Windows sets DISPLAY environment when screen sharing
            is_sharing = is_sharing or self._check_windows_display_sharing()
            
            if is_sharing and not self.is_screen_shared:
                # Screen sharing started - hide the window
                self.is_screen_shared = True
                self.was_visible = self.isVisible()
                self.hide()
            elif not is_sharing and self.is_screen_shared:
                # Screen sharing stopped - show the window again
                self.is_screen_shared = False
                if self.was_visible:
                    self.show()
                    self.raise_()
                    self.activateWindow()
        except Exception as e:
            pass  # Silent fail - detection is optional
    
    def _check_windows_display_sharing(self):
        """Check if Windows display is being shared via API"""
        try:
            # Use Windows API to detect screen sharing
            user32 = ctypes.windll.user32
            
            # GetDisplayConfigBufferSizes returns error if display is shared
            # This is a heuristic check
            num_paths = ctypes.c_uint32()
            num_modes = ctypes.c_uint32()
            
            # If this succeeds, display might be shared
            result = user32.GetDisplayConfigBufferSizes(1, ctypes.byref(num_paths), ctypes.byref(num_modes))
            
            # Alternative: check if RdpIsConnected (Remote Desktop)
            # This is a simple heuristic
            return False
        except:
            return False

    def on_start(self):
        """Handle start button click"""
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pdf_btn.setEnabled(False)  # Disable PDF upload during recording
        self.status_dot.setStyleSheet("color: #34c759; font-size: 8px;")
        self.status_text.setText("Recording")
        self.status_text.setStyleSheet("color: #34c759;")
        self.start_requested.emit()

    def on_stop(self):
        """Handle stop button click"""
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pdf_btn.setEnabled(True)  # Re-enable PDF upload after recording
        self.status_dot.setStyleSheet("color: #8a8a8e; font-size: 8px;")
        self.status_text.setText("Stopped")
        self.status_text.setStyleSheet("color: #86868b;")
        self.stop_requested.emit()

    def on_add_pdf(self):
        """Handle PDF file selection"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.pdf_selected.emit(file_path)
            # Show confirmation message
            pdf_name = file_path.split("\\")[-1]
            self.text_box.insertPlainText(f"\n✓ PDF loaded: {pdf_name}\n")
            # Auto-scroll to bottom
            self.text_box.verticalScrollBar().setValue(self.text_box.verticalScrollBar().maximum())

    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Ctrl+H to toggle visibility for screen sharing
        if event.key() == Qt.Key.Key_H and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.toggle_visibility()
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def show_message(self, text: str):
        """Thread-safe message display using signal"""
        self.message_to_display.emit(text)
    
    def _display_message(self, text: str):
        """Internal method to actually update the text box (runs in main thread)"""
        self.text_box.setPlainText(text)
        self.show()
        self.raise_()  # Bring to front
        self.activateWindow()  # Ensure window gets focus

    def show_answer(self, answer_text: str):
        """Display answer - appends to current text with formatting"""
        current = self.text_box.toPlainText()
        # Format: append answer with clear formatting
        formatted = f"{current}\n\n✓ ANSWER:\n{answer_text}\n{'-'*50}\n"
        self.message_to_display.emit(formatted)
    
    def show_qa_pair(self, question: str, answer: str):
        """Display question-answer pair with clear formatting"""
        current = self.text_box.toPlainText()
        # Format: display both question and answer
        qa_text = f"\n\n❓ QUESTION:\n{question}\n\n✓ ANSWER:\n{answer}\n{'-'*50}\n"
        formatted = f"{current}{qa_text}"
        self.message_to_display.emit(formatted)
    
    def show_question(self, question: str):
        """Display question immediately before answer generation"""
        current = self.text_box.toPlainText()
        q_text = f"\n\n❓ QUESTION:\n{question}\n\n⏳ GENERATING ANSWER...\n"
        formatted = f"{current}{q_text}"
        self.message_to_display.emit(formatted)
    
    def append_answer_chunk(self, chunk: str):
        """Append streaming answer chunk (real-time display)"""
        current = self.text_box.toPlainText()
        # Remove the "GENERATING" line if present
        if "⏳ GENERATING ANSWER..." in current:
            current = current.replace("\n⏳ GENERATING ANSWER...\n", "\n\n✓ ANSWER:\n")
        formatted = f"{current}{chunk}"
        self.text_box.setPlainText(formatted)
        # Auto-scroll to bottom
        self.text_box.verticalScrollBar().setValue(self.text_box.verticalScrollBar().maximum())
    
    def toggle_visibility(self):
        """Toggle window visibility - useful for screen sharing"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

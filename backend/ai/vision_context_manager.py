"""
Vision Context Manager - Multi-modal merging of OCR + audio transcript + conversation history.
Implements context prioritization and conflict resolution.
"""
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from collections import deque
import re


class ContextSource(Enum):
    """Source types for context information."""
    SCREEN_OCR = "screen_ocr"
    AUDIO_TRANSCRIPT = "audio_transcript"
    CONVERSATION_HISTORY = "conversation_history"
    CODE_SNIPPET = "code_snippet"
    RESUME_DATA = "resume_data"


class ContextPriority(Enum):
    """Priority levels for context resolution."""
    CRITICAL = 5      # Screen content (highest - visual truth)
    HIGH = 4          # Current audio/speech
    MEDIUM = 3        # Recent conversation
    LOW = 2           # Historical context
    BACKGROUND = 1    # Resume/static data


@dataclass
class ContextItem:
    """Individual context item from any source."""
    source: ContextSource
    content: str
    timestamp: float
    priority: ContextPriority
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp
    
    @property
    def effective_priority(self) -> float:
        """Calculate effective priority based on age and confidence."""
        age_decay = max(0.5, 1.0 - (self.age_seconds / 60.0))  # Decay over 1 minute
        return self.priority.value * self.confidence * age_decay


@dataclass
class MergedContext:
    """Final merged context ready for LLM consumption."""
    primary_context: str
    supporting_context: List[str]
    detected_code: Optional[str]
    detected_language: Optional[str]
    question_type: str
    confidence: float
    sources_used: List[ContextSource]
    token_count: int


class VisionContextManager:
    """
    Multi-modal context manager that merges and prioritizes:
    - Screen OCR content (visual truth)
    - Audio transcripts (spoken questions)
    - Conversation history (context continuity)
    - Resume data (candidate background)
    
    Key rule: If screen information contradicts previous text, SCREEN WINS.
    """
    
    def __init__(self, max_context_items: int = 100, max_tokens: int = 8000):
        self.max_context_items = max_context_items
        self.max_tokens = max_tokens
        
        # Separate buffers for each source
        self._screen_buffer: deque = deque(maxlen=20)
        self._audio_buffer: deque = deque(maxlen=50)
        self._conversation_buffer: deque = deque(maxlen=30)
        self._static_context: Dict[str, ContextItem] = {}
        
        # Code detection patterns
        self._code_patterns = {
            'python': [r'def\s+\w+\s*\(', r'import\s+\w+', r'class\s+\w+:', r'print\s*\('],
            'javascript': [r'function\s+\w+', r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'=>', r'console\.log'],
            'java': [r'public\s+class', r'public\s+static\s+void', r'System\.out\.print'],
            'cpp': [r'#include\s*<', r'int\s+main\s*\(', r'std::', r'cout\s*<<'],
            'sql': [r'SELECT\s+', r'FROM\s+', r'WHERE\s+', r'INSERT\s+INTO', r'CREATE\s+TABLE']
        }
        
        # Question type patterns
        self._question_patterns = {
            'coding': [r'write\s+a?\s*(function|code|program)', r'implement', r'solve', r'algorithm'],
            'behavioral': [r'tell\s+me\s+about', r'describe\s+a\s+time', r'how\s+do\s+you', r'what\s+would\s+you'],
            'technical': [r'explain\s+how', r'what\s+is\s+the\s+difference', r'how\s+does\s+.*\s+work'],
            'system_design': [r'design\s+a?\s+system', r'architect', r'scale', r'database\s+schema']
        }
    
    def add_screen_context(self, text: str, confidence: float = 1.0, 
                          detected_code: Optional[str] = None,
                          detected_language: Optional[str] = None):
        """Add screen OCR content - highest priority."""
        item = ContextItem(
            source=ContextSource.SCREEN_OCR,
            content=text,
            timestamp=time.time(),
            priority=ContextPriority.CRITICAL,
            confidence=confidence,
            metadata={
                'detected_code': detected_code,
                'detected_language': detected_language
            }
        )
        self._screen_buffer.append(item)
    
    def add_audio_context(self, transcript: str, confidence: float = 0.9):
        """Add audio transcript - high priority."""
        item = ContextItem(
            source=ContextSource.AUDIO_TRANSCRIPT,
            content=transcript,
            timestamp=time.time(),
            priority=ContextPriority.HIGH,
            confidence=confidence
        )
        self._audio_buffer.append(item)
    
    def add_conversation_turn(self, role: str, content: str):
        """Add conversation history entry."""
        item = ContextItem(
            source=ContextSource.CONVERSATION_HISTORY,
            content=f"{role}: {content}",
            timestamp=time.time(),
            priority=ContextPriority.MEDIUM,
            metadata={'role': role}
        )
        self._conversation_buffer.append(item)
    
    def set_resume_context(self, resume_data: Dict[str, Any]):
        """Set static resume context."""
        content = self._format_resume_context(resume_data)
        self._static_context['resume'] = ContextItem(
            source=ContextSource.RESUME_DATA,
            content=content,
            timestamp=time.time(),
            priority=ContextPriority.BACKGROUND,
            metadata=resume_data
        )
    
    def _format_resume_context(self, resume_data: Dict[str, Any]) -> str:
        """Format resume data for context injection."""
        parts = []
        if resume_data.get('languages'):
            parts.append(f"Languages: {', '.join(resume_data['languages'])}")
        if resume_data.get('skills'):
            parts.append(f"Skills: {', '.join(resume_data['skills'][:10])}")
        if resume_data.get('experience'):
            parts.append(f"Experience: {resume_data['experience']}")
        return " | ".join(parts) if parts else ""
    
    def get_merged_context(self, question: Optional[str] = None) -> MergedContext:
        """
        Merge all context sources with proper prioritization.
        
        Priority Rules:
        1. Screen content is TRUTH (visual verification)
        2. Recent audio trumps older audio
        3. Conversation provides continuity
        4. Resume provides background knowledge
        """
        # Collect all items
        all_items: List[ContextItem] = []
        all_items.extend(self._screen_buffer)
        all_items.extend(self._audio_buffer)
        all_items.extend(self._conversation_buffer)
        all_items.extend(self._static_context.values())
        
        # Sort by effective priority
        all_items.sort(key=lambda x: x.effective_priority, reverse=True)
        
        # Detect question type
        question_type = self._detect_question_type(question) if question else "unknown"
        
        # Extract code if present
        detected_code, detected_language = self._extract_code_from_context(all_items)
        
        # Build merged context
        primary_parts = []
        supporting_parts = []
        sources_used = set()
        total_tokens = 0
        
        # Screen content first (TRUTH)
        for item in all_items:
            if item.source == ContextSource.SCREEN_OCR and item.age_seconds < 30:
                text = item.content.strip()
                if text and len(text) > 10:
                    tokens = len(text.split())
                    if total_tokens + tokens <= self.max_tokens:
                        primary_parts.append(f"[SCREEN] {text}")
                        sources_used.add(item.source)
                        total_tokens += tokens
        
        # Audio transcript
        for item in sorted([i for i in all_items if i.source == ContextSource.AUDIO_TRANSCRIPT],
                          key=lambda x: x.timestamp, reverse=True)[:5]:
            text = item.content.strip()
            if text:
                tokens = len(text.split())
                if total_tokens + tokens <= self.max_tokens:
                    supporting_parts.append(f"[HEARD] {text}")
                    sources_used.add(item.source)
                    total_tokens += tokens
        
        # Conversation history
        for item in sorted([i for i in all_items if i.source == ContextSource.CONVERSATION_HISTORY],
                          key=lambda x: x.timestamp, reverse=True)[:10]:
            text = item.content.strip()
            if text:
                tokens = len(text.split())
                if total_tokens + tokens <= self.max_tokens:
                    supporting_parts.append(text)
                    sources_used.add(item.source)
                    total_tokens += tokens
        
        # Resume context (if room)
        if 'resume' in self._static_context:
            resume_item = self._static_context['resume']
            tokens = len(resume_item.content.split())
            if total_tokens + tokens <= self.max_tokens:
                supporting_parts.append(f"[BACKGROUND] {resume_item.content}")
                sources_used.add(resume_item.source)
                total_tokens += tokens
        
        # Calculate overall confidence
        screen_items = [i for i in all_items if i.source == ContextSource.SCREEN_OCR and i.age_seconds < 30]
        confidence = max([i.confidence for i in screen_items]) if screen_items else 0.7
        
        return MergedContext(
            primary_context="\n".join(primary_parts),
            supporting_context=supporting_parts,
            detected_code=detected_code,
            detected_language=detected_language,
            question_type=question_type,
            confidence=confidence,
            sources_used=list(sources_used),
            token_count=total_tokens
        )
    
    def _detect_question_type(self, question: str) -> str:
        """Detect type of interview question."""
        question_lower = question.lower()
        
        for qtype, patterns in self._question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    return qtype
        
        return "general"
    
    def _extract_code_from_context(self, items: List[ContextItem]) -> tuple:
        """Extract code snippets and detect language from context."""
        code_blocks = []
        detected_language = None
        
        for item in items:
            # Check metadata for pre-detected code
            if item.metadata.get('detected_code'):
                code_blocks.append(item.metadata['detected_code'])
                if item.metadata.get('detected_language'):
                    detected_language = item.metadata['detected_language']
                continue
            
            # Try to detect code in content
            content = item.content
            
            # Look for code block markers
            code_match = re.search(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
            if code_match:
                lang = code_match.group(1)
                code = code_match.group(2)
                code_blocks.append(code)
                if lang:
                    detected_language = lang
                continue
            
            # Detect language from patterns
            for lang, patterns in self._code_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        detected_language = detected_language or lang
                        break
        
        combined_code = "\n\n".join(code_blocks) if code_blocks else None
        return combined_code, detected_language
    
    def resolve_conflict(self, screen_content: str, audio_content: str) -> str:
        """
        Resolve conflicts between screen and audio.
        RULE: Screen content WINS (visual truth).
        """
        # If screen clearly shows code/question, use screen
        if self._contains_code_or_question(screen_content):
            return screen_content
        
        # If audio provides additional context, merge
        if audio_content and not self._is_contradictory(screen_content, audio_content):
            return f"{screen_content}\n\nAdditional context: {audio_content}"
        
        # Default: trust screen
        return screen_content
    
    def _contains_code_or_question(self, text: str) -> bool:
        """Check if text contains code or interview question."""
        for patterns in self._code_patterns.values():
            for pattern in patterns:
                if re.search(pattern, text):
                    return True
        
        for patterns in self._question_patterns.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        
        return False
    
    def _is_contradictory(self, text1: str, text2: str) -> bool:
        """Check if two pieces of text contradict each other."""
        # Simple heuristic: check for negation or vastly different content
        negation_patterns = [r'\bnot\b', r'\bno\b', r"\bisn't\b", r"\bwasn't\b"]
        
        has_negation_1 = any(re.search(p, text1.lower()) for p in negation_patterns)
        has_negation_2 = any(re.search(p, text2.lower()) for p in negation_patterns)
        
        return has_negation_1 != has_negation_2
    
    def clear_old_context(self, max_age_seconds: float = 120.0):
        """Clear context older than specified age."""
        cutoff = time.time() - max_age_seconds
        
        self._screen_buffer = deque(
            [i for i in self._screen_buffer if i.timestamp > cutoff],
            maxlen=self._screen_buffer.maxlen
        )
        self._audio_buffer = deque(
            [i for i in self._audio_buffer if i.timestamp > cutoff],
            maxlen=self._audio_buffer.maxlen
        )
        self._conversation_buffer = deque(
            [i for i in self._conversation_buffer if i.timestamp > cutoff],
            maxlen=self._conversation_buffer.maxlen
        )
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about current context state."""
        return {
            'screen_items': len(self._screen_buffer),
            'audio_items': len(self._audio_buffer),
            'conversation_items': len(self._conversation_buffer),
            'static_items': len(self._static_context),
            'total_items': (len(self._screen_buffer) + len(self._audio_buffer) + 
                          len(self._conversation_buffer) + len(self._static_context))
        }


# Convenience function for creating pre-configured manager
def create_vision_context_manager(max_tokens: int = 8000) -> VisionContextManager:
    """Factory function to create a configured VisionContextManager."""
    return VisionContextManager(max_tokens=max_tokens)

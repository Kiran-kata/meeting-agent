"""
Context Buffer - Manages rolling context from multiple sources
Handles screen OCR, audio transcript, and conversation history.
"""
import logging
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """A single context entry from any source."""
    source: str  # 'screen', 'audio', 'qa'
    content: str
    timestamp: float
    priority: float = 1.0
    metadata: Dict = field(default_factory=dict)
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]


class ContextBuffer:
    """
    Rolling context buffer for multi-modal interview assistant.
    Manages context from screen, audio, and Q&A with smart truncation.
    """
    
    # Priority weights
    PRIORITY = {
        "screen": 1.5,      # Screen content is highest priority
        "audio": 1.2,       # Recent audio is important
        "qa": 1.0,          # Past Q&A for context
        "resume": 0.8,      # Resume context
    }
    
    # Token limits per source (approximate)
    TOKEN_LIMITS = {
        "screen": 1000,
        "audio": 500,
        "qa": 800,
        "resume": 400,
        "total": 3000,
    }
    
    def __init__(
        self,
        max_screen_entries: int = 10,
        max_audio_entries: int = 20,
        max_qa_entries: int = 10,
        dedup_threshold: float = 0.8
    ):
        """
        Initialize context buffer.
        
        Args:
            max_screen_entries: Max screen OCR entries to keep
            max_audio_entries: Max audio transcript chunks
            max_qa_entries: Max Q&A pairs to keep
            dedup_threshold: Similarity threshold for deduplication
        """
        self.screen_buffer: deque = deque(maxlen=max_screen_entries)
        self.audio_buffer: deque = deque(maxlen=max_audio_entries)
        self.qa_buffer: deque = deque(maxlen=max_qa_entries)
        self.resume_context: str = ""
        
        self.dedup_threshold = dedup_threshold
        self.lock = threading.Lock()
        
        # Track last seen content for deduplication
        self._last_screen_hash = ""
        self._last_audio_hash = ""
        
        logger.info("Context buffer initialized")
    
    def add_screen_context(self, text: str, metadata: Dict = None):
        """Add screen OCR text to buffer."""
        if not text or not text.strip():
            return
        
        # Skip if same as last screen
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        if content_hash == self._last_screen_hash:
            return
        
        self._last_screen_hash = content_hash
        
        entry = ContextEntry(
            source="screen",
            content=text.strip(),
            timestamp=datetime.now().timestamp(),
            priority=self.PRIORITY["screen"],
            metadata=metadata or {},
            content_hash=content_hash
        )
        
        with self.lock:
            self.screen_buffer.append(entry)
        
        logger.debug(f"Added screen context: {len(text)} chars")
    
    def add_audio_context(self, text: str, speaker: str = "unknown"):
        """Add audio transcript to buffer."""
        if not text or not text.strip():
            return
        
        # Skip duplicates
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        if content_hash == self._last_audio_hash:
            return
        
        self._last_audio_hash = content_hash
        
        entry = ContextEntry(
            source="audio",
            content=text.strip(),
            timestamp=datetime.now().timestamp(),
            priority=self.PRIORITY["audio"],
            metadata={"speaker": speaker},
            content_hash=content_hash
        )
        
        with self.lock:
            self.audio_buffer.append(entry)
        
        logger.debug(f"Added audio context: {len(text)} chars")
    
    def add_qa_pair(self, question: str, answer: str):
        """Add Q&A pair to buffer."""
        entry = ContextEntry(
            source="qa",
            content=f"Q: {question}\nA: {answer}",
            timestamp=datetime.now().timestamp(),
            priority=self.PRIORITY["qa"],
            metadata={"question": question, "answer": answer}
        )
        
        with self.lock:
            self.qa_buffer.append(entry)
        
        logger.debug("Added Q&A pair to context")
    
    def set_resume_context(self, text: str):
        """Set resume context."""
        self.resume_context = text[:self.TOKEN_LIMITS["resume"] * 4]  # ~4 chars per token
        logger.info(f"Resume context set: {len(self.resume_context)} chars")
    
    def get_merged_context(self, max_tokens: int = None) -> str:
        """
        Get merged context from all sources, prioritized and truncated.
        
        Args:
            max_tokens: Max approximate tokens (None = use default)
            
        Returns:
            Merged context string
        """
        max_tokens = max_tokens or self.TOKEN_LIMITS["total"]
        
        with self.lock:
            parts = []
            
            # Screen context (highest priority) - SCREEN WINS
            screen_text = self._get_recent_screen()
            if screen_text:
                parts.append(f"[SCREEN CONTENT - CURRENT]\n{screen_text}")
            
            # Audio context
            audio_text = self._get_recent_audio()
            if audio_text:
                parts.append(f"[RECENT CONVERSATION]\n{audio_text}")
            
            # Q&A history
            qa_text = self._get_qa_history()
            if qa_text:
                parts.append(f"[PREVIOUS Q&A]\n{qa_text}")
            
            # Resume context
            if self.resume_context:
                parts.append(f"[CANDIDATE BACKGROUND]\n{self.resume_context}")
        
        merged = "\n\n".join(parts)
        
        # Truncate if needed
        char_limit = max_tokens * 4  # Approximate 4 chars per token
        if len(merged) > char_limit:
            merged = merged[:char_limit] + "\n[...truncated]"
        
        return merged
    
    def _get_recent_screen(self) -> str:
        """Get recent screen content, deduplicated."""
        if not self.screen_buffer:
            return ""
        
        # Get most recent unique entries
        seen = set()
        texts = []
        
        for entry in reversed(self.screen_buffer):
            if entry.content_hash not in seen:
                seen.add(entry.content_hash)
                texts.append(entry.content)
            if len(texts) >= 3:  # Max 3 recent screen captures
                break
        
        return "\n---\n".join(reversed(texts))
    
    def _get_recent_audio(self) -> str:
        """Get recent audio transcript."""
        if not self.audio_buffer:
            return ""
        
        # Get last N entries
        recent = list(self.audio_buffer)[-5:]
        return " ".join(e.content for e in recent)
    
    def _get_qa_history(self) -> str:
        """Get Q&A history."""
        if not self.qa_buffer:
            return ""
        
        recent = list(self.qa_buffer)[-3:]
        return "\n\n".join(e.content for e in recent)
    
    def get_screen_for_conflict_check(self) -> str:
        """Get latest screen content for conflict resolution."""
        if self.screen_buffer:
            return list(self.screen_buffer)[-1].content
        return ""
    
    def clear(self):
        """Clear all buffers."""
        with self.lock:
            self.screen_buffer.clear()
            self.audio_buffer.clear()
            self.qa_buffer.clear()
        logger.info("Context buffer cleared")
    
    def get_stats(self) -> Dict:
        """Get buffer statistics."""
        return {
            "screen_entries": len(self.screen_buffer),
            "audio_entries": len(self.audio_buffer),
            "qa_entries": len(self.qa_buffer),
            "has_resume": bool(self.resume_context),
            "total_chars": (
                sum(len(e.content) for e in self.screen_buffer) +
                sum(len(e.content) for e in self.audio_buffer) +
                sum(len(e.content) for e in self.qa_buffer) +
                len(self.resume_context)
            )
        }


class ConflictResolver:
    """
    Resolves conflicts between different context sources.
    Rule: Screen content wins over audio when they contradict.
    """
    
    @staticmethod
    def resolve(
        screen_context: str,
        audio_context: str,
        question: str
    ) -> Tuple[str, str]:
        """
        Resolve conflicts between screen and audio context.
        
        Returns:
            (primary_context, conflict_note)
        """
        if not screen_context:
            return audio_context, ""
        
        if not audio_context:
            return screen_context, ""
        
        # Check for potential conflicts
        # If screen shows code/problem and audio mentions different problem
        screen_lower = screen_context.lower()
        audio_lower = audio_context.lower()
        
        # Keywords that indicate specific content
        specific_keywords = [
            "sort", "search", "tree", "graph", "array", "list",
            "binary", "merge", "quick", "heap", "stack", "queue",
            "linked", "hash", "dynamic", "greedy"
        ]
        
        screen_keywords = set(kw for kw in specific_keywords if kw in screen_lower)
        audio_keywords = set(kw for kw in specific_keywords if kw in audio_lower)
        
        if screen_keywords and audio_keywords:
            # Both have specific content
            if screen_keywords != audio_keywords:
                # Conflict detected - screen wins
                return (
                    screen_context,
                    f"Note: Screen shows different content. Prioritizing visible screen ({', '.join(screen_keywords)})"
                )
        
        # No conflict - combine
        return f"{screen_context}\n\n{audio_context}", ""
    
    @staticmethod
    def extract_problem_from_screen(screen_text: str) -> Optional[Dict]:
        """Extract coding problem details from screen text."""
        if not screen_text:
            return None
        
        # Look for common problem patterns
        problem_indicators = [
            "implement", "write", "create", "design", "build",
            "given", "input", "output", "example", "constraint"
        ]
        
        text_lower = screen_text.lower()
        
        # Check if this looks like a problem
        indicator_count = sum(1 for ind in problem_indicators if ind in text_lower)
        
        if indicator_count >= 2:
            return {
                "text": screen_text,
                "type": "coding_problem",
                "indicators_found": indicator_count
            }
        
        return None

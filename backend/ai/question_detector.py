"""
Question Detector - Automatic detection of coding questions from multiple sources.
Combines screen OCR, audio transcripts, and pattern matching for accurate detection.
"""
import re
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionCategory(Enum):
    """Categories of interview questions."""
    CODING_ALGORITHM = "coding_algorithm"
    DATA_STRUCTURE = "data_structure"
    SYSTEM_DESIGN = "system_design"
    SQL_DATABASE = "sql_database"
    BEHAVIORAL = "behavioral"
    TECHNICAL_CONCEPT = "technical_concept"
    DEBUGGING = "debugging"
    CODE_REVIEW = "code_review"
    UNKNOWN = "unknown"


class DifficultyLevel(Enum):
    """Difficulty level of the question."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


@dataclass
class DetectedQuestion:
    """A detected interview question with metadata."""
    text: str
    category: QuestionCategory
    difficulty: DifficultyLevel
    confidence: float
    source: str  # 'screen', 'audio', 'combined'
    timestamp: float
    keywords: List[str] = field(default_factory=list)
    expected_language: Optional[str] = None
    time_estimate_minutes: Optional[int] = None
    hints: List[str] = field(default_factory=list)
    
    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp


class QuestionDetector:
    """
    Automatic coding question detection system.
    
    Features:
    - Multi-source detection (screen + audio)
    - Category classification
    - Difficulty estimation
    - Language detection
    - Time estimation
    """
    
    # Coding question patterns by category
    CATEGORY_PATTERNS = {
        QuestionCategory.CODING_ALGORITHM: [
            r'(write|implement|create)\s+(a\s+)?(function|method|algorithm)',
            r'(find|return|calculate|compute)\s+the\s+',
            r'given\s+(an?\s+)?(array|string|list|number)',
            r'(reverse|sort|merge|search)\s+(a\s+)?(string|array|list)',
            r'(two sum|three sum|valid parentheses|palindrome)',
            r'(fibonacci|factorial|prime|binary search)',
        ],
        QuestionCategory.DATA_STRUCTURE: [
            r'implement\s+(a\s+)?(stack|queue|linked list|tree|graph|heap)',
            r'(design|create)\s+(a\s+)?(data structure)',
            r'(insert|delete|update|traverse)\s+(in|from|into)\s+(a\s+)?',
            r'(bst|binary search tree|trie|hash table)',
        ],
        QuestionCategory.SYSTEM_DESIGN: [
            r'design\s+(a\s+)?(system|service|api|database)',
            r'(architect|scale|design)\s+',
            r'how would you (build|design|architect)',
            r'(url shortener|twitter|facebook|uber|netflix)',
            r'(distributed|scalable|high availability)',
        ],
        QuestionCategory.SQL_DATABASE: [
            r'(write|create)\s+(a\s+)?(sql|query)',
            r'(select|join|group by|having|where)',
            r'(database|table|index|foreign key)',
            r'(normalize|denormalize|schema)',
        ],
        QuestionCategory.BEHAVIORAL: [
            r'tell me about a time',
            r'describe a situation',
            r'how (did|would) you handle',
            r'give (me\s+)?an example',
            r'what (is|was) your (biggest|greatest)',
            r'why (do you|did you|should we)',
        ],
        QuestionCategory.TECHNICAL_CONCEPT: [
            r'(explain|describe|what is)\s+(the\s+)?(difference|concept)',
            r'how does\s+\w+\s+work',
            r'what (is|are)\s+(the\s+)?(benefit|advantage|disadvantage)',
            r'(compare|contrast)\s+',
        ],
        QuestionCategory.DEBUGGING: [
            r'(find|fix|debug)\s+(the\s+)?(bug|error|issue)',
            r'what(\'s|\s+is)\s+wrong\s+with',
            r'why (is|does)\s+this\s+(code|function)',
        ],
        QuestionCategory.CODE_REVIEW: [
            r'(review|improve|optimize)\s+(this\s+)?(code|function)',
            r'what would you change',
            r'how can (we|you) (improve|make.*better)',
        ]
    }
    
    # Difficulty indicators
    DIFFICULTY_INDICATORS = {
        DifficultyLevel.EASY: [
            'simple', 'basic', 'easy', 'straightforward',
            'two sum', 'reverse', 'palindrome', 'fibonacci',
            'linear search', 'array sum'
        ],
        DifficultyLevel.MEDIUM: [
            'medium', 'moderate',
            'binary search', 'linked list', 'tree traversal',
            'dynamic programming', 'bfs', 'dfs', 'stack', 'queue'
        ],
        DifficultyLevel.HARD: [
            'hard', 'complex', 'advanced', 'challenging',
            'graph algorithm', 'shortest path', 'dp', 'optimization',
            'system design', 'distributed', 'concurrent'
        ]
    }
    
    # Language indicators
    LANGUAGE_INDICATORS = {
        'python': ['python', 'def ', 'import ', 'print(', '__init__'],
        'javascript': ['javascript', 'js', 'const ', 'let ', 'function ', '=>'],
        'java': ['java', 'public class', 'public static', 'System.out'],
        'cpp': ['c++', 'cpp', '#include', 'std::', 'cout'],
        'sql': ['sql', 'select ', 'from ', 'where ', 'join ']
    }
    
    # Time estimates by category and difficulty (in minutes)
    TIME_ESTIMATES = {
        (QuestionCategory.CODING_ALGORITHM, DifficultyLevel.EASY): 10,
        (QuestionCategory.CODING_ALGORITHM, DifficultyLevel.MEDIUM): 20,
        (QuestionCategory.CODING_ALGORITHM, DifficultyLevel.HARD): 45,
        (QuestionCategory.DATA_STRUCTURE, DifficultyLevel.EASY): 15,
        (QuestionCategory.DATA_STRUCTURE, DifficultyLevel.MEDIUM): 25,
        (QuestionCategory.DATA_STRUCTURE, DifficultyLevel.HARD): 45,
        (QuestionCategory.SYSTEM_DESIGN, DifficultyLevel.MEDIUM): 30,
        (QuestionCategory.SYSTEM_DESIGN, DifficultyLevel.HARD): 45,
        (QuestionCategory.SQL_DATABASE, DifficultyLevel.EASY): 10,
        (QuestionCategory.SQL_DATABASE, DifficultyLevel.MEDIUM): 15,
        (QuestionCategory.SQL_DATABASE, DifficultyLevel.HARD): 25,
    }
    
    def __init__(self):
        self._detected_questions: List[DetectedQuestion] = []
        self._seen_texts: set = set()  # Avoid duplicate detection
        
        logger.info("QuestionDetector initialized")
    
    def detect_from_text(self, text: str, source: str = "unknown") -> Optional[DetectedQuestion]:
        """
        Detect if text contains a coding question.
        
        Args:
            text: Text to analyze
            source: Source of text ('screen', 'audio', 'combined')
            
        Returns:
            DetectedQuestion if found, None otherwise
        """
        if not text or len(text.strip()) < 10:
            return None
        
        # Normalize text
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Check for duplicates (using first 100 chars as key)
        text_key = text_lower[:100]
        if text_key in self._seen_texts:
            return None
        
        # Detect category
        category, category_confidence = self._detect_category(text_lower)
        
        # Only proceed if we detect a question-like pattern
        if category == QuestionCategory.UNKNOWN and not self._is_question_like(text_lower):
            return None
        
        # Detect difficulty
        difficulty = self._detect_difficulty(text_lower)
        
        # Detect expected language
        language = self._detect_language(text_lower)
        
        # Extract keywords
        keywords = self._extract_keywords(text_lower)
        
        # Estimate time
        time_estimate = self.TIME_ESTIMATES.get(
            (category, difficulty),
            15  # Default 15 minutes
        )
        
        # Calculate overall confidence
        confidence = category_confidence
        if self._is_question_like(text_lower):
            confidence = min(1.0, confidence + 0.1)
        if len(keywords) >= 3:
            confidence = min(1.0, confidence + 0.1)
        
        # Generate hints
        hints = self._generate_hints(category, keywords)
        
        # Create result
        question = DetectedQuestion(
            text=text_clean,
            category=category,
            difficulty=difficulty,
            confidence=confidence,
            source=source,
            timestamp=time.time(),
            keywords=keywords,
            expected_language=language,
            time_estimate_minutes=time_estimate,
            hints=hints
        )
        
        # Store for history
        self._detected_questions.append(question)
        self._seen_texts.add(text_key)
        
        logger.info(f"Detected question: {category.value} ({difficulty.value}) - confidence: {confidence:.2f}")
        
        return question
    
    def detect_from_screen_and_audio(self, 
                                     screen_text: Optional[str],
                                     audio_text: Optional[str]) -> Optional[DetectedQuestion]:
        """
        Detect questions by combining screen and audio sources.
        Screen content takes priority when both are available.
        """
        # Try screen first (visual truth)
        if screen_text:
            result = self.detect_from_text(screen_text, source="screen")
            if result and result.confidence > 0.6:
                return result
        
        # Try audio
        if audio_text:
            result = self.detect_from_text(audio_text, source="audio")
            if result and result.confidence > 0.6:
                return result
        
        # Try combined if both exist
        if screen_text and audio_text:
            combined = f"{screen_text}\n\nAdditional context: {audio_text}"
            result = self.detect_from_text(combined, source="combined")
            return result
        
        return None
    
    def _detect_category(self, text: str) -> Tuple[QuestionCategory, float]:
        """Detect the category of the question."""
        best_category = QuestionCategory.UNKNOWN
        best_score = 0.0
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    score += 1.0 / len(patterns)
            
            if matches > 0 and score > best_score:
                best_score = score
                best_category = category
        
        # Normalize confidence
        confidence = min(1.0, best_score + 0.3) if best_category != QuestionCategory.UNKNOWN else 0.3
        
        return best_category, confidence
    
    def _detect_difficulty(self, text: str) -> DifficultyLevel:
        """Detect the difficulty level of the question."""
        scores = {level: 0 for level in DifficultyLevel}
        
        for level, indicators in self.DIFFICULTY_INDICATORS.items():
            for indicator in indicators:
                if indicator in text:
                    scores[level] += 1
        
        # Default to medium if unclear
        max_level = max(scores, key=scores.get)
        return max_level if scores[max_level] > 0 else DifficultyLevel.MEDIUM
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect expected programming language."""
        for lang, indicators in self.LANGUAGE_INDICATORS.items():
            for indicator in indicators:
                if indicator in text:
                    return lang
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from the question."""
        keywords = []
        
        # Technical keywords
        tech_keywords = [
            'array', 'string', 'list', 'dictionary', 'hash', 'tree', 'graph',
            'sort', 'search', 'reverse', 'merge', 'split', 'join',
            'recursive', 'iterative', 'dynamic', 'greedy',
            'stack', 'queue', 'heap', 'linked list', 'binary',
            'time complexity', 'space complexity', 'optimize'
        ]
        
        for kw in tech_keywords:
            if kw in text:
                keywords.append(kw)
        
        return keywords[:10]  # Limit to 10
    
    def _is_question_like(self, text: str) -> bool:
        """Check if text resembles a question."""
        question_indicators = [
            r'\?',  # Question mark
            r'^(how|what|why|when|where|which)',  # Question words
            r'\b(write|implement|create|design|explain|describe)\b',  # Imperative verbs
            r'given\s+',  # Problem setup
        ]
        
        for pattern in question_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _generate_hints(self, category: QuestionCategory, keywords: List[str]) -> List[str]:
        """Generate helpful hints based on question analysis."""
        hints = []
        
        # Category-specific hints
        category_hints = {
            QuestionCategory.CODING_ALGORITHM: [
                "Consider edge cases (empty input, single element)",
                "Think about time and space complexity",
                "Start with a brute force approach, then optimize"
            ],
            QuestionCategory.DATA_STRUCTURE: [
                "Consider which operations need to be efficient",
                "Think about space-time tradeoffs",
                "Remember to handle edge cases"
            ],
            QuestionCategory.SYSTEM_DESIGN: [
                "Start with requirements clarification",
                "Estimate scale (users, requests per second)",
                "Consider reliability, scalability, maintainability"
            ],
            QuestionCategory.SQL_DATABASE: [
                "Identify the tables and relationships needed",
                "Consider using JOINs for related data",
                "Think about indexing for performance"
            ]
        }
        
        hints.extend(category_hints.get(category, []))
        
        # Keyword-specific hints
        if 'binary' in keywords:
            hints.append("Binary search requires sorted input")
        if 'recursive' in keywords:
            hints.append("Define base case and recursive case clearly")
        if 'dynamic' in keywords:
            hints.append("Identify overlapping subproblems")
        
        return hints[:5]  # Limit to 5 hints
    
    def get_recent_questions(self, max_age_seconds: float = 300.0) -> List[DetectedQuestion]:
        """Get questions detected in the last N seconds."""
        cutoff = time.time() - max_age_seconds
        return [q for q in self._detected_questions if q.timestamp > cutoff]
    
    def get_latest_question(self) -> Optional[DetectedQuestion]:
        """Get the most recently detected question."""
        return self._detected_questions[-1] if self._detected_questions else None
    
    def get_questions_by_category(self, category: QuestionCategory) -> List[DetectedQuestion]:
        """Get all questions of a specific category."""
        return [q for q in self._detected_questions if q.category == category]
    
    def clear_history(self):
        """Clear detection history."""
        self._detected_questions.clear()
        self._seen_texts.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        by_category = {}
        for category in QuestionCategory:
            count = len([q for q in self._detected_questions if q.category == category])
            if count > 0:
                by_category[category.value] = count
        
        return {
            'total_detected': len(self._detected_questions),
            'by_category': by_category,
            'unique_texts': len(self._seen_texts)
        }


# Factory function
def create_question_detector() -> QuestionDetector:
    """Create a QuestionDetector instance."""
    return QuestionDetector()

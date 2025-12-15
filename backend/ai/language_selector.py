"""
Language Selector - Resume-based technology filtering and language selection.
Extracts languages from resume and filters responses to match candidate's expertise.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProficiencyLevel(Enum):
    """Proficiency level for a programming language."""
    EXPERT = "expert"       # Primary language, extensive experience
    PROFICIENT = "proficient"  # Regular use, comfortable
    FAMILIAR = "familiar"   # Some experience, mentioned on resume
    BASIC = "basic"         # Minimal experience


@dataclass
class LanguageProfile:
    """Profile of a programming language from resume."""
    name: str
    proficiency: ProficiencyLevel
    years_experience: Optional[float] = None
    projects_count: int = 0
    mentioned_contexts: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    
    @property
    def priority_score(self) -> float:
        """Calculate priority score for language selection."""
        base_scores = {
            ProficiencyLevel.EXPERT: 4.0,
            ProficiencyLevel.PROFICIENT: 3.0,
            ProficiencyLevel.FAMILIAR: 2.0,
            ProficiencyLevel.BASIC: 1.0
        }
        score = base_scores[self.proficiency]
        
        # Bonus for experience
        if self.years_experience:
            score += min(2.0, self.years_experience * 0.3)
        
        # Bonus for projects
        score += min(1.0, self.projects_count * 0.2)
        
        return score


@dataclass
class ResumeLanguageData:
    """Extracted language data from resume."""
    languages: Dict[str, LanguageProfile]
    primary_language: Optional[str]
    secondary_languages: List[str]
    all_technologies: Set[str]
    frameworks: Dict[str, List[str]]  # language -> frameworks


class LanguageSelector:
    """
    Resume-based language selection for interview responses.
    
    Features:
    - Extract programming languages from resume
    - Determine proficiency levels
    - Select best language for answering questions
    - Filter responses to match candidate expertise
    """
    
    # Known programming languages with aliases
    KNOWN_LANGUAGES = {
        'python': ['python', 'py', 'python3', 'python2'],
        'javascript': ['javascript', 'js', 'ecmascript', 'es6', 'es2015'],
        'typescript': ['typescript', 'ts'],
        'java': ['java', 'jdk', 'jre'],
        'cpp': ['c++', 'cpp', 'cplusplus'],
        'c': ['c', 'c language'],
        'csharp': ['c#', 'csharp', 'c-sharp'],
        'ruby': ['ruby', 'rb'],
        'go': ['go', 'golang'],
        'rust': ['rust', 'rs'],
        'swift': ['swift'],
        'kotlin': ['kotlin', 'kt'],
        'php': ['php'],
        'scala': ['scala'],
        'r': ['r', 'r language'],
        'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'oracle'],
        'bash': ['bash', 'shell', 'sh', 'zsh'],
        'perl': ['perl'],
        'haskell': ['haskell'],
        'elixir': ['elixir'],
        'clojure': ['clojure'],
        'dart': ['dart'],
    }
    
    # Framework mappings to languages
    FRAMEWORK_LANGUAGE_MAP = {
        # Python
        'django': 'python', 'flask': 'python', 'fastapi': 'python',
        'pandas': 'python', 'numpy': 'python', 'tensorflow': 'python',
        'pytorch': 'python', 'scikit-learn': 'python', 'keras': 'python',
        
        # JavaScript/TypeScript
        'react': 'javascript', 'angular': 'javascript', 'vue': 'javascript',
        'node': 'javascript', 'nodejs': 'javascript', 'express': 'javascript',
        'next': 'javascript', 'nextjs': 'javascript', 'nuxt': 'javascript',
        'nest': 'typescript', 'nestjs': 'typescript',
        
        # Java
        'spring': 'java', 'springboot': 'java', 'hibernate': 'java',
        'maven': 'java', 'gradle': 'java', 'junit': 'java',
        
        # C#
        '.net': 'csharp', 'dotnet': 'csharp', 'asp.net': 'csharp',
        'entity framework': 'csharp', 'xamarin': 'csharp',
        
        # Ruby
        'rails': 'ruby', 'ruby on rails': 'ruby', 'sinatra': 'ruby',
        
        # Go
        'gin': 'go', 'echo': 'go', 'beego': 'go',
        
        # Swift
        'swiftui': 'swift', 'uikit': 'swift',
        
        # Kotlin
        'ktor': 'kotlin', 'jetpack': 'kotlin',
    }
    
    # Proficiency indicators
    PROFICIENCY_INDICATORS = {
        ProficiencyLevel.EXPERT: [
            'expert', 'advanced', 'extensive', 'primary', 'lead',
            '5+ years', '6+ years', '7+ years', '8+ years', '10+ years'
        ],
        ProficiencyLevel.PROFICIENT: [
            'proficient', 'experienced', 'skilled', 'competent',
            '3+ years', '4+ years', '2-3 years', '3-5 years'
        ],
        ProficiencyLevel.FAMILIAR: [
            'familiar', 'working knowledge', 'exposure',
            '1-2 years', '1+ year', '2+ years'
        ],
        ProficiencyLevel.BASIC: [
            'basic', 'beginner', 'learning', 'coursework', 'academic'
        ]
    }
    
    def __init__(self):
        self._resume_data: Optional[ResumeLanguageData] = None
        self._extracted_languages: Dict[str, LanguageProfile] = {}
        
        logger.info("LanguageSelector initialized")
    
    def extract_from_resume(self, resume_text: str) -> ResumeLanguageData:
        """
        Extract programming languages and proficiency from resume text.
        
        Args:
            resume_text: Full text content of resume
            
        Returns:
            ResumeLanguageData with extracted information
        """
        resume_lower = resume_text.lower()
        languages: Dict[str, LanguageProfile] = {}
        all_technologies: Set[str] = set()
        frameworks: Dict[str, List[str]] = {}
        
        # Extract programming languages
        for lang_name, aliases in self.KNOWN_LANGUAGES.items():
            for alias in aliases:
                # Use word boundaries for better matching
                pattern = rf'\b{re.escape(alias)}\b'
                matches = list(re.finditer(pattern, resume_lower))
                
                if matches:
                    # Determine proficiency from context
                    proficiency = self._determine_proficiency(resume_lower, alias, matches)
                    years = self._extract_years(resume_lower, alias)
                    contexts = self._extract_contexts(resume_text, alias, matches)
                    
                    if lang_name not in languages:
                        languages[lang_name] = LanguageProfile(
                            name=lang_name,
                            proficiency=proficiency,
                            years_experience=years,
                            projects_count=len(matches),
                            mentioned_contexts=contexts
                        )
                    
                    all_technologies.add(lang_name)
        
        # Extract frameworks and map to languages
        for framework, lang in self.FRAMEWORK_LANGUAGE_MAP.items():
            pattern = rf'\b{re.escape(framework)}\b'
            if re.search(pattern, resume_lower):
                all_technologies.add(framework)
                
                if lang not in frameworks:
                    frameworks[lang] = []
                frameworks[lang].append(framework)
                
                # If we found a framework but not the language, add the language
                if lang not in languages:
                    languages[lang] = LanguageProfile(
                        name=lang,
                        proficiency=ProficiencyLevel.FAMILIAR,
                        frameworks=[framework]
                    )
                else:
                    languages[lang].frameworks.append(framework)
        
        # Determine primary language
        primary = self._determine_primary_language(languages)
        
        # Get secondary languages
        secondary = [
            name for name, profile in sorted(
                languages.items(),
                key=lambda x: x[1].priority_score,
                reverse=True
            )
            if name != primary
        ][:5]  # Top 5 secondary
        
        self._resume_data = ResumeLanguageData(
            languages=languages,
            primary_language=primary,
            secondary_languages=secondary,
            all_technologies=all_technologies,
            frameworks=frameworks
        )
        
        self._extracted_languages = languages
        
        logger.info(f"Extracted {len(languages)} languages, primary: {primary}")
        
        return self._resume_data
    
    def _determine_proficiency(self, text: str, language: str, 
                              matches: List[re.Match]) -> ProficiencyLevel:
        """Determine proficiency level for a language."""
        # Check context around each match
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            for level, indicators in self.PROFICIENCY_INDICATORS.items():
                for indicator in indicators:
                    if indicator in context:
                        return level
        
        # Default based on mention count
        if len(matches) >= 5:
            return ProficiencyLevel.PROFICIENT
        elif len(matches) >= 2:
            return ProficiencyLevel.FAMILIAR
        else:
            return ProficiencyLevel.BASIC
    
    def _extract_years(self, text: str, language: str) -> Optional[float]:
        """Extract years of experience for a language."""
        # Look for patterns like "5 years of Python" or "Python (3 years)"
        patterns = [
            rf'(\d+\.?\d*)\+?\s*years?\s*(of\s+)?{language}',
            rf'{language}\s*[\(\[]\s*(\d+\.?\d*)\+?\s*years?',
            rf'{language}.*?(\d+\.?\d*)\+?\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_contexts(self, text: str, language: str, 
                         matches: List[re.Match]) -> List[str]:
        """Extract contexts where language is mentioned."""
        contexts = []
        
        for match in matches[:3]:  # Limit to 3 contexts
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            context = re.sub(r'\s+', ' ', context)  # Normalize whitespace
            contexts.append(context)
        
        return contexts
    
    def _determine_primary_language(self, languages: Dict[str, LanguageProfile]) -> Optional[str]:
        """Determine the primary language from extracted profiles."""
        if not languages:
            return None
        
        # Sort by priority score
        sorted_langs = sorted(
            languages.items(),
            key=lambda x: x[1].priority_score,
            reverse=True
        )
        
        return sorted_langs[0][0] if sorted_langs else None
    
    def select_language(self, question: str, 
                       requested_language: Optional[str] = None) -> str:
        """
        Select the best language for answering a question.
        
        Args:
            question: The interview question
            requested_language: Explicitly requested language (if any)
            
        Returns:
            Selected language name
        """
        # If explicitly requested and we know it, use it
        if requested_language:
            normalized = self._normalize_language(requested_language)
            if normalized and self._knows_language(normalized):
                return normalized
        
        # Check if question implies a specific language
        implied = self._detect_implied_language(question)
        if implied and self._knows_language(implied):
            return implied
        
        # Fall back to primary language
        if self._resume_data and self._resume_data.primary_language:
            return self._resume_data.primary_language
        
        # Ultimate fallback
        return 'python'
    
    def _normalize_language(self, name: str) -> Optional[str]:
        """Normalize a language name to our standard names."""
        name_lower = name.lower().strip()
        
        for lang_name, aliases in self.KNOWN_LANGUAGES.items():
            if name_lower in aliases:
                return lang_name
        
        return None
    
    def _knows_language(self, language: str) -> bool:
        """Check if candidate knows a language."""
        if not self._resume_data:
            return True  # Assume yes if no resume data
        
        return language in self._resume_data.languages
    
    def _detect_implied_language(self, question: str) -> Optional[str]:
        """Detect if question implies a specific language."""
        question_lower = question.lower()
        
        # Check for explicit language mentions
        for lang_name, aliases in self.KNOWN_LANGUAGES.items():
            for alias in aliases:
                if re.search(rf'\b{re.escape(alias)}\b', question_lower):
                    return lang_name
        
        # Check for framework mentions
        for framework, lang in self.FRAMEWORK_LANGUAGE_MAP.items():
            if re.search(rf'\b{re.escape(framework)}\b', question_lower):
                return lang
        
        return None
    
    def get_language_profile(self, language: str) -> Optional[LanguageProfile]:
        """Get profile for a specific language."""
        normalized = self._normalize_language(language) or language
        return self._extracted_languages.get(normalized)
    
    def get_all_languages(self) -> List[str]:
        """Get all languages from resume."""
        return list(self._extracted_languages.keys())
    
    def get_recommended_languages(self, count: int = 3) -> List[str]:
        """Get top N recommended languages for candidate."""
        sorted_langs = sorted(
            self._extracted_languages.items(),
            key=lambda x: x[1].priority_score,
            reverse=True
        )
        return [name for name, _ in sorted_langs[:count]]
    
    def get_frameworks_for_language(self, language: str) -> List[str]:
        """Get frameworks associated with a language."""
        if not self._resume_data:
            return []
        
        normalized = self._normalize_language(language) or language
        return self._resume_data.frameworks.get(normalized, [])
    
    def filter_response(self, response: str, target_language: str) -> str:
        """
        Filter response to ensure it matches target language.
        This is a simple filter - more complex filtering should be done at generation time.
        """
        # For now, just verify and return
        # In a full implementation, this could translate code or adjust terminology
        return response
    
    def get_context_for_llm(self) -> str:
        """Generate context string for LLM about candidate's language expertise."""
        if not self._resume_data:
            return ""
        
        parts = []
        
        if self._resume_data.primary_language:
            primary_profile = self._extracted_languages.get(self._resume_data.primary_language)
            if primary_profile:
                parts.append(f"Primary language: {self._resume_data.primary_language} "
                           f"({primary_profile.proficiency.value})")
        
        if self._resume_data.secondary_languages:
            parts.append(f"Also knows: {', '.join(self._resume_data.secondary_languages)}")
        
        return " | ".join(parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about extracted language data."""
        if not self._resume_data:
            return {'status': 'no_resume_loaded'}
        
        return {
            'languages_count': len(self._extracted_languages),
            'primary_language': self._resume_data.primary_language,
            'secondary_languages': self._resume_data.secondary_languages,
            'frameworks_count': sum(len(f) for f in self._resume_data.frameworks.values()),
            'all_technologies': list(self._resume_data.all_technologies)
        }


# Factory function
def create_language_selector() -> LanguageSelector:
    """Create a LanguageSelector instance."""
    return LanguageSelector()

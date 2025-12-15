"""
Resume Parser - Extract skills, experience, and context from PDF resumes
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ResumeParser:
    """Parse resume PDFs and extract structured information."""
    
    # Common skill categories
    SKILL_CATEGORIES = {
        "languages": ["python", "javascript", "java", "c++", "c#", "go", "rust", "typescript", "kotlin", "swift"],
        "frameworks": ["react", "angular", "vue", "django", "flask", "fastapi", "spring", "node.js", "express"],
        "databases": ["sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb", "cassandra"],
        "cloud": ["aws", "gcp", "azure", "kubernetes", "docker", "terraform", "jenkins", "ci/cd"],
        "ml": ["tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "keras", "mlflow", "spark"],
        "tools": ["git", "linux", "jira", "confluence", "figma", "postman", "grafana", "datadog"],
    }
    
    def __init__(self):
        self.resume_text = ""
        self.skills = {}
        self.experience = []
        self.education = []
        self.name = ""
        self.email = ""
    
    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        Parse a PDF resume and extract structured data.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict with extracted resume data
        """
        try:
            from PyPDF2 import PdfReader
            
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            self.resume_text = text
            self._extract_skills(text)
            self._extract_experience(text)
            
            logger.info(f"Parsed resume: {Path(pdf_path).name}")
            return self.get_summary()
            
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            return {}
    
    def _extract_skills(self, text: str):
        """Extract skills from resume text."""
        text_lower = text.lower()
        
        self.skills = {}
        for category, skills in self.SKILL_CATEGORIES.items():
            found = [s for s in skills if s in text_lower]
            if found:
                self.skills[category] = found
    
    def _extract_experience(self, text: str):
        """Extract experience indicators from text."""
        text_lower = text.lower()
        
        # Years of experience patterns
        import re
        year_patterns = [
            r'(\d+)\+?\s*years?\s*(of)?\s*experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, text_lower)
            if match:
                self.experience.append(f"{match.group(1)}+ years experience")
                break
        
        # Company indicators
        companies = ["amazon", "google", "microsoft", "meta", "apple", "netflix", "uber", "airbnb"]
        for company in companies:
            if company in text_lower:
                self.experience.append(f"Experience at {company.title()}")
    
    def get_summary(self) -> Dict:
        """Get a summary of parsed resume data."""
        return {
            "text": self.resume_text,
            "skills": self.skills,
            "experience": self.experience,
            "skill_count": sum(len(s) for s in self.skills.values()),
        }
    
    def get_skills_for_prompt(self) -> str:
        """Get skills formatted for LLM prompt."""
        if not self.skills:
            return "No specific skills extracted"
        
        parts = []
        for category, skills in self.skills.items():
            parts.append(f"{category.title()}: {', '.join(skills)}")
        return "\n".join(parts)
    
    def get_context_for_answer(self) -> str:
        """Get resume context formatted for answer generation."""
        if not self.resume_text:
            return ""
        
        # Return first 1500 chars of resume for context
        return self.resume_text[:1500]

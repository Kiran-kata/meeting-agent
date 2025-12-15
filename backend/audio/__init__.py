"""
Parakeet-style audio processing module
"""
from .parakeet_audio import ParakeetAudioProcessor, TranscriptEvent, Speaker
from .decision_engine import ParakeetDecisionEngine, ParakeetAnswerFormatter, QuestionIntent

__all__ = [
    'ParakeetAudioProcessor',
    'TranscriptEvent',
    'Speaker',
    'ParakeetDecisionEngine',
    'ParakeetAnswerFormatter',
    'QuestionIntent'
]

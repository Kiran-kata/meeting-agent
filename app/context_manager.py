import time
from collections import deque


class ContextManager:
    def __init__(self, max_chars: int = 8000) -> None:
        self.transcript_segments = deque()
        self.qa_log = []
        self.max_chars = max_chars

    def add_transcript(self, text: str, source: str) -> None:
        """
        source: 'meeting' or 'mic' – we keep both, but only meeting source triggers answers.
        """
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}][{source.upper()}] {text}"
        self.transcript_segments.append(entry)

        while sum(len(s) for s in self.transcript_segments) > self.max_chars:
            self.transcript_segments.popleft()

    def get_recent_transcript(self, last_n_chars: int = 2000) -> str:
        buf = []
        total = 0
        for seg in reversed(self.transcript_segments):
            seg_len = len(seg)
            if total + seg_len > last_n_chars:
                break
            buf.append(seg)
            total += seg_len
        return "\n".join(reversed(buf))

    def log_qa(self, question: str, answer: str) -> None:
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] Q: {question}\nA: {answer}\n"
        self.qa_log.append(entry)

    def get_full_transcript(self) -> str:
        return "\n".join(self.transcript_segments)

    def get_qa_log(self) -> str:
        return "\n".join(self.qa_log)

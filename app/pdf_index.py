import os
from typing import List, Tuple
import logging

import numpy as np
import faiss
from PyPDF2 import PdfReader
from groq import Groq

from .config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200


def _load_pdfs(folder: str = "data") -> List[Tuple[str, str]]:
    """
    Load all PDFs in `folder` and return chunks as (text, source_filename).
    """
    chunks: List[Tuple[str, str]] = []
    for fname in os.listdir(folder):
        if not fname.lower().endswith(".pdf"):
            continue
        path = os.path.join(folder, fname)
        reader = PdfReader(path)
        full_text = ""
        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n"

        i = 0
        while i < len(full_text):
            chunk = full_text[i:i + CHUNK_SIZE]
            chunks.append((chunk, fname))
            i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _embed_texts(texts: List[str]) -> np.ndarray:
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    vecs = np.array([d.embedding for d in resp.data]).astype("float32")
    return vecs


class PDFIndex:
    def __init__(self) -> None:
        self.index = None
        self.chunks: List[str] = []
        self.sources: List[str] = []

    def build(self, folder: str = "data") -> None:
        chunks_with_src = _load_pdfs(folder)
        if not chunks_with_src:
            return
        texts, sources = zip(*chunks_with_src)
        self.chunks = list(texts)
        self.sources = list(sources)

        vectors = _embed_texts(self.chunks)
        dim = vectors.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(vectors)

    def query(self, question: str, k: int = 5) -> List[str]:
        if self.index is None:
            return []
        q_vec = _embed_texts([question])
        D, I = self.index.search(q_vec, k)
        return [self.chunks[i] for i in I[0]]

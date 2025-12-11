"""
Streaming LLM Client - Real-time answer generation like Parquet.AI
Generates answers token-by-token as they are being formulated.
"""
import logging
import asyncio
from typing import AsyncGenerator
import google.generativeai as genai
from .config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)


async def stream_answer(
    question: str,
    pdf_context: str = "",
    transcript_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Stream answer tokens in real-time as they are generated.
    This allows displaying answers as they're being formulated.
    
    Args:
        question: The question asked
        pdf_context: Context from PDF documents
        transcript_context: Recent transcript for context
    
    Yields:
        Individual tokens/chunks of the answer as they're generated
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Build context
        pdf_part = f"\nKNOWLEDGE BASE (from PDF):\n{pdf_context[:500]}" if pdf_context else ""
        tx = transcript_context[-200:].strip() if transcript_context else ""
        tx_part = f"\nRECENT DISCUSSION:\n{tx}" if tx else ""
        
        context = pdf_part + tx_part
        
        # Build prompt
        prompt = f"QUESTION: {question}\n{context}\n\nProvide a detailed, helpful answer based on the above information."
        
        # Stream the response
        response = model.generate_content(
            prompt,
            stream=True,
            safety_settings=[
                {
                    "category": genai.types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                    "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
                }
            ]
        )
        
        # Yield tokens as they arrive
        for chunk in response:
            if chunk.text:
                yield chunk.text
                logger.debug(f"Streamed chunk: {chunk.text[:50]}...")
    
    except Exception as e:
        logger.error(f"Error in stream_answer: {e}", exc_info=True)
        yield f"Error generating answer: {str(e)}"


class StreamingAnswerBuffer:
    """Buffer for collecting streaming answer chunks"""
    
    def __init__(self):
        self.chunks = []
        self.full_answer = ""
    
    def add_chunk(self, chunk: str):
        """Add a chunk to the buffer"""
        self.chunks.append(chunk)
        self.full_answer += chunk
    
    def get_full_answer(self) -> str:
        """Get the complete answer so far"""
        return self.full_answer
    
    def clear(self):
        """Clear the buffer"""
        self.chunks = []
        self.full_answer = ""


async def ask_llm_streaming(
    question: str,
    pdf_context: str = "",
    transcript_context: str = "",
    callback=None,
) -> str:
    """
    Ask LLM with streaming, calling callback for each chunk.
    
    Args:
        question: The question
        pdf_context: PDF context
        transcript_context: Transcript context
        callback: Callable(chunk_text) called for each streamed chunk
    
    Returns:
        Complete answer text
    """
    buffer = StreamingAnswerBuffer()
    
    async for chunk in stream_answer(question, pdf_context, transcript_context):
        buffer.add_chunk(chunk)
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(chunk)
                else:
                    callback(chunk)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    return buffer.get_full_answer()

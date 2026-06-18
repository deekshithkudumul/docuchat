"""
services/embeddings.py — Text chunking + sentence-transformer embeddings
"""
import os
from sentence_transformers import SentenceTransformer
from typing import List
from models.schemas import TextChunk

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        cache_folder = os.getenv("SENTENCE_TRANSFORMERS_HOME", "C:/models")
        _model = SentenceTransformer(MODEL_NAME, cache_folder=cache_folder)
    return _model

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + chunk_size]))
        start += chunk_size - overlap
    return chunks

def embed_chunks(chunks: List[str], doc_id: str) -> List[TextChunk]:
    vectors = get_model().encode(chunks, show_progress_bar=False)
    return [
        TextChunk(
            chunk_id=f"{doc_id}_chunk_{i}",
            text=chunk,
            embedding=vec.tolist(),
            doc_id=doc_id,
        )
        for i, (chunk, vec) in enumerate(zip(chunks, vectors))
    ]

def process_document(text: str, doc_id: str) -> List[TextChunk]:
    return embed_chunks(chunk_text(text), doc_id)

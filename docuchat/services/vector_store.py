"""
services/vector_store.py — ChromaDB vector store
"""
import os
import chromadb
from typing import List
from models.schemas import TextChunk, SearchResult

_client = None
_collection = None
COLLECTION_NAME = "docuchat_chunks"
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_data")

def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection

def save_chunks(chunks: List[TextChunk]) -> int:
    collection = get_collection()
    collection.upsert(
        ids=[c.chunk_id for c in chunks],
        embeddings=[c.embedding for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[{"doc_id": c.doc_id} for c in chunks],
    )
    return len(chunks)

def search_chunks(query_embedding: List[float], n_results: int = 5, doc_id: str = None) -> List[SearchResult]:
    collection = get_collection()
    where = {"doc_id": doc_id} if doc_id else None
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    output = []
    if results["documents"] and results["documents"][0]:
        for text, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            output.append(SearchResult(text=text, doc_id=meta.get("doc_id", ""), score=round(1 - dist, 4)))
    return output

def get_all_chunks_for_doc(doc_id: str) -> List[SearchResult]:
    collection = get_collection()
    results = collection.get(where={"doc_id": doc_id}, include=["documents", "metadatas"])
    output = []
    if results["documents"]:
        for text, meta in zip(results["documents"], results["metadatas"]):
            output.append(SearchResult(text=text, doc_id=meta.get("doc_id", ""), score=1.0))
    return output

def delete_document(doc_id: str) -> int:
    collection = get_collection()
    existing = collection.get(where={"doc_id": doc_id})
    ids_to_delete = existing["ids"]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)

def list_documents() -> List[str]:
    collection = get_collection()
    all_meta = collection.get(include=["metadatas"])["metadatas"]
    seen = set()
    return [m["doc_id"] for m in all_meta if m["doc_id"] not in seen and not seen.add(m["doc_id"])]

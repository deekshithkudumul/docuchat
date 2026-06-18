from pydantic import BaseModel
from typing import List, Optional

class UploadResponse(BaseModel):
    filename: str
    num_pages: int
    chunks_stored: int
    message: str

class ChatRequest(BaseModel):
    question: str
    doc_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    highlight: Optional[str] = None
    source_doc: Optional[str] = None
    sources: List[str] = []

class SummarizeRequest(BaseModel):
    doc_id: str

class SummarizeResponse(BaseModel):
    doc_id: str
    summary: str

class QuizRequest(BaseModel):
    doc_id: str
    num_questions: Optional[int] = 5

class QuizQuestion(BaseModel):
    rank: int
    question: str
    importance: str
    hint: str

class QuizResponse(BaseModel):
    doc_id: str
    total_questions: int
    questions: List[QuizQuestion]

class EvaluateRequest(BaseModel):
    doc_id: str
    question: str
    student_answer: str

class EvaluateResponse(BaseModel):
    question: str
    student_answer: str
    score: int
    feedback: str
    correct_answer: str
    encouragement: str
    score_label: str

class TextChunk(BaseModel):
    chunk_id: str
    text: str
    embedding: List[float]
    doc_id: str

class SearchResult(BaseModel):
    text: str
    doc_id: str
    score: float

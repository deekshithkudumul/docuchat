"""
routers/chat.py — chat, summarize, quiz, evaluate
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import ChatSession, ChatMessage, QuizResult
from models.schemas import ChatRequest, ChatResponse, SummarizeRequest, SummarizeResponse, QuizRequest, QuizResponse, QuizQuestion, EvaluateRequest, EvaluateResponse
from services.embeddings import get_model
from services.vector_store import search_chunks, get_all_chunks_for_doc
from services.llm import get_answer, summarize_document, generate_quiz, evaluate_answer

router = APIRouter()

def _score_label(score: int) -> str:
    if score >= 9: return "Excellent 🌟"
    if score >= 7: return "Good 👍"
    if score >= 5: return "Fair 📚"
    if score >= 3: return "Needs Work 💪"
    return "Keep Trying 🔄"

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    q_vector = get_model().encode([req.question])[0].tolist()
    results = search_chunks(query_embedding=q_vector, n_results=5, doc_id=req.doc_id)
    if not results:
        return ChatResponse(answer="No documents found. Please upload a PDF first.", sources=[])
    result = get_answer(question=req.question, chunks=results)
    sources = [f"[{r.doc_id} | score:{r.score}] {r.text[:200]}..." for r in results]
    session = ChatSession(doc_id=req.doc_id, title=req.question[:50])
    db.add(session)
    db.flush()
    db.add(ChatMessage(session_id=session.id, role="user", content=req.question))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=result["answer"], highlight=result.get("highlight"), source_doc=result.get("source_doc")))
    db.commit()
    return ChatResponse(answer=result["answer"], highlight=result.get("highlight"), source_doc=result.get("source_doc"), sources=sources)

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest, db: Session = Depends(get_db)):
    chunks = get_all_chunks_for_doc(req.doc_id)
    if not chunks:
        raise HTTPException(status_code=404, detail=f"No document found with id '{req.doc_id}'.")
    summary = summarize_document(chunks)
    return SummarizeResponse(doc_id=req.doc_id, summary=summary)

@router.post("/quiz", response_model=QuizResponse)
async def quiz(req: QuizRequest, db: Session = Depends(get_db)):
    chunks = get_all_chunks_for_doc(req.doc_id)
    if not chunks:
        raise HTTPException(status_code=404, detail=f"No document found with id '{req.doc_id}'.")
    num_q = max(1, min(req.num_questions or 5, 10))
    questions_raw = generate_quiz(chunks, num_questions=num_q)
    questions = [QuizQuestion(**q) for q in questions_raw]
    return QuizResponse(doc_id=req.doc_id, total_questions=len(questions), questions=questions)

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(req: EvaluateRequest, db: Session = Depends(get_db)):
    if not req.student_answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")
    chunks = get_all_chunks_for_doc(req.doc_id)
    if not chunks:
        raise HTTPException(status_code=404, detail=f"No document found with id '{req.doc_id}'.")
    result = evaluate_answer(question=req.question, student_answer=req.student_answer, chunks=chunks)
    db.add(QuizResult(doc_id=req.doc_id, question=req.question, student_answer=req.student_answer, score=result["score"], feedback=result["feedback"], correct_answer=result["correct_answer"]))
    db.commit()
    return EvaluateResponse(question=req.question, student_answer=req.student_answer, score=result["score"], feedback=result["feedback"], correct_answer=result["correct_answer"], encouragement=result["encouragement"], score_label=_score_label(result["score"]))

@router.get("/sessions/{doc_id}")
def get_sessions(doc_id: str, db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.doc_id == doc_id).order_by(ChatSession.created_at.desc()).all()
    return [{"id": s.id, "title": s.title, "created_at": s.created_at} for s in sessions]

@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return [{"role": m.role, "content": m.content, "highlight": m.highlight, "source_doc": m.source_doc, "created_at": m.created_at} for m in messages]

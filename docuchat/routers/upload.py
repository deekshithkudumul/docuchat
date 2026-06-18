"""
routers/upload.py — PDF upload pipeline
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import Document
from services.pdf_extractor import extract_text
from services.embeddings import process_document
from services.vector_store import save_chunks, delete_document
from models.schemas import UploadResponse

router = APIRouter()

@router.post("/", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    text = extract_text(contents)
    num_pages = text.count("\f") + 1
    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text found in PDF.")
    delete_document(file.filename)
    chunks = process_document(text=text, doc_id=file.filename)
    stored = save_chunks(chunks)
    existing = db.query(Document).filter(Document.filename == file.filename).first()
    if existing:
        existing.num_pages = num_pages
        existing.chunks = stored
    else:
        db.add(Document(filename=file.filename, num_pages=num_pages, chunks=stored))
    db.commit()
    return UploadResponse(filename=file.filename, num_pages=num_pages, chunks_stored=stored, message=f"Ingested {stored} chunks from {num_pages} page(s).")

@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return [{"id": d.id, "filename": d.filename, "num_pages": d.num_pages, "chunks": d.chunks, "uploaded_at": d.uploaded_at} for d in docs]

@router.delete("/documents/{filename}")
def delete_doc(filename: str, db: Session = Depends(get_db)):
    deleted_chunks = delete_document(filename)
    doc = db.query(Document).filter(Document.filename == filename).first()
    if doc:
        db.delete(doc)
        db.commit()
    return {"message": f"Deleted {filename}", "chunks_removed": deleted_chunks}

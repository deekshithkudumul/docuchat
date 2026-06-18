"""
main.py — DocuChat entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, chat
from routers.auth import router as auth_router
from services.llm import print_llm_status
from database import engine
from models import db_models

db_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DocuChat", description="RAG Chatbot with Auth", version="0.8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

@app.on_event("startup")
async def startup():
    print_llm_status()
    print("[DocuChat] Database tables ready ✅")
    print("[DocuChat] Auth system active 🔐")

@app.get("/")
def root():
    return {"status": "ok", "message": "DocuChat is running!"}

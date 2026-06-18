"""
models/db_models.py — ORM models
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id         = Column(String, primary_key=True, default=gen_uuid)
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, nullable=False, index=True)
    password   = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    documents  = relationship("Document", back_populates="owner", cascade="all, delete")

class Document(Base):
    __tablename__ = "documents"
    id          = Column(String, primary_key=True, default=gen_uuid)
    filename    = Column(String, nullable=False)
    num_pages   = Column(Integer, default=1)
    chunks      = Column(Integer, default=0)
    uploaded_at = Column(DateTime, server_default=func.now())
    owner_id    = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    owner       = relationship("User", back_populates="documents")
    sessions    = relationship("ChatSession", back_populates="document", cascade="all, delete")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id         = Column(String, primary_key=True, default=gen_uuid)
    doc_id     = Column(String, ForeignKey("documents.id", ondelete="CASCADE"))
    title      = Column(String, default="New Chat")
    created_at = Column(DateTime, server_default=func.now())
    document   = relationship("Document", back_populates="sessions")
    messages   = relationship("ChatMessage", back_populates="session", cascade="all, delete")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role       = Column(String, nullable=False)
    content    = Column(Text, nullable=False)
    highlight  = Column(Text, nullable=True)
    source_doc = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    session    = relationship("ChatSession", back_populates="messages")

class QuizResult(Base):
    __tablename__ = "quiz_results"
    id             = Column(String, primary_key=True, default=gen_uuid)
    doc_id         = Column(String, nullable=False)
    question       = Column(Text, nullable=False)
    student_answer = Column(Text, nullable=False)
    score          = Column(Integer, default=0)
    feedback       = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    created_at     = Column(DateTime, server_default=func.now())

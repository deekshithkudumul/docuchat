"""
services/llm.py — Smart LLM Router: Groq primary + Gemini fallback
"""
import os
import time
import google.generativeai as genai
from groq import Groq
from typing import List
from dotenv import load_dotenv
from models.schemas import SearchResult

load_dotenv()

GROQ_CONTEXT_CHAR_LIMIT = 400_000
QUOTA_MESSAGE = (
    "All API keys (Groq + Gemini) have hit their quota. "
    "Options: (1) Wait until 12:30 PM IST tomorrow for Gemini reset. "
    "(2) Wait a few minutes for Groq per-minute quota to reset. "
    "(3) Add more keys to .env file."
)

# --- Groq ---
_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        _groq_client = Groq(api_key=api_key)
    return _groq_client

def _call_groq(prompt: str) -> str:
    client = get_groq_client()
    if client is None:
        raise ValueError("GROQ_API_KEY not set")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

# --- Gemini ---
def _load_gemini_keys() -> List[str]:
    keys = []
    for i in range(1, 11):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k:
            keys.append(k.strip())
    if not keys:
        k = os.getenv("GEMINI_API_KEY")
        if k:
            keys.append(k.strip())
    return keys

GEMINI_KEYS = _load_gemini_keys()
_gemini_key_index = 0
_gemini_model = None

def _init_gemini(key: str):
    global _gemini_model
    genai.configure(api_key=key)
    _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    return _gemini_model

def get_gemini():
    global _gemini_model, _gemini_key_index
    if not GEMINI_KEYS:
        return None
    if _gemini_model is None:
        _init_gemini(GEMINI_KEYS[_gemini_key_index])
    return _gemini_model

def _rotate_gemini_key() -> bool:
    global _gemini_key_index, _gemini_model
    next_idx = _gemini_key_index + 1
    if next_idx >= len(GEMINI_KEYS):
        return False
    _gemini_key_index = next_idx
    _init_gemini(GEMINI_KEYS[_gemini_key_index])
    print(f"[DocuChat] Rotated to Gemini key #{_gemini_key_index + 1}")
    return True

def _call_gemini(prompt: str) -> str:
    global _gemini_key_index
    attempts = 0
    while attempts <= len(GEMINI_KEYS):
        try:
            model = get_gemini()
            if model is None:
                raise ValueError("No Gemini keys configured")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            err = str(e).lower()
            is_quota = any(w in err for w in ["quota", "rate", "429", "exhausted", "resource_exhausted"])
            if is_quota:
                print(f"[DocuChat] Gemini key #{_gemini_key_index + 1} quota hit.")
                if not _rotate_gemini_key():
                    _gemini_key_index = 0
                    _init_gemini(GEMINI_KEYS[0])
                    return "__QUOTA_EXHAUSTED__"
                attempts += 1
                time.sleep(0.5)
            else:
                raise e
    return "__QUOTA_EXHAUSTED__"

def _generate(prompt: str) -> str:
    if len(prompt) > GROQ_CONTEXT_CHAR_LIMIT:
        print("[DocuChat] Large context → using Gemini")
        result = _call_gemini(prompt)
        return QUOTA_MESSAGE if result == "__QUOTA_EXHAUSTED__" else result
    groq_client = get_groq_client()
    if groq_client is not None:
        try:
            print("[DocuChat] Using Groq (llama-3.3-70b)")
            return _call_groq(prompt)
        except Exception as e:
            err = str(e).lower()
            is_quota = any(w in err for w in ["quota", "rate", "429", "exceeded", "limit"])
            print(f"[DocuChat] Groq {'quota hit' if is_quota else f'error: {e}'} → falling back to Gemini")
    print("[DocuChat] Using Gemini (gemini-2.0-flash)")
    result = _call_gemini(prompt)
    return QUOTA_MESSAGE if result == "__QUOTA_EXHAUSTED__" else result

def print_llm_status():
    groq_ready = os.getenv("GROQ_API_KEY") is not None
    print(f"[DocuChat LLM] Groq: {'✅ ready' if groq_ready else '❌ not configured'}")
    print(f"[DocuChat LLM] Gemini: {len(GEMINI_KEYS)} key(s) loaded")
    print(f"[DocuChat LLM] Large doc threshold: {GROQ_CONTEXT_CHAR_LIMIT:,} chars")

def get_answer(question: str, chunks: List[SearchResult]) -> dict:
    if not chunks:
        return {"answer": "No documents found. Please upload a PDF first.", "highlight": None, "source_doc": None}
    context_parts = [f"[Chunk {i} | doc: {c.doc_id} | score: {c.score:.2f}]\n{c.text}" for i, c in enumerate(chunks, 1)]
    context_str = "\n---\n".join(context_parts)
    prompt = f"""You are DocuChat, an AI assistant. Answer ONLY from the context below.

CONTEXT:
{context_str}

QUESTION:
{question}

INSTRUCTIONS:
- Answer concisely from the context.
- After your answer write: HIGHLIGHT: then the most relevant phrase (max 40 words).
- Then write: SOURCE: then the doc name.
- If not found say "I couldn't find that in the uploaded documents." and write HIGHLIGHT: none

FORMAT:
<answer>
HIGHLIGHT: <phrase>
SOURCE: <doc>"""
    try:
        text = _generate(prompt)
        if text == QUOTA_MESSAGE:
            return {"answer": text, "highlight": None, "source_doc": None}
        answer, highlight, source_doc = text, None, None
        if "HIGHLIGHT:" in text:
            parts = text.split("HIGHLIGHT:")
            answer = parts[0].strip()
            rest = parts[1].strip()
            if "SOURCE:" in rest:
                hi_parts = rest.split("SOURCE:")
                highlight = hi_parts[0].strip()
                source_doc = hi_parts[1].strip()
            else:
                highlight = rest.strip()
        if highlight and highlight.lower() == "none":
            highlight = None
        return {"answer": answer, "highlight": highlight, "source_doc": source_doc or (chunks[0].doc_id if chunks else None)}
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "highlight": None, "source_doc": None}

def summarize_document(chunks: List[SearchResult]) -> str:
    if not chunks:
        return "No content found to summarize."
    all_text = "\n\n".join([c.text for c in chunks])
    if len(all_text) > 12000:
        all_text = all_text[:12000] + "...[truncated]"
    prompt = f"""You are DocuChat. Summarize the following document clearly.

DOCUMENT CONTENT:
{all_text}

Provide:
1. A 2-3 sentence overview.
2. Key topics covered (bullet list).
3. Most important takeaways (3-5 points)."""
    try:
        result = _generate(prompt)
        return QUOTA_MESSAGE if result == QUOTA_MESSAGE else result
    except Exception as e:
        return f"Error: {str(e)}"

def generate_quiz(chunks: List[SearchResult], num_questions: int = 5) -> list:
    if not chunks:
        return []
    all_text = "\n\n".join([c.text for c in chunks])
    if len(all_text) > 12000:
        all_text = all_text[:12000] + "...[truncated]"
    prompt = f"""You are an expert teacher. A student uploaded study material and wants to be quizzed.

STUDY MATERIAL:
{all_text}

Generate exactly {num_questions} exam-style questions ranked MOST to LEAST important.

Format:
Q1: <question>
IMPORTANCE: <why important>
HINT: <subtle hint>
---
Q2: <question>
IMPORTANCE: <why important>
HINT: <hint>
---"""
    try:
        text = _generate(prompt)
        if text == QUOTA_MESSAGE:
            return [{"question": QUOTA_MESSAGE, "importance": "", "hint": "", "rank": 1}]
        questions = []
        for block in text.split("---"):
            block = block.strip()
            if not block:
                continue
            q_text = importance = hint = None
            for line in block.split("\n"):
                line = line.strip()
                if line and ":" in line and line[0] == "Q" and line[1:line.index(":")].strip().isdigit():
                    q_text = line.split(":", 1)[1].strip()
                elif line.startswith("IMPORTANCE:"):
                    importance = line.replace("IMPORTANCE:", "").strip()
                elif line.startswith("HINT:"):
                    hint = line.replace("HINT:", "").strip()
            if q_text:
                questions.append({"question": q_text, "importance": importance or "Key concept.", "hint": hint or "Review your notes.", "rank": len(questions) + 1})
        return questions[:num_questions]
    except Exception as e:
        return [{"question": f"Error: {str(e)}", "importance": "", "hint": "", "rank": 1}]

def evaluate_answer(question: str, student_answer: str, chunks: List[SearchResult]) -> dict:
    context_str = "\n---\n".join([c.text for c in chunks[:5]])
    prompt = f"""You are a strict but kind exam evaluator.

STUDY MATERIAL:
{context_str}

EXAM QUESTION:
{question}

STUDENT'S ANSWER:
{student_answer}

Respond in EXACT format:
SCORE: <0 to 10>
FEEDBACK: <2-3 sentences>
CORRECT_ANSWER: <ideal answer, 2-5 sentences>
ENCOURAGEMENT: <one motivational sentence>

Scoring: 9-10 complete | 7-8 mostly right | 5-6 partial | 3-4 mostly wrong | 0-2 irrelevant"""
    try:
        text = _generate(prompt)
        if text == QUOTA_MESSAGE:
            return {"score": 0, "feedback": QUOTA_MESSAGE, "correct_answer": "", "encouragement": ""}
        score, feedback, correct_answer, encouragement = 0, "", "", ""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("SCORE:"):
                try: score = max(0, min(10, int(line.replace("SCORE:", "").strip().split()[0])))
                except: score = 0
            elif line.startswith("FEEDBACK:"): feedback = line.replace("FEEDBACK:", "").strip()
            elif line.startswith("CORRECT_ANSWER:"): correct_answer = line.replace("CORRECT_ANSWER:", "").strip()
            elif line.startswith("ENCOURAGEMENT:"): encouragement = line.replace("ENCOURAGEMENT:", "").strip()
        return {"score": score, "feedback": feedback or "See correct answer below.", "correct_answer": correct_answer or "Refer to your study material.", "encouragement": encouragement or ("Great job!" if score >= 7 else "Keep studying!")}
    except Exception as e:
        return {"score": 0, "feedback": f"Error: {str(e)}", "correct_answer": "", "encouragement": ""}

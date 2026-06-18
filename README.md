# DocuChat — AI RAG Chatbot

## Setup

### Backend
```bash
cd docuchat
cp .env.example .env
# Fill in your API keys in .env
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd docuchat-frontend
npm install
npm run dev
```

Open http://localhost:3000

## Features
- PDF upload + RAG chat with source highlighting
- Document summarizer
- Quiz mode with answer evaluation
- JWT authentication
- Groq + Gemini smart LLM routing

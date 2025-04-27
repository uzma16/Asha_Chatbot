import sys
from pathlib import Path

# Add the backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, feedback
from app.config import settings
from pydantic import BaseModel
from app.services.rag_service import RAGService


app = FastAPI(title="Asha Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
# app.include_router(jobs.router, prefix="/api", tags=["jobs"])
# app.include_router(events.router, prefix="/api", tags=["events"])
# app.include_router(mentorship.router, prefix="/api", tags=["mentorship"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])

rag_service = RAGService()

class Query(BaseModel):
    question: str

@app.post("/query")
async def query_rag(query: Query):
    try:
        response = rag_service.query(query.question)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Asha Chatbot API is running"}
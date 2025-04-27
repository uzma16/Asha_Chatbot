from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatMessage(BaseModel):
    session_id: str
    message: str
    sender: str  # "user" or "bot"
    timestamp: datetime = datetime.now()

class ChatRequest(BaseModel):
    session_id: str
    query: str
    contact_info: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime = datetime.now()
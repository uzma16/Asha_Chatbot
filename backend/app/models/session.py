import sys
from pathlib import Path

# Add the backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings

class SessionBase(BaseModel):
    session_id: str
    created_at: datetime
    last_accessed: datetime
    context: Dict[str, List[Dict[str, str]]]

class SessionCreate(BaseModel):
    session_id: str
    context: Optional[Dict] = {}

class SessionUpdate(BaseModel):
    last_accessed: datetime
    context: Dict
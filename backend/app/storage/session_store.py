import sys
from pathlib import Path

# Add the backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.models.session import SessionBase, SessionCreate, SessionUpdate
from app.config import settings
from app.utils.logger import logger

class SessionStore:
    def __init__(self):
        self.sessions_file = Path("data/sessions.json")
        self.sessions_file.parent.mkdir(exist_ok=True)
        if not self.sessions_file.exists():
            self.sessions_file.write_text("{}")
        self.sessions: Dict[str, SessionBase] = self._load_sessions()

    def _load_sessions(self) -> Dict[str, SessionBase]:
        try:
            with open(self.sessions_file, "r") as f:
                data = json.load(f)
                return {
                    sid: SessionBase(**session_data)
                    for sid, session_data in data.items()
                }
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            return {}

    def _save_sessions(self):
        try:
            with open(self.sessions_file, "w") as f:
                json.dump(
                    {sid: session.dict() for sid, session in self.sessions.items()},
                    f,
                    indent=2,
                    default=str
                )
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")

    def create_session(self, session: SessionCreate) -> SessionBase:
        new_session = SessionBase(
            session_id=session.session_id,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            context=session.context
        )
        self.sessions[session.session_id] = new_session
        self._save_sessions()
        return new_session

    def get_session(self, session_id: str) -> Optional[SessionBase]:
        self._cleanup_expired_sessions()
        if session_id in self.sessions:
            return self.sessions[session_id]
        return None

    def update_session(self, session_id: str, update_data: SessionUpdate) -> Optional[SessionBase]:
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        updated_session = SessionBase(
            session_id=session_id,
            created_at=session.created_at,
            last_accessed=update_data.last_accessed,
            context=update_data.context
        )
        
        self.sessions[session_id] = updated_session
        self._save_sessions()
        return updated_session

    def _cleanup_expired_sessions(self):
        expiry_time = datetime.now() - timedelta(minutes=settings.session_timeout_minutes)
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if datetime.fromisoformat(session.last_accessed) < expiry_time
        ]
        
        for sid in expired_sessions:
            del self.sessions[sid]
        
        if expired_sessions:
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
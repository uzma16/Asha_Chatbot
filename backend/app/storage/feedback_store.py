import sys
from pathlib import Path

# Add the backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
sys.path.append(str(backend_dir))

from typing import Optional
from datetime import datetime
import json
from pathlib import Path
from app.utils.logger import logger

class FeedbackStore:
    def __init__(self):
        self.feedback_file = Path("data/feedback.json")
        self.feedback_file.parent.mkdir(exist_ok=True)
        if not self.feedback_file.exists():
            self.feedback_file.write_text("[]")

    async def save_feedback(self, session_id: str, feedback_text: str, 
                          contact_info: Optional[str] = None):
        try:
            feedback_data = {
                "session_id": session_id,
                "feedback": feedback_text,
                "contact_info": contact_info,
                "timestamp": datetime.now().isoformat()
            }
            
            # Read existing feedback
            current_data = json.loads(self.feedback_file.read_text())
            current_data.append(feedback_data)
            
            # Write back to file
            self.feedback_file.write_text(json.dumps(current_data, indent=2))
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            raise
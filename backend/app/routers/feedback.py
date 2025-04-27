import sys
from pathlib import Path

# Add the backend directory to sys.path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent
sys.path.append(str(backend_dir))

from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest
from app.storage.feedback_store import FeedbackStore
from app.utils.logger import logger

router = APIRouter()
feedback_store = FeedbackStore()

@router.post("/feedback")
async def submit_feedback(feedback_request: ChatRequest):
    """
    Submit user feedback
    """
    try:
        await feedback_store.save_feedback(
            session_id=feedback_request.session_id,
            feedback_text=feedback_request.query,
            contact_info=feedback_request.contact_info
        )
        return {"status": "success", "message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Error submitting feedback")

@router.get("/feedback/{session_id}")
async def get_feedback(session_id: str):
    """
    Get feedback for a specific session
    """
    try:
        feedback = await feedback_store.get_feedback(session_id)
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return feedback
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving feedback")
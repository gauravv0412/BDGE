"""Safe user feedback capture for presentation results."""

from app.feedback.storage import append_feedback_record
from app.feedback.validation import FeedbackValidationError, validate_feedback_payload

__all__ = ["FeedbackValidationError", "append_feedback_record", "validate_feedback_payload"]

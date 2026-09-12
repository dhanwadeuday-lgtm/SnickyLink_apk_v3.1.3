from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from ..models.analytics import AnalyticsEvent

class AnalyticsService:
    @staticmethod
    def log_event(
        db: Session,
        event_name: str,
        user_id: Optional[str] = None,
        couple_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Logs a domain event for analytics.
        """
        event = AnalyticsEvent(
            event_name=event_name,
            user_id=user_id,
            couple_id=couple_id,
            properties=properties
        )
        db.add(event)
        db.commit()

# Singleton for the app
analytics_service = AnalyticsService()

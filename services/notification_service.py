"""
Notification service
"""
from typing import List, Dict, Any
from patterns.observer.observer import NotificationObserver, Observer
from patterns.facade.banking_facade_db import BankingFacadeDB


class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self, banking_facade: BankingFacadeDB):
        self.facade = banking_facade
        self.notification_observer = NotificationObserver()
        self.facade.addObserver(self.notification_observer)
    
    def get_notifications(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        return self.notification_observer.get_notifications(user_id)


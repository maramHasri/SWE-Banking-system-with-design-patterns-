"""
Observer Pattern for notifications and event handling
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum


class EventType(Enum):
    """Types of events that can be observed"""
    TRANSACTION_COMPLETED = "transaction_completed"
    BALANCE_CHANGED = "balance_changed"
    ACCOUNT_STATE_CHANGED = "account_state_changed"
    TRANSACTION_APPROVED = "transaction_approved"
    TRANSACTION_REJECTED = "transaction_rejected"


class Observer(ABC):
    """Observer interface"""
    
    @abstractmethod
    def update(self, event_type: EventType, data: Dict[str, Any]):
        """Receive notification of an event"""
        pass


class Subject(ABC):
    """Subject interface for Observer pattern"""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def addObserver(self, observer: Observer):
        """Attach an observer"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def removeObserver(self, observer: Observer):
        """Detach an observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notifyObserver(self, event_type: EventType, data: Dict[str, Any]):
        """Notify all observers"""
        for observer in self._observers:
            observer.update(event_type, data)


class NotificationObserver(Observer):
    """Observer that sends notifications"""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
    
    def update(self, event_type: EventType, data: Dict[str, Any]):
        """Handle notification event"""
        notification = {
            'event_type': event_type.value,
            'data': data,
            'timestamp': data.get('timestamp')
        }
        self.notifications.append(notification)
        print(f"📧 Notification: {event_type.value} - {data.get('message', '')}")
    
    def get_notifications(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get notifications, optionally filtered by user"""
        if user_id:
            return [n for n in self.notifications 
                   if n['data'].get('user_id') == user_id]
        return self.notifications


class AuditLogObserver(Observer):
    """Observer that logs events for audit purposes"""
    
    def __init__(self):
        self.audit_logs: List[Dict[str, Any]] = []
    
    def update(self, event_type: EventType, data: Dict[str, Any]):
        """Log event for audit"""
        log_entry = {
            'event_type': event_type.value,
            'data': data,
            'timestamp': data.get('timestamp')
        }
        self.audit_logs.append(log_entry)
        from utils.logger import logger
        logger.info(f"Audit: {event_type.value} - {data}")


class ReportingObserver(Observer):
    """Observer that generates reports"""
    
    def __init__(self):
        self.reports: List[Dict[str, Any]] = []
    
    def update(self, event_type: EventType, data: Dict[str, Any]):
        """Generate report entry"""
        report_entry = {
            'event_type': event_type.value,
            'data': data,
            'timestamp': data.get('timestamp')
        }
        self.reports.append(report_entry)


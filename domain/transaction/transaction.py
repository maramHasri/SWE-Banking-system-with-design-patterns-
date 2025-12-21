"""
Transaction domain model
"""
from enum import Enum
from datetime import datetime
from typing import Optional


class TransactionType(Enum):
    """Types of transactions"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatus(Enum):
    """Transaction status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Transaction:
    """Transaction model"""
    
    def __init__(self, transaction_id: str, transaction_type: TransactionType,
                 account_id: str, amount: float, 
                 target_account_id: Optional[str] = None,
                 description: str = ""):
        self.transaction_id = transaction_id
        self.transaction_type = transaction_type
        self.account_id = account_id
        self.target_account_id = target_account_id
        self.amount = amount
        self.status = TransactionStatus.PENDING
        self.description = description
        self.created_at = datetime.now()
        self.approved_by: Optional[str] = None
        self.approved_at: Optional[datetime] = None
    
    def approve(self, approver: str):
        """Approve the transaction"""
        self.status = TransactionStatus.APPROVED
        self.approved_by = approver
        self.approved_at = datetime.now()
    
    def reject(self):
        """Reject the transaction"""
        self.status = TransactionStatus.REJECTED
    
    def complete(self):
        """Mark transaction as completed"""
        self.status = TransactionStatus.COMPLETED
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary"""
        return {
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type.value,
            'account_id': self.account_id,
            'target_account_id': self.target_account_id,
            'amount': self.amount,
            'status': self.status.value,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }


"""
Approval service for transaction approvals
"""
from typing import List
from domain.transaction.transaction import Transaction
from domain.roles.role import Role
from patterns.facade.banking_facade_db import BankingFacadeDB


class ApprovalService:
    """Service for transaction approvals"""
    
    def __init__(self, banking_facade: BankingFacadeDB):
        self.facade = banking_facade
    
    def get_pending_approvals(self, user_role: Role) -> List[Transaction]:
        """Get transactions pending approval for a role"""
        pending = self.facade.get_pending_transactions()
        
        if user_role == Role.ADMIN:
            # Admin can see all pending
            return pending
        elif user_role == Role.EMPLOYEE:
            # Employee can see medium-value transactions
            from config import EMPLOYEE_APPROVE_THRESHOLD
            return [t for t in pending if t.amount <= EMPLOYEE_APPROVE_THRESHOLD]
        else:
            return []
    
    def approve_transaction(self, transaction_id: str, approver_role: Role, approver_id: str) -> bool:
        """Approve a transaction"""
        return self.facade.approve_transaction(transaction_id, approver_role, approver_id)
    
    def complete_transaction(self, transaction_id: str, executor_role: Role, executor_id: str) -> bool:
        """Execute an approved transaction and mark it as completed"""
        return self.facade.complete_transaction(transaction_id, executor_role, executor_id)
    
    def deny_transaction(self, transaction_id: str, approver_role: Role, approver_id: str) -> bool:
        """Deny/reject a transaction"""
        return self.facade.deny_transaction(transaction_id, approver_role, approver_id)


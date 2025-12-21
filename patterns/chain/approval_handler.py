"""
Chain of Responsibility Pattern for transaction approval workflow
"""
from abc import ABC, abstractmethod
from typing import Optional
from domain.transaction.transaction import Transaction
from domain.roles.role import Role
from config import AUTO_APPROVE_THRESHOLD, EMPLOYEE_APPROVE_THRESHOLD


class ApprovalHandler(ABC):
    """Base handler for approval chain"""
    
    def __init__(self):
        self._next_handler: Optional['ApprovalHandler'] = None
    
    def set_next(self, handler: 'ApprovalHandler') -> 'ApprovalHandler':
        """Set the next handler in the chain"""
        self._next_handler = handler
        return handler
    
    @abstractmethod
    def handle(self, transaction: Transaction, user_role: Role) -> bool:
        """
        Handle approval request
        Returns True if approved, False if rejected, None if passed to next handler
        """
        pass
    
    def _pass_to_next(self, transaction: Transaction, user_role: Role) -> Optional[bool]:
        """Pass request to next handler"""
        if self._next_handler:
            return self._next_handler.handle(transaction, user_role)
        return None


class AutoApprovalHandler(ApprovalHandler):
    """Handles auto-approval for small transactions"""
    
    def handle(self, transaction: Transaction, user_role: Role) -> Optional[bool]:
        """Auto-approve transactions below threshold"""
        if transaction.amount <= AUTO_APPROVE_THRESHOLD:
            transaction.approve("System")
            from utils.logger import log_approval
            log_approval(transaction.transaction_id, "System", "Auto-approved")
            return True
        return self._pass_to_next(transaction, user_role)


class EmployeeApprovalHandler(ApprovalHandler):
    """Handles employee approval for medium transactions"""
    
    def handle(self, transaction: Transaction, user_role: Role) -> Optional[bool]:
        """Employee can approve medium transactions"""
        if AUTO_APPROVE_THRESHOLD < transaction.amount <= EMPLOYEE_APPROVE_THRESHOLD:
            if user_role in [Role.EMPLOYEE, Role.ADMIN]:
                transaction.approve(f"{user_role.value.title()}")
                from utils.logger import log_approval
                log_approval(transaction.transaction_id, user_role.value, "Approved")
                return True
            else:
                # Transaction needs employee approval but user is not employee/admin
                return None  # Pass to next or wait for approval
        return self._pass_to_next(transaction, user_role)


class AdminApprovalHandler(ApprovalHandler):
    """Handles admin approval for large transactions"""
    
    def handle(self, transaction: Transaction, user_role: Role) -> Optional[bool]:
        """Admin can approve large transactions"""
        if transaction.amount > EMPLOYEE_APPROVE_THRESHOLD:
            if user_role == Role.ADMIN:
                transaction.approve("Admin")
                from utils.logger import log_approval
                log_approval(transaction.transaction_id, "Admin", "Approved")
                return True
            else:
                # Transaction needs admin approval
                return None  # Wait for admin approval
        return self._pass_to_next(transaction, user_role)


class ApprovalChain:
    """Builder for approval chain"""
    
    @staticmethod
    def create_chain() -> ApprovalHandler:
        """Create the approval chain"""
        auto_handler = AutoApprovalHandler()
        employee_handler = EmployeeApprovalHandler()
        admin_handler = AdminApprovalHandler()
        
        auto_handler.set_next(employee_handler).set_next(admin_handler)
        return auto_handler


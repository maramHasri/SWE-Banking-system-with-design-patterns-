"""
Transaction service - business logic for transactions
"""
from typing import List
from domain.transaction.transaction import Transaction
from domain.roles.role import Role
from patterns.facade.banking_facade_db import BankingFacadeDB
from utils.exceptions import InvalidTransactionError


class TransactionService:
    """Service for transaction operations"""
    
    def __init__(self, banking_facade: BankingFacadeDB):
        self.facade = banking_facade
    
    def deposit(self, account_id: str, amount: float, description: str = "",
               user_role: Role = Role.CUSTOMER, user_id: str = None) -> Transaction:
        """
        Deposit funds into any account.
        Anyone (customer, employee, admin) can deposit into any account.
        """
        return self.facade.deposit(account_id, amount, description, user_role, user_id)
    
    def withdraw(self, account_id: str, amount: float, description: str = "",
                user_role: Role = Role.CUSTOMER, user_id: str = None,
                authenticated_account_id: str = None) -> Transaction:
        """
        Withdraw funds from account.
        For account-based auth: authenticated_account_id must match account_id.
        For user-based auth: Customers can only withdraw from their own accounts.
        Employees and admins can withdraw from any account.
        """
        return self.facade.withdraw(account_id, amount, description, user_role, user_id, authenticated_account_id)
    
    def transfer(self, from_account_id: str, to_account_id: str, 
                amount: float, description: str = "",
                user_role: Role = Role.CUSTOMER, user_id: str = None,
                authenticated_account_id: str = None) -> Transaction:
        """
        Transfer funds between accounts.
        For account-based auth: authenticated_account_id must match from_account_id.
        For user-based auth: Customers can only transfer from their own accounts.
        Employees and admins can transfer from any account to any account.
        """
        return self.facade.transfer(from_account_id, to_account_id, amount, description, user_role, user_id, authenticated_account_id)
    
    def approve_transaction(self, transaction_id: str, approver_role: Role, approver_id: str) -> bool:
        """Approve a pending transaction"""
        return self.facade.approve_transaction(transaction_id, approver_role, approver_id)
    
    def get_pending_transactions(self) -> List[Transaction]:
        """Get pending transactions"""
        return self.facade.get_pending_transactions()
    
    def get_account_transactions(self, account_id: str) -> List[Transaction]:
        """Get transactions for an account"""
        return self.facade.get_transactions_by_account(account_id)
    
    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions"""
        return self.facade.get_all_transactions()


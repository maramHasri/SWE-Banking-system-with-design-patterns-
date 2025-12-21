"""
Account service - business logic for account operations
"""
from typing import List, Optional
from domain.account.account import Account
from domain.account.account_type import AccountType
from domain.roles.role import Role
from patterns.facade.banking_facade import BankingFacade
from utils.exceptions import AccountNotFoundError, UnauthorizedOperationError


class AccountService:
    """Service for account management"""
    
    def __init__(self, banking_facade: BankingFacade):
        self.facade = banking_facade
    
    def create_account(self, account_type: AccountType, owner_id: str, 
                     initial_balance: float = 0.0, user_role: Role = None) -> Account:
        """
        Create a new account
        
        Args:
            account_type: Type of account to create
            owner_id: ID of the account owner
            initial_balance: Initial balance for the account
            user_role: Role of the user attempting to create the account
            
        Returns:
            Created Account object
            
        Raises:
            UnauthorizedOperationError: If user_role is CUSTOMER (only employees/admins can create accounts)
        """
        # Enforce authorization: Only employees and admins can create accounts
        if user_role is not None and user_role == Role.CUSTOMER:
            raise UnauthorizedOperationError(
                "Customers are not allowed to create accounts. Please contact an employee to create an account for you."
            )
        
        return self.facade.create_account(account_type, owner_id, initial_balance)
    
    def get_account(self, account_id: str) -> Account:
        """Get account by ID"""
        return self.facade.get_account(account_id)
    
    def get_user_accounts(self, user_id: str) -> List[Account]:
        """Get all accounts for a user"""
        return self.facade.get_accounts_by_owner(user_id)
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts (admin/employee only)"""
        return self.facade.get_all_accounts()
    
    def change_account_state(self, account_id: str, state: str, user_role):
        """Change account state"""
        from domain.roles.role import Role
        role = Role(user_role) if isinstance(user_role, str) else user_role
        return self.facade.change_account_state(account_id, state, role)


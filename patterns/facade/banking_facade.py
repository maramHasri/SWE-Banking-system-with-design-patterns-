"""
Facade Pattern - Unified interface for all banking operations
"""
from typing import List, Optional, Dict, Any
from domain.account.account import Account
from domain.account.account_type import AccountType
from domain.transaction.transaction import Transaction, TransactionType, TransactionStatus
from domain.roles.role import Role
from domain.state.account_state import ActiveState, FrozenState, SuspendedState, ClosedState
from patterns.observer.observer import Subject, EventType
from patterns.chain.approval_handler import ApprovalChain
from utils.exceptions import (
    InvalidTransactionError, UnauthorizedAccessError, 
    AccountNotFoundError, InsufficientFundsError
)
from datetime import datetime
import uuid


class BankingFacade(Subject):
    """
    Facade providing unified interface for all banking operations
    Hides complexity of transactions, approvals, notifications, etc.
    """
    
    def __init__(self):
        super().__init__()
        self.accounts: Dict[str, Account] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.approval_chain = ApprovalChain.create_chain()
        self.retained_earnings = 0.0  # Bank's retained earnings
    
    # Account Management
    def create_account(self, account_type: AccountType, owner_id: str, 
                      initial_balance: float = 0.0, 
                      parent_account_id: Optional[str] = None) -> Account:
        """Create a new account"""
        account_id = f"ACC_{uuid.uuid4().hex[:8].upper()}"
        account = Account(account_id, account_type, owner_id, initial_balance, parent_account_id)
        self.accounts[account_id] = account
        
        self.notify(EventType.ACCOUNT_STATE_CHANGED, {
            'account_id': account_id,
            'state': account.get_state_name(),
            'message': f"Account {account_id} created",
            'timestamp': datetime.now().isoformat()
        })
        
        return account
    
    def get_account(self, account_id: str) -> Account:
        """Get account by ID"""
        if account_id not in self.accounts:
            raise AccountNotFoundError(f"Account {account_id} not found")
        return self.accounts[account_id]
    
    def get_accounts_by_owner(self, owner_id: str) -> List[Account]:
        """Get all accounts for an owner"""
        return [acc for acc in self.accounts.values() if acc.owner_id == owner_id]
    
    def change_account_state(self, account_id: str, state_name: str, user_role: Role):
        """Change account state (requires appropriate role)"""
        if user_role not in [Role.EMPLOYEE, Role.ADMIN]:
            raise UnauthorizedAccessError("Only employees and admins can change account state")
        
        account = self.get_account(account_id)
        
        state_map = {
            'active': ActiveState(),
            'frozen': FrozenState(),
            'suspended': SuspendedState(),
            'closed': ClosedState()
        }
        
        if state_name.lower() not in state_map:
            raise InvalidTransactionError(f"Invalid state: {state_name}")
        
        account.set_state(state_map[state_name.lower()])
        
        self.notify(EventType.ACCOUNT_STATE_CHANGED, {
            'account_id': account_id,
            'state': account.get_state_name(),
            'changed_by': user_role.value,
            'message': f"Account {account_id} state changed to {state_name}",
            'timestamp': datetime.now().isoformat()
        })
    
    # Transaction Operations
    def deposit(self, account_id: str, amount: float, description: str = "",
               user_role: Role = Role.CUSTOMER) -> Transaction:
        """Deposit funds into account"""
        account = self.get_account(account_id)
        
        # Check authorization
        if user_role == Role.CUSTOMER and account.owner_id != getattr(self, '_current_user_id', None):
            raise UnauthorizedAccessError("Customers can only deposit to their own accounts")
        
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        transaction = Transaction(transaction_id, TransactionType.DEPOSIT, 
                                 account_id, amount, description=description)
        self.transactions[transaction_id] = transaction
        
        # Process through approval chain
        approved = self.approval_chain.handle(transaction, user_role)
        
        if approved:
            if account.deposit(amount):
                transaction.complete()
                self.notify(EventType.TRANSACTION_COMPLETED, {
                    'transaction_id': transaction_id,
                    'account_id': account_id,
                    'amount': amount,
                    'type': 'deposit',
                    'message': f"Deposit of ${amount:.2f} completed",
                    'timestamp': datetime.now().isoformat()
                })
                self.notify(EventType.BALANCE_CHANGED, {
                    'account_id': account_id,
                    'new_balance': account.balance,
                    'message': f"Balance updated to ${account.balance:.2f}",
                    'timestamp': datetime.now().isoformat()
                })
            else:
                transaction.reject()
        else:
            # Pending approval
            pass
        
        return transaction
    
    def withdraw(self, account_id: str, amount: float, description: str = "",
                user_role: Role = Role.CUSTOMER) -> Transaction:
        """Withdraw funds from account"""
        account = self.get_account(account_id)
        
        # Check authorization
        if user_role == Role.CUSTOMER and account.owner_id != getattr(self, '_current_user_id', None):
            raise UnauthorizedAccessError("Customers can only withdraw from their own accounts")
        
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        transaction = Transaction(transaction_id, TransactionType.WITHDRAWAL, 
                                 account_id, amount, description=description)
        self.transactions[transaction_id] = transaction
        
        # Process through approval chain
        approved = self.approval_chain.handle(transaction, user_role)
        
        if approved:
            try:
                if account.withdraw(amount):
                    transaction.complete()
                    self.notify(EventType.TRANSACTION_COMPLETED, {
                        'transaction_id': transaction_id,
                        'account_id': account_id,
                        'amount': amount,
                        'type': 'withdrawal',
                        'message': f"Withdrawal of ${amount:.2f} completed",
                        'timestamp': datetime.now().isoformat()
                    })
                    self.notify(EventType.BALANCE_CHANGED, {
                        'account_id': account_id,
                        'new_balance': account.balance,
                        'message': f"Balance updated to ${account.balance:.2f}",
                        'timestamp': datetime.now().isoformat()
                    })
            except InsufficientFundsError as e:
                transaction.reject()
                raise
        else:
            # Pending approval
            pass
        
        return transaction
    
    def transfer(self, from_account_id: str, to_account_id: str, 
                amount: float, description: str = "",
                user_role: Role = Role.CUSTOMER) -> Transaction:
        """Transfer funds between accounts"""
        from_account = self.get_account(from_account_id)
        to_account = self.get_account(to_account_id)
        
        # Check authorization
        if user_role == Role.CUSTOMER and from_account.owner_id != getattr(self, '_current_user_id', None):
            raise UnauthorizedAccessError("Customers can only transfer from their own accounts")
        
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        transaction = Transaction(transaction_id, TransactionType.TRANSFER, 
                                 from_account_id, amount, 
                                 target_account_id=to_account_id,
                                 description=description)
        self.transactions[transaction_id] = transaction
        
        # Process through approval chain
        approved = self.approval_chain.handle(transaction, user_role)
        
        if approved:
            try:
                if from_account.transfer(amount) and to_account.deposit(amount):
                    from_account.withdraw(amount)  # Actually withdraw
                    transaction.complete()
                    self.notify(EventType.TRANSACTION_COMPLETED, {
                        'transaction_id': transaction_id,
                        'account_id': from_account_id,
                        'target_account_id': to_account_id,
                        'amount': amount,
                        'type': 'transfer',
                        'message': f"Transfer of ${amount:.2f} completed",
                        'timestamp': datetime.now().isoformat()
                    })
                    self.notify(EventType.BALANCE_CHANGED, {
                        'account_id': from_account_id,
                        'new_balance': from_account.balance,
                        'message': f"Balance updated to ${from_account.balance:.2f}",
                        'timestamp': datetime.now().isoformat()
                    })
                    self.notify(EventType.BALANCE_CHANGED, {
                        'account_id': to_account_id,
                        'new_balance': to_account.balance,
                        'message': f"Balance updated to ${to_account.balance:.2f}",
                        'timestamp': datetime.now().isoformat()
                    })
            except InsufficientFundsError as e:
                transaction.reject()
                raise
        else:
            # Pending approval
            pass
        
        return transaction
    
    def approve_transaction(self, transaction_id: str, approver_role: Role, approver_id: str) -> bool:
        """Manually approve a pending transaction"""
        if transaction_id not in self.transactions:
            raise InvalidTransactionError(f"Transaction {transaction_id} not found")
        
        transaction = self.transactions[transaction_id]
        
        if transaction.status != TransactionStatus.PENDING:
            raise InvalidTransactionError("Transaction is not pending approval")
        
        # Check if approver has permission
        if transaction.amount > 75000 and approver_role != Role.ADMIN:
            raise UnauthorizedAccessError("Only admin can approve transactions over $75,000")
        elif transaction.amount > 25000 and approver_role not in [Role.EMPLOYEE, Role.ADMIN]:
            raise UnauthorizedAccessError("Only employees/admins can approve transactions over $25,000")
        
        transaction.approve(approver_id)
        
        # Execute the transaction
        account = self.get_account(transaction.account_id)
        
        if transaction.transaction_type == TransactionType.DEPOSIT:
            account.deposit(transaction.amount)
            transaction.complete()
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            account.withdraw(transaction.amount)
            transaction.complete()
        elif transaction.transaction_type == TransactionType.TRANSFER:
            target_account = self.get_account(transaction.target_account_id)
            account.withdraw(transaction.amount)
            target_account.deposit(transaction.amount)
            transaction.complete()
        
        self.notify(EventType.TRANSACTION_APPROVED, {
            'transaction_id': transaction_id,
            'approver': approver_id,
            'message': f"Transaction {transaction_id} approved by {approver_id}",
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    # Reporting
    def get_pending_transactions(self) -> List[Transaction]:
        """Get all pending transactions"""
        return [t for t in self.transactions.values() 
               if t.status == TransactionStatus.PENDING]
    
    def get_transactions_by_account(self, account_id: str) -> List[Transaction]:
        """Get all transactions for an account"""
        return [t for t in self.transactions.values() 
               if t.account_id == account_id or t.target_account_id == account_id]
    
    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions"""
        return list(self.transactions.values())
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts"""
        return list(self.accounts.values())
    
    # Bank financials
    def update_retained_earnings(self, net_income: float, dividends: float):
        """Update bank's retained earnings"""
        self.retained_earnings += net_income - dividends
    
    def get_retained_earnings(self) -> float:
        """Get bank's retained earnings"""
        return self.retained_earnings
    
    def set_current_user(self, user_id: str):
        """Set current user for authorization checks"""
        self._current_user_id = user_id


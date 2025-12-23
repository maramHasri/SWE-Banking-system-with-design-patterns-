"""
Database-enabled Banking Facade
Uses PostgreSQL database for persistent storage
"""
from typing import List, Optional, Dict, Any
from domain.account.account import Account
from domain.account.account_type import AccountType
from domain.transaction.transaction import Transaction, TransactionType, TransactionStatus
from domain.roles.role import Role
from patterns.state.account_state import ActiveState, FrozenState, SuspendedState, ClosedState
from patterns.observer.observer import Subject, EventType
from patterns.chain.approval_handler import ApprovalChain
from database.repository import AccountRepository, TransactionRepository, FinancialsRepository
from database.models import AccountStateEnum, TransactionStatusEnum
from utils.exceptions import (
    InvalidTransactionError, UnauthorizedAccessError, 
    AccountNotFoundError, InsufficientFundsError, FrozenAccountError
)
from datetime import datetime
import uuid


class BankingFacadeDB(Subject):
    """
    Database-enabled Facade providing unified interface for all banking operations
    Uses PostgreSQL for persistent storage
    """
    
    def __init__(self):
        super().__init__()
        self.approval_chain = ApprovalChain.create_chain()
    
    # Account Management
    def create_account(self, account_type: AccountType, owner_id: str, 
                      initial_balance: float = 0.0, 
                      parent_account_id: Optional[str] = None) -> Account:
        """Create a new account"""
        account_id = f"ACC_{uuid.uuid4().hex[:8].upper()}"
        
        # Create in database
        db_account = AccountRepository.create(
            account_id, account_type, owner_id, initial_balance, parent_account_id
        )
        
        # Convert to domain object
        account = AccountRepository.to_domain_account(db_account)
        
        self.notifyObserver(EventType.ACCOUNT_STATE_CHANGED, {
            'account_id': account_id,
            'state': account.get_state_name(),
            'message': f"Account {account_id} created",
            'timestamp': datetime.now().isoformat()
        })
        
        return account
    
    def get_account(self, account_id: str) -> Account:
        """Get account by ID"""
        db_account = AccountRepository.get(account_id)
        return AccountRepository.to_domain_account(db_account)
    
    def get_accounts_by_owner(self, owner_id: str) -> List[Account]:
        """Get all accounts for an owner"""
        db_accounts = AccountRepository.get_by_owner(owner_id)
        return [AccountRepository.to_domain_account(acc) for acc in db_accounts]
    
    def get_all_accounts(self) -> List[Account]:
        """Get all accounts"""
        db_accounts = AccountRepository.get_all()
        return [AccountRepository.to_domain_account(acc) for acc in db_accounts]
    
    def change_account_state(self, account_id: str, state_name: str, user_role: Role):
        """Change account state (requires appropriate role)"""
        if user_role not in [Role.EMPLOYEE, Role.ADMIN]:
            raise UnauthorizedAccessError("Only employees and admins can change account state")
        
        account = self.get_account(account_id)
        
        state_map = {
            'active': AccountStateEnum.ACTIVE,
            'frozen': AccountStateEnum.FROZEN,
            'suspended': AccountStateEnum.SUSPENDED,
            'closed': AccountStateEnum.CLOSED
        }
        
        if state_name.lower() not in state_map:
            raise InvalidTransactionError(f"Invalid state: {state_name}")
        
        # Update in database
        AccountRepository.update_state(account_id, state_map[state_name.lower()])
        
        # Reload account to get updated state
        account = self.get_account(account_id)
        
        self.notifyObserver(EventType.ACCOUNT_STATE_CHANGED, {
            'account_id': account_id,
            'state': account.get_state_name(),
            'changed_by': user_role.value,
            'message': f"Account {account_id} state changed to {state_name}",
            'timestamp': datetime.now().isoformat()
        })
    
    # Transaction Operations
    def deposit(self, account_id: str, amount: float, description: str = "",
               user_role: Role = Role.CUSTOMER, user_id: str = None) -> Transaction:
        """
        Deposit funds into account.
        ANYONE (customer, employee, admin) can deposit into ANY account.
        This allows deposits from external sources, third parties, etc.
        """
        account = self.get_account(account_id)
        
        # No authorization check - anyone can deposit to any account
        
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        
        # Create transaction in database
        db_transaction = TransactionRepository.create(
            transaction_id, TransactionType.DEPOSIT, account_id, amount, 
            description=description
        )
        transaction = TransactionRepository.to_domain_transaction(db_transaction)
        
        # Process through approval chain
        approved = self.approval_chain.handle(transaction, user_role)
        
        if approved:
            if account.deposit(amount):
                # Update account balance in database
                AccountRepository.update_balance(account_id, account.balance)
                # Update transaction status to COMPLETED after execution
                TransactionRepository.update_status(
                    transaction_id, TransactionStatusEnum.COMPLETED, "System"
                )
                transaction.complete()
                
                self.notifyObserver(EventType.TRANSACTION_COMPLETED, {
                    'transaction_id': transaction_id,
                    'account_id': account_id,
                    'amount': amount,
                    'type': 'deposit',
                    'message': f"Deposit of ${amount:.2f} completed",
                    'timestamp': datetime.now().isoformat()
                })
                self.notifyObserver(EventType.BALANCE_CHANGED, {
                    'account_id': account_id,
                    'new_balance': account.balance,
                    'message': f"Balance updated to ${account.balance:.2f}",
                    'timestamp': datetime.now().isoformat()
                })
        
        return transaction
    
    def withdraw(self, account_id: str, amount: float, description: str = "",
                user_role: Role = Role.CUSTOMER, user_id: str = None,
                authenticated_account_id: str = None) -> Transaction:
        """
        Withdraw funds from account.
        For account-based authentication: authenticated_account_id must match account_id.
        For user-based authentication: Customers can only withdraw from their own accounts.
        Employees and admins can withdraw from any account.
        Balance is verified before withdrawal.
        """
        account = self.get_account(account_id)
        
        # Account-based authentication (account_id + IBAN)
        if authenticated_account_id:
            if account_id != authenticated_account_id:
                raise UnauthorizedAccessError(
                    f"Security violation: You can only withdraw from the account you authenticated with. "
                    f"Authenticated: {authenticated_account_id}, Requested: {account_id}"
                )
        # User-based authentication (legacy)
        elif user_role == Role.CUSTOMER:
            current_user_id = user_id or getattr(self, '_current_user_id', None)
            if account.owner_id != current_user_id:
                raise UnauthorizedAccessError(
                    f"Security violation: Customers can only withdraw from their own accounts. "
                    f"Account {account_id} belongs to {account.owner_id}, not {current_user_id}"
                )
        
        # Balance verification is done in account.withdraw() which raises InsufficientFundsError
        
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        
        # Create transaction in database
        db_transaction = TransactionRepository.create(
            transaction_id, TransactionType.WITHDRAWAL, account_id, amount, 
            description=description
        )
        transaction = TransactionRepository.to_domain_transaction(db_transaction)
        
        # Process through approval chain
        approved = self.approval_chain.handle(transaction, user_role)
        
        if approved:
            try:
                if account.withdraw(amount):
                    # Update account balance in database
                    AccountRepository.update_balance(account_id, account.balance)
                    # Transaction is already approved by approval chain
                    # Status remains APPROVED after execution
                    
                    self.notifyObserver(EventType.TRANSACTION_APPROVED, {
                        'transaction_id': transaction_id,
                        'account_id': account_id,
                        'amount': amount,
                        'type': 'withdrawal',
                        'message': f"Withdrawal of ${amount:.2f} approved and executed",
                        'timestamp': datetime.now().isoformat()
                    })
                    self.notifyObserver(EventType.BALANCE_CHANGED, {
                        'account_id': account_id,
                        'new_balance': account.balance,
                        'message': f"Balance updated to ${account.balance:.2f}",
                        'timestamp': datetime.now().isoformat()
                    })
            except (InsufficientFundsError, FrozenAccountError) as e:
                TransactionRepository.update_status(transaction_id, TransactionStatusEnum.REJECTED)
                transaction.reject()
                raise
        
        return transaction
    
    def transfer(self, from_account_id: str, to_account_id: str, 
                amount: float, description: str = "",
                user_role: Role = Role.CUSTOMER, user_id: str = None,
                authenticated_account_id: str = None) -> Transaction:
        """
        Transfer funds between accounts.
        For account-based authentication: authenticated_account_id must match from_account_id.
        For user-based authentication: Customers can only transfer from their own accounts.
        Employees and admins can transfer from any account to any account.
        Transfer is atomic - both accounts are updated together or not at all.
        """
        from_account = self.get_account(from_account_id)
        to_account = self.get_account(to_account_id)
        
        # Validate accounts exist
        if not from_account:
            raise AccountNotFoundError(f"Source account {from_account_id} not found")
        if not to_account:
            raise AccountNotFoundError(f"Destination account {to_account_id} not found")
        
        # Account-based authentication (account_id + IBAN)
        if authenticated_account_id:
            if from_account_id != authenticated_account_id:
                raise UnauthorizedAccessError(
                    f"Security violation: You can only transfer from the account you authenticated with. "
                    f"Authenticated: {authenticated_account_id}, Requested: {from_account_id}"
                )
        # User-based authentication (legacy)
        elif user_role == Role.CUSTOMER:
            current_user_id = user_id or getattr(self, '_current_user_id', None)
            if from_account.owner_id != current_user_id:
                raise UnauthorizedAccessError(
                    f"Security violation: Customers can only transfer from their own accounts. "
                    f"Account {from_account_id} belongs to {from_account.owner_id}, not {current_user_id}"
                )
        
        # Verify sufficient balance in source account (done in account.transfer())
        # This will raise InsufficientFundsError if balance is insufficient
        
        transaction_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        
        # Create transaction in database
        db_transaction = TransactionRepository.create(
            transaction_id, TransactionType.TRANSFER, from_account_id, amount,
            target_account_id=to_account_id, description=description
        )
        transaction = TransactionRepository.to_domain_transaction(db_transaction)
        
        # Process through approval chain
        approved = self.approval_chain.handle(transaction, user_role)
        
        if approved:
            # Use database transaction for atomicity
            from database.db import db
            try:
                # Verify transfer is allowed (checks balance)
                if not from_account.transfer(amount):
                    raise InsufficientFundsError("Transfer validation failed")
                
                # Perform atomic transfer: withdraw from source, deposit to destination
                from_account.withdraw(amount)  # This also verifies balance
                to_account.deposit(amount)
                
                # Update balances in database atomically
                AccountRepository.update_balance(from_account_id, from_account.balance)
                AccountRepository.update_balance(to_account_id, to_account.balance)
                
                # Update transaction status to COMPLETED after execution
                TransactionRepository.update_status(
                    transaction_id, TransactionStatusEnum.COMPLETED, "System"
                )
                transaction.complete()
                
                # Commit all changes atomically
                db.session.commit()
                
                self.notifyObserver(EventType.TRANSACTION_COMPLETED, {
                    'transaction_id': transaction_id,
                    'account_id': from_account_id,
                    'target_account_id': to_account_id,
                    'amount': amount,
                    'type': 'transfer',
                    'message': f"Transfer of ${amount:.2f} completed",
                    'timestamp': datetime.now().isoformat()
                })
                self.notifyObserver(EventType.BALANCE_CHANGED, {
                    'account_id': from_account_id,
                    'new_balance': from_account.balance,
                    'message': f"Balance updated to ${from_account.balance:.2f}",
                    'timestamp': datetime.now().isoformat()
                })
                self.notifyObserver(EventType.BALANCE_CHANGED, {
                    'account_id': to_account_id,
                    'new_balance': to_account.balance,
                    'message': f"Balance updated to ${to_account.balance:.2f}",
                    'timestamp': datetime.now().isoformat()
                })
            except (InsufficientFundsError, AccountNotFoundError, FrozenAccountError) as e:
                # Rollback database changes on error for atomicity
                db.session.rollback()
                TransactionRepository.update_status(transaction_id, TransactionStatusEnum.REJECTED)
                transaction.reject()
                raise
            except Exception as e:
                # Rollback on any unexpected error
                db.session.rollback()
                TransactionRepository.update_status(transaction_id, TransactionStatusEnum.REJECTED)
                transaction.reject()
                raise InvalidTransactionError(f"Transfer failed: {str(e)}")
        
        return transaction
    
    def approve_transaction(self, transaction_id: str, approver_role: Role, approver_id: str) -> bool:
        """Manually approve a pending transaction"""
        db_transaction = TransactionRepository.get(transaction_id)
        if not db_transaction:
            raise InvalidTransactionError(f"Transaction {transaction_id} not found")
        
        transaction = TransactionRepository.to_domain_transaction(db_transaction)
        
        if transaction.status != TransactionStatus.PENDING:
            raise InvalidTransactionError("Transaction is not pending approval")
        
        # Check if approver has permission
        if transaction.amount > 75000 and approver_role != Role.ADMIN:
            raise UnauthorizedAccessError("Only admin can approve transactions over $75,000")
        elif transaction.amount > 25000 and approver_role not in [Role.EMPLOYEE, Role.ADMIN]:
            raise UnauthorizedAccessError("Only employees/admins can approve transactions over $25,000")
        
        # Execute the transaction first
        account = self.get_account(transaction.account_id)
        
        try:
            if transaction.transaction_type == TransactionType.DEPOSIT:
                account.deposit(transaction.amount)
                AccountRepository.update_balance(transaction.account_id, account.balance)
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                account.withdraw(transaction.amount)
                AccountRepository.update_balance(transaction.account_id, account.balance)
            elif transaction.transaction_type == TransactionType.TRANSFER:
                target_account = self.get_account(transaction.target_account_id)
                account.withdraw(transaction.amount)
                target_account.deposit(transaction.amount)
                AccountRepository.update_balance(transaction.account_id, account.balance)
                AccountRepository.update_balance(transaction.target_account_id, target_account.balance)
            
            # Update transaction status in database to APPROVED first
            TransactionRepository.update_status(
                transaction_id, TransactionStatusEnum.APPROVED, approver_id
            )
            transaction.approve(approver_id)
            
            # Then update to COMPLETED after execution
            TransactionRepository.update_status(
                transaction_id, TransactionStatusEnum.COMPLETED, approver_id
            )
            transaction.complete()
        except (InsufficientFundsError, FrozenAccountError, AccountNotFoundError) as e:
            # If execution fails, reject the transaction
            TransactionRepository.update_status(transaction_id, TransactionStatusEnum.REJECTED, approver_id)
            transaction.reject()
            raise
        
        self.notifyObserver(EventType.TRANSACTION_APPROVED, {
            'transaction_id': transaction_id,
            'approver': approver_id,
            'message': f"Transaction {transaction_id} approved by {approver_id}",
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    def complete_transaction(self, transaction_id: str, executor_role: Role, executor_id: str) -> bool:
        """Execute an approved transaction and mark it as completed"""
        db_transaction = TransactionRepository.get(transaction_id)
        if not db_transaction:
            raise InvalidTransactionError(f"Transaction {transaction_id} not found")
        
        transaction = TransactionRepository.to_domain_transaction(db_transaction)
        
        if transaction.status != TransactionStatus.APPROVED:
            raise InvalidTransactionError("Transaction must be APPROVED before it can be completed")
        
        # Execute the transaction
        account = self.get_account(transaction.account_id)
        
        try:
            if transaction.transaction_type == TransactionType.DEPOSIT:
                account.deposit(transaction.amount)
                AccountRepository.update_balance(transaction.account_id, account.balance)
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                account.withdraw(transaction.amount)
                AccountRepository.update_balance(transaction.account_id, account.balance)
            elif transaction.transaction_type == TransactionType.TRANSFER:
                target_account = self.get_account(transaction.target_account_id)
                account.withdraw(transaction.amount)
                target_account.deposit(transaction.amount)
                AccountRepository.update_balance(transaction.account_id, account.balance)
                AccountRepository.update_balance(transaction.target_account_id, target_account.balance)
            
            # Update transaction status to COMPLETED after execution
            TransactionRepository.update_status(
                transaction_id, TransactionStatusEnum.COMPLETED, executor_id
            )
            transaction.complete()
            
            self.notifyObserver(EventType.TRANSACTION_COMPLETED, {
                'transaction_id': transaction_id,
                'executor': executor_id,
                'message': f"Transaction {transaction_id} executed and completed by {executor_id}",
                'timestamp': datetime.now().isoformat()
            })
            
            return True
        except (InsufficientFundsError, FrozenAccountError, AccountNotFoundError) as e:
            # If execution fails, keep transaction in APPROVED status
            raise
    
    def deny_transaction(self, transaction_id: str, approver_role: Role, approver_id: str) -> bool:
        """Manually deny/reject a pending transaction"""
        db_transaction = TransactionRepository.get(transaction_id)
        if not db_transaction:
            raise InvalidTransactionError(f"Transaction {transaction_id} not found")
        
        transaction = TransactionRepository.to_domain_transaction(db_transaction)
        
        if transaction.status != TransactionStatus.PENDING:
            raise InvalidTransactionError("Transaction is not pending approval")
        
        # Check if approver has permission
        if transaction.amount > 75000 and approver_role != Role.ADMIN:
            raise UnauthorizedAccessError("Only admin can deny transactions over $75,000")
        elif transaction.amount > 25000 and approver_role not in [Role.EMPLOYEE, Role.ADMIN]:
            raise UnauthorizedAccessError("Only employees/admins can deny transactions over $25,000")
        
        # Update transaction status to rejected in database
        TransactionRepository.update_status(
            transaction_id, TransactionStatusEnum.REJECTED, approver_id
        )
        transaction.reject()
        
        self.notifyObserver(EventType.TRANSACTION_APPROVED, {
            'transaction_id': transaction_id,
            'approver': approver_id,
            'message': f"Transaction {transaction_id} denied by {approver_id}",
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    # Reporting
    def get_pending_transactions(self) -> List[Transaction]:
        """Get all pending transactions"""
        db_transactions = TransactionRepository.get_pending()
        return [TransactionRepository.to_domain_transaction(t) for t in db_transactions]
    
    def get_transactions_by_account(self, account_id: str) -> List[Transaction]:
        """Get all transactions for an account"""
        db_transactions = TransactionRepository.get_by_account(account_id)
        return [TransactionRepository.to_domain_transaction(t) for t in db_transactions]
    
    def get_all_transactions(self) -> List[Transaction]:
        """Get all transactions"""
        db_transactions = TransactionRepository.get_all()
        return [TransactionRepository.to_domain_transaction(t) for t in db_transactions]
    
    # Bank financials
    def update_retained_earnings(self, net_income: float, dividends: float):
        """Update bank's retained earnings"""
        FinancialsRepository.update_earnings(net_income, dividends)
    
    def get_retained_earnings(self) -> float:
        """Get bank's retained earnings"""
        return FinancialsRepository.get_retained_earnings()
    
    def set_current_user(self, user_id: str):
        """Set current user for authorization checks"""
        self._current_user_id = user_id

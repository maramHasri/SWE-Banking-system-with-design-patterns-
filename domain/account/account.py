"""
Account domain model
"""
from typing import Optional
from datetime import datetime
from domain.account.account_type import AccountType
from domain.state.account_state import AccountState, ActiveState
from utils.exceptions import InvalidStateTransitionError, InsufficientFundsError


class Account:
    """Base account class"""
    
    def __init__(self, account_id: str, account_type: AccountType, owner_id: str, 
                 balance: float = 0.0, parent_account_id: Optional[str] = None,
                 iban: Optional[str] = None):
        self.account_id = account_id
        self.iban = iban
        self.account_type = account_type
        self.owner_id = owner_id
        self.balance = balance
        self.parent_account_id = parent_account_id
        self.state: AccountState = ActiveState()
        self.created_at = datetime.now()
        self.is_closed = False
    
    def set_state(self, new_state: AccountState):
        """Change account state"""
        if self.is_closed:
            from domain.state.account_state import ClosedState
            if not isinstance(new_state, ClosedState):
                raise InvalidStateTransitionError("Cannot change state of closed account")
        self.state = new_state
    
    def deposit(self, amount: float) -> bool:
        """Deposit funds into account"""
        if not self.state.deposit(self, amount):
            return False
        if amount <= 0:
            return False
        self.balance += amount
        return True
    
    def withdraw(self, amount: float) -> bool:
        """Withdraw funds from account"""
        if not self.state.withdraw(self, amount):
            from utils.exceptions import FrozenAccountError
            if self.get_state_name() == "Frozen":
                raise FrozenAccountError(
                    f"Cannot withdraw from frozen account {self.account_id}. "
                    f"Frozen accounts allow deposits and incoming transfers only. "
                    f"Please contact support to unfreeze the account."
                )
            return False
        if amount <= 0:
            return False
        if self.balance < amount:
            raise InsufficientFundsError(f"Insufficient funds. Balance: ${self.balance:.2f}, Requested: ${amount:.2f}")
        self.balance -= amount
        return True
    
    def transfer(self, amount: float) -> bool:
        """Check if outgoing transfer is allowed"""
        if not self.state.transfer(self, amount):
            from utils.exceptions import FrozenAccountError
            if self.get_state_name() == "Frozen":
                raise FrozenAccountError(
                    f"Cannot transfer from frozen account {self.account_id}. "
                    f"Frozen accounts allow deposits and incoming transfers only. "
                    f"Please contact support to unfreeze the account."
                )
            return False
        if amount <= 0:
            return False
        if self.balance < amount:
            raise InsufficientFundsError(f"Insufficient funds for transfer")
        return True
    
    def get_state_name(self) -> str:
        """Get current state name"""
        return self.state.get_state_name()
    
    def close(self):
        """Close the account"""
        from domain.state.account_state import ClosedState
        self.set_state(ClosedState())
        self.is_closed = True
    
    def to_dict(self) -> dict:
        """Convert account to dictionary"""
        return {
            'account_id': self.account_id,
            'iban': self.iban,
            'account_type': self.account_type.value,
            'owner_id': self.owner_id,
            'balance': self.balance,
            'parent_account_id': self.parent_account_id,
            'state': self.get_state_name(),
            'created_at': self.created_at.isoformat(),
            'is_closed': self.is_closed
        }


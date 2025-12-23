"""
Account State Pattern Implementation
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.account.account import Account


class AccountState(ABC):
    """Abstract state for account"""
    
    @abstractmethod
    def deposit(self, account: 'Account', amount: float) -> bool:
        """Attempt to deposit funds"""
        pass
    
    @abstractmethod
    def withdraw(self, account: 'Account', amount: float) -> bool:
        """Attempt to withdraw funds"""
        pass
    
    @abstractmethod
    def transfer(self, account: 'Account', amount: float) -> bool:
        """Attempt to transfer funds"""
        pass
    
    @abstractmethod
    def get_state_name(self) -> str:
        """Get the name of the current state"""
        pass


class ActiveState(AccountState):
    """Account is active and operational"""
    
    def deposit(self, account: 'Account', amount: float) -> bool:
        return True
    
    def withdraw(self, account: 'Account', amount: float) -> bool:
        return True
    
    def transfer(self, account: 'Account', amount: float) -> bool:
        return True
    
    def get_state_name(self) -> str:
        return "Active"


class FrozenState(AccountState):
    """
    Account is frozen - temporarily restricted due to security, legal, or compliance reasons.
    - Allows: Deposits and incoming transfers (funds coming IN)
    - Blocks: Withdrawals and outgoing transfers (funds going OUT)
    """
    
    def deposit(self, account: 'Account', amount: float) -> bool:
        """Deposits into frozen account are allowed"""
        return True
    
    def withdraw(self, account: 'Account', amount: float) -> bool:
        """Withdrawals from frozen account are strictly prohibited"""
        return False
    
    def transfer(self, account: 'Account', amount: float) -> bool:
        """
        Outgoing transfers from frozen account are not allowed.
        Note: Incoming transfers (to this account) are handled separately in the transfer logic.
        """
        return False
    
    def get_state_name(self) -> str:
        return "Frozen"


class SuspendedState(AccountState):
    """Account is suspended - limited operations"""
    
    def deposit(self, account: 'Account', amount: float) -> bool:
        return True  # Can receive deposits
    
    def withdraw(self, account: 'Account', amount: float) -> bool:
        return False  # Cannot withdraw
    
    def transfer(self, account: 'Account', amount: float) -> bool:
        return False  # Cannot transfer
    
    def get_state_name(self) -> str:
        return "Suspended"


class ClosedState(AccountState):
    """Account is closed - no operations allowed"""
    
    def deposit(self, account: 'Account', amount: float) -> bool:
        return False
    
    def withdraw(self, account: 'Account', amount: float) -> bool:
        return False
    
    def transfer(self, account: 'Account', amount: float) -> bool:
        return False
    
    def get_state_name(self) -> str:
        return "Closed"


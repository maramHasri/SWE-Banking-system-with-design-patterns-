"""
Composite Pattern for hierarchical account structures
"""
from abc import ABC, abstractmethod
from typing import List, Optional


class AccountComponent(ABC):
    """Component interface for Composite pattern"""
    
    @abstractmethod
    def get_account_id(self) -> str:
        """Get account ID"""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get total balance"""
        pass
    
    @abstractmethod
    def get_all_accounts(self) -> List['AccountComponent']:
        """Get all accounts (for composite, returns children)"""
        pass
    
    @abstractmethod
    def add_account(self, account: 'AccountComponent'):
        """Add child account (only for composites)"""
        pass
    
    @abstractmethod
    def remove_account(self, account_id: str):
        """Remove child account (only for composites)"""
        pass


class AccountLeaf(AccountComponent):
    """Leaf node - represents a single account"""
    
    def __init__(self, account):
        """Initialize with an Account object"""
        self.account = account
    
    def get_account_id(self) -> str:
        return self.account.account_id
    
    def get_balance(self) -> float:
        return self.account.balance
    
    def get_all_accounts(self) -> List[AccountComponent]:
        return [self]
    
    def add_account(self, account: AccountComponent):
        raise NotImplementedError("Cannot add account to leaf node")
    
    def remove_account(self, account_id: str):
        raise NotImplementedError("Cannot remove account from leaf node")
    
    def get_account(self):
        """Get the underlying account object"""
        return self.account


class AccountComposite(AccountComponent):
    """Composite node - represents a group of accounts"""
    
    def __init__(self, account_id: str, name: str):
        self.account_id = account_id
        self.name = name
        self.children: List[AccountComponent] = []
    
    def get_account_id(self) -> str:
        return self.account_id
    
    def get_balance(self) -> float:
        """Get total balance of all child accounts"""
        return sum(child.get_balance() for child in self.children)
    
    def get_all_accounts(self) -> List[AccountComponent]:
        """Get all accounts recursively"""
        accounts = []
        for child in self.children:
            accounts.extend(child.get_all_accounts())
        return accounts
    
    def add_account(self, account: AccountComponent):
        """Add a child account"""
        self.children.append(account)
    
    def remove_account(self, account_id: str):
        """Remove a child account"""
        self.children = [child for child in self.children 
                        if child.get_account_id() != account_id]
    
    def get_children(self) -> List[AccountComponent]:
        """Get direct children"""
        return self.children


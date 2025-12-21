"""
Decorator Pattern for adding features to accounts dynamically
"""
from abc import ABC, abstractmethod
from domain.account.account import Account


class AccountFeature(ABC):
    """Base decorator for account features"""
    
    def __init__(self, account: Account):
        self._account = account
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance with feature modifications"""
        pass
    
    @abstractmethod
    def get_feature_name(self) -> str:
        """Get the name of this feature"""
        pass
    
    def get_account(self) -> Account:
        """Get the underlying account"""
        return self._account


class OverdraftProtection(AccountFeature):
    """Adds overdraft protection to account"""
    
    def __init__(self, account: Account, overdraft_limit: float = 1000.0):
        super().__init__(account)
        self.overdraft_limit = overdraft_limit
    
    def get_balance(self) -> float:
        """Return balance including overdraft protection"""
        return self._account.balance + self.overdraft_limit
    
    def get_feature_name(self) -> str:
        return "Overdraft Protection"
    
    def withdraw(self, amount: float) -> bool:
        """Allow withdrawal up to overdraft limit"""
        available = self._account.balance + self.overdraft_limit
        if amount <= available:
            if self._account.balance >= amount:
                return self._account.withdraw(amount)
            else:
                # Use overdraft
                self._account.balance -= amount
                return True
        return False


class InvestmentBonus(AccountFeature):
    """Adds investment bonus to account"""
    
    def __init__(self, account: Account, bonus_rate: float = 0.05):
        super().__init__(account)
        self.bonus_rate = bonus_rate
    
    def get_balance(self) -> float:
        """Return balance with investment bonus"""
        return self._account.balance * (1 + self.bonus_rate)
    
    def get_feature_name(self) -> str:
        return f"Investment Bonus ({self.bonus_rate * 100}%)"
    
    def apply_bonus(self):
        """Apply bonus to account"""
        bonus = self._account.balance * self.bonus_rate
        self._account.balance += bonus


class PremiumSavings(AccountFeature):
    """Adds premium savings benefits"""
    
    def __init__(self, account: Account, interest_rate: float = 0.03):
        super().__init__(account)
        self.interest_rate = interest_rate
    
    def get_balance(self) -> float:
        """Return balance with accrued interest"""
        return self._account.balance
    
    def get_feature_name(self) -> str:
        return f"Premium Savings ({self.interest_rate * 100}% interest)"
    
    def apply_interest(self):
        """Apply interest to account"""
        interest = self._account.balance * self.interest_rate
        self._account.balance += interest


class BusinessLoanExtension(AccountFeature):
    """Adds business loan extension features"""
    
    def __init__(self, account: Account, extension_amount: float = 50000.0):
        super().__init__(account)
        self.extension_amount = extension_amount
    
    def get_balance(self) -> float:
        """Return available credit including extension"""
        # For loans, balance is negative (debt)
        return abs(self._account.balance) + self.extension_amount
    
    def get_feature_name(self) -> str:
        return f"Business Loan Extension (${self.extension_amount:.2f})"
    
    def get_available_credit(self) -> float:
        """Get available credit"""
        return self.extension_amount - abs(self._account.balance)


"""
Custom exceptions for Banking System
"""


class BankingSystemError(Exception):
    """Base exception for banking system"""
    pass


class InvalidTransactionError(BankingSystemError):
    """Raised when a transaction is invalid"""
    pass


class UnauthorizedAccessError(BankingSystemError):
    """Raised when user lacks required permissions"""
    pass


class InvalidStateTransitionError(BankingSystemError):
    """Raised when account state transition is invalid"""
    pass


class InsufficientFundsError(BankingSystemError):
    """Raised when account has insufficient funds"""
    pass


class AccountNotFoundError(BankingSystemError):
    """Raised when account is not found"""
    pass


class UnauthorizedOperationError(BankingSystemError):
    """Raised when user attempts an operation they are not authorized to perform"""
    pass


class FrozenAccountError(BankingSystemError):
    """Raised when an operation is attempted on a frozen account that is not allowed"""
    pass
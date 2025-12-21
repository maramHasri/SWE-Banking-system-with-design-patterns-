"""
Account type definitions
"""
from enum import Enum


class AccountType(Enum):
    """Types of bank accounts"""
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    LOAN = "loan"
    BUSINESS_LOAN = "business_loan"


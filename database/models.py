"""
SQLAlchemy database models
"""
from datetime import datetime
from database.db import db
from sqlalchemy import Column, String, Float, Integer, DateTime, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import enum


class RoleEnum(enum.Enum):
    """User role enumeration"""
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    ADMIN = "admin"


class User(db.Model):
    """User model - represents all system users (customers, employees, admins)"""
    __tablename__ = 'users'
    
    user_id = Column(String(100), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(SQLEnum(RoleEnum, native_enum=False, length=20), default=RoleEnum.CUSTOMER, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    accounts = relationship('Account', foreign_keys='Account.owner_id', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value if isinstance(self.role, enum.Enum) else self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f"<User {self.username}: {self.role.value}>"


class AccountTypeEnum(enum.Enum):
    """Account type enumeration"""
    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    LOAN = "loan"
    BUSINESS_LOAN = "business_loan"


class AccountStateEnum(enum.Enum):
    """Account state enumeration"""
    ACTIVE = "active"
    FROZEN = "frozen"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class TransactionTypeEnum(enum.Enum):
    """Transaction type enumeration"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatusEnum(enum.Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Account(db.Model):
    """Account model"""
    __tablename__ = 'accounts'
    
    account_id = Column(String(50), primary_key=True)
    iban = Column(String(34), unique=True, nullable=True, index=True)
    account_type = Column(SQLEnum(AccountTypeEnum, native_enum=False, length=20), nullable=False)
    owner_id = Column(String(100), ForeignKey('users.user_id'), nullable=False, index=True)
    balance = Column(Float, default=0.0, nullable=False)
    parent_account_id = Column(String(50), ForeignKey('accounts.account_id'), nullable=True)
    state = Column(SQLEnum(AccountStateEnum, native_enum=False, length=20), default=AccountStateEnum.ACTIVE, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    parent_account = relationship('Account', remote_side=[account_id], backref='child_accounts')
    transactions = relationship('Transaction', foreign_keys='Transaction.account_id', back_populates='account')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'account_id': self.account_id,
            'iban': self.iban,
            'account_type': self.account_type.value if isinstance(self.account_type, enum.Enum) else self.account_type,
            'owner_id': self.owner_id,
            'balance': self.balance,
            'parent_account_id': self.parent_account_id,
            'state': self.state.value if isinstance(self.state, enum.Enum) else self.state,
            'is_closed': self.is_closed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<Account {self.account_id}: {self.account_type.value} - ${self.balance:.2f}>"


class Transaction(db.Model):
    """Transaction model"""
    __tablename__ = 'transactions'
    
    transaction_id = Column(String(50), primary_key=True)
    transaction_type = Column(SQLEnum(TransactionTypeEnum, native_enum=False, length=20), nullable=False)
    account_id = Column(String(50), ForeignKey('accounts.account_id'), nullable=False, index=True)
    target_account_id = Column(String(50), ForeignKey('accounts.account_id'), nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(TransactionStatusEnum, native_enum=False, length=20), default=TransactionStatusEnum.PENDING, nullable=False)
    description = Column(String(500), nullable=True)
    approved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    account = relationship('Account', foreign_keys=[account_id], back_populates='transactions')
    target_account = relationship('Account', foreign_keys=[target_account_id])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type.value if isinstance(self.transaction_type, enum.Enum) else self.transaction_type,
            'account_id': self.account_id,
            'target_account_id': self.target_account_id,
            'amount': self.amount,
            'status': self.status.value if isinstance(self.status, enum.Enum) else self.status,
            'description': self.description,
            'approved_by': self.approved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }
    
    def __repr__(self):
        return f"<Transaction {self.transaction_id}: {self.transaction_type.value} - ${self.amount:.2f}>"


class BankFinancials(db.Model):
    """Bank financials model"""
    __tablename__ = 'bank_financials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    retained_earnings = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<BankFinancials: Retained Earnings = ${self.retained_earnings:.2f}>"


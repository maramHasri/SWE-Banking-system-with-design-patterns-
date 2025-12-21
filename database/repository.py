"""
Database repository for banking operations
"""
import re
import random
import string
from typing import List, Optional
from database.db import db
from database.models import (
    User as UserModel, Account as AccountModel, Transaction as TransactionModel, 
    BankFinancials, AccountTypeEnum, AccountStateEnum, RoleEnum,
    TransactionTypeEnum, TransactionStatusEnum
)
from domain.account.account import Account
from domain.account.account_type import AccountType
from domain.transaction.transaction import Transaction, TransactionType, TransactionStatus
from domain.state.account_state import ActiveState, FrozenState, SuspendedState, ClosedState
from domain.roles.role import Role
from utils.exceptions import AccountNotFoundError
from datetime import datetime


# IBAN (International Bank Account Number) utilities
def validate_iban(iban: str) -> bool:
    """
    Validate IBAN format and checksum according to ISO 13616 standard.
    
    Args:
        iban: IBAN string to validate
        
    Returns:
        True if IBAN is valid, False otherwise
    """
    if not iban:
        return False
    
    # Remove spaces and convert to uppercase
    iban = iban.replace(' ', '').upper()
    
    # IBAN must be between 15 and 34 characters
    if len(iban) < 15 or len(iban) > 34:
        return False
    
    # Must start with 2 letters (country code)
    if not re.match(r'^[A-Z]{2}', iban):
        return False
    
    # Must contain only alphanumeric characters
    if not re.match(r'^[A-Z0-9]+$', iban):
        return False
    
    # Basic format validation: Country code (2) + Check digits (2) + BBAN (variable)
    if len(iban) < 4:
        return False
    
    # Validate checksum using MOD-97 algorithm
    try:
        # Move first 4 characters to end
        rearranged = iban[4:] + iban[:4]
        
        # Replace letters with numbers (A=10, B=11, ..., Z=35)
        numeric = ''
        for char in rearranged:
            if char.isdigit():
                numeric += char
            else:
                numeric += str(ord(char) - ord('A') + 10)
        
        # Calculate MOD-97
        remainder = int(numeric) % 97
        
        # Valid IBAN has remainder of 1
        return remainder == 1
    except (ValueError, TypeError):
        return False


def generate_iban(country_code: str = 'US', account_id: str = None) -> str:
    """
    Generate a valid IBAN for an account.
    
    Args:
        country_code: Two-letter country code (default: 'US')
        account_id: Account ID to incorporate into IBAN
        
    Returns:
        Valid IBAN string
    """
    if not account_id:
        account_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    # Create base BBAN (Basic Bank Account Number)
    # Format: 4-char bank code + account identifier (padded to 20 chars)
    bank_code = 'BANK'  # Bank identifier
    account_part = account_id.replace('ACC_', '').replace('_', '').upper()
    account_part = account_part.ljust(20, '0')[:20]  # Pad to 20 chars
    
    bban = bank_code + account_part
    
    # Calculate check digits
    rearranged = bban + country_code + '00'
    numeric = ''
    for char in rearranged:
        if char.isdigit():
            numeric += char
        else:
            numeric += str(ord(char) - ord('A') + 10)
    
    checksum = 98 - (int(numeric) % 97)
    check_digits = f"{checksum:02d}"
    
    # Construct final IBAN
    iban = country_code + check_digits + bban
    
    # Validate the generated IBAN
    if validate_iban(iban):
        return iban
    else:
        # Fallback: generate a simpler valid IBAN
        return _generate_simple_iban(country_code, account_id)


def _generate_simple_iban(country_code: str = 'US', account_id: str = None) -> str:
    """
    Generate a simple valid IBAN (for testing/development).
    Uses a simplified format that passes validation.
    """
    if not account_id:
        account_id = ''.join([str(random.randint(0, 9)) for _ in range(12)])
    
    # Simple format: US + check digits + fixed bank code + account number
    bank_code = '0001'
    account_num = account_id.replace('ACC_', '').replace('_', '').zfill(20)
    
    # Create base
    base = bank_code + account_num + country_code + '00'
    
    # Convert to numeric
    numeric = ''
    for char in base:
        if char.isdigit():
            numeric += char
        else:
            numeric += str(ord(char) - ord('A') + 10)
    
    # Calculate checksum
    checksum = 98 - (int(numeric) % 97)
    check_digits = f"{checksum:02d}"
    
    iban = country_code + check_digits + bank_code + account_num
    
    return iban


class UserRepository:
    """Repository for user operations"""
    
    @staticmethod
    def create(user_id: str, username: str, role: Role, email: str = None, 
               phone: str = None, password_hash: str = None) -> UserModel:
        """Create user in database"""
        try:
            user = UserModel(
                user_id=user_id,
                username=username,
                email=email,
                phone=phone,
                password_hash=password_hash,
                role=RoleEnum(role.value),
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise
    
    @staticmethod
    def get(user_id: str) -> UserModel:
        """Get user by ID"""
        user = UserModel.query.get(user_id)
        if not user:
            return None
        return user
    
    @staticmethod
    def get_by_username(username: str) -> UserModel:
        """Get user by username"""
        return UserModel.query.filter_by(username=username).first()
    
    @staticmethod
    def get_by_email(email: str) -> UserModel:
        """Get user by email"""
        return UserModel.query.filter_by(email=email).first()
    
    @staticmethod
    def get_by_phone(phone: str) -> UserModel:
        """Get user by phone number"""
        return UserModel.query.filter_by(phone=phone).first()
    
    @staticmethod
    def get_by_email_or_phone(email_or_phone: str) -> UserModel:
        """Get user by email or phone number"""
        user = UserModel.query.filter_by(email=email_or_phone).first()
        if not user:
            user = UserModel.query.filter_by(phone=email_or_phone).first()
        return user
    
    @staticmethod
    def get_all() -> List[UserModel]:
        """Get all users"""
        return UserModel.query.all()
    
    @staticmethod
    def get_by_role(role: Role) -> List[UserModel]:
        """Get users by role"""
        return UserModel.query.filter_by(role=RoleEnum(role.value)).all()
    
    @staticmethod
    def update_role(user_id: str, role: Role):
        """Update user role"""
        user = UserRepository.get(user_id)
        if user:
            user.role = RoleEnum(role.value)
            db.session.commit()
    
    @staticmethod
    def get_all_employees() -> List[UserModel]:
        """Get all employees"""
        return UserModel.query.filter_by(role=RoleEnum.EMPLOYEE).all()
    
    @staticmethod
    def get_all_admins() -> List[UserModel]:
        """Get all admins"""
        return UserModel.query.filter_by(role=RoleEnum.ADMIN).all()
    
    @staticmethod
    def verify_user_credentials(username: str, password: str) -> Optional[UserModel]:
        """
        Verify user credentials (username + password).
        Returns UserModel if credentials are valid, None otherwise.
        """
        from security.password import verify_password
        
        user = UserRepository.get_by_username(username)
        if user and user.password_hash:
            if verify_password(user.password_hash, password):
                return user
        return None


class AccountRepository:
    """Repository for account operations"""
    
    @staticmethod
    def create(account_id: str, account_type: AccountType, owner_id: str, 
              balance: float, parent_account_id: Optional[str] = None,
              iban: Optional[str] = None) -> AccountModel:
        """Create account in database"""
        try:
            # Generate IBAN if not provided
            if not iban:
                iban = generate_iban('US', account_id)
                # Ensure uniqueness
                while AccountRepository.get_by_iban(iban):
                    iban = generate_iban('US', account_id)
            
            account = AccountModel(
                account_id=account_id,
                iban=iban,
                account_type=AccountTypeEnum(account_type.value),
                owner_id=owner_id,
                balance=balance,
                parent_account_id=parent_account_id,
                state=AccountStateEnum.ACTIVE
            )
            db.session.add(account)
            db.session.commit()
            return account  
        except Exception as e:
            db.session.rollback()
            raise
    
    @staticmethod
    def get(account_id: str) -> AccountModel:
        """Get account by ID"""
        account = AccountModel.query.get(account_id)
        if not account:
            raise AccountNotFoundError(f"Account {account_id} not found")
        return account
    
    @staticmethod
    def get_by_owner(owner_id: str) -> List[AccountModel]:
        """Get all accounts for owner"""
        return AccountModel.query.filter_by(owner_id=owner_id).all()
    
    @staticmethod
    def get_by_iban(iban: str) -> Optional[AccountModel]:
        """Get account by IBAN"""
        if not iban:
            return None
        # Remove spaces for lookup
        iban_clean = iban.replace(' ', '').upper()
        return AccountModel.query.filter_by(iban=iban_clean).first()
    
    @staticmethod
    def get_by_account_id_and_iban(account_id: str, iban: str) -> Optional[AccountModel]:
        """Get account by both account_id and IBAN (for authentication)"""
        if not account_id or not iban:
            return None
        iban_clean = iban.replace(' ', '').upper()
        account = AccountModel.query.filter_by(account_id=account_id, iban=iban_clean).first()
        return account
    
    @staticmethod
    def generate_ibans_for_all_accounts() -> int:
        """
        Generate IBANs for all accounts that don't have one.
        Returns the number of accounts updated.
        """
        accounts_without_iban = AccountModel.query.filter(
            (AccountModel.iban == None) | (AccountModel.iban == '')
        ).all()
        
        if not accounts_without_iban:
            return 0
        
        updated_count = 0
        for account in accounts_without_iban:
            try:
                # Generate unique IBAN
                iban = generate_iban('US', account.account_id)
                
                # Ensure uniqueness
                while AccountRepository.get_by_iban(iban):
                    iban = generate_iban('US', account.account_id)
                
                # Validate before saving
                if validate_iban(iban):
                    account.iban = iban
                    db.session.commit()
                    updated_count += 1
            except Exception as e:
                db.session.rollback()
                raise
        
        return updated_count
    
    @staticmethod
    def get_all() -> List[AccountModel]:
        """Get all accounts"""
        return AccountModel.query.all()
    
    @staticmethod
    def update_balance(account_id: str, new_balance: float):
        """Update account balance"""
        account = AccountRepository.get(account_id)
        account.balance = new_balance
        db.session.commit()
    
    @staticmethod
    def update_state(account_id: str, state: AccountStateEnum):
        """Update account state"""
        account = AccountRepository.get(account_id)
        account.state = state
        if state == AccountStateEnum.CLOSED:
            account.is_closed = True
        db.session.commit()
    
    @staticmethod
    def to_domain_account(db_account: AccountModel) -> Account:
        """Convert database model to domain Account"""
        account = Account(
            account_id=db_account.account_id,
            account_type=AccountType(db_account.account_type.value),
            owner_id=db_account.owner_id,
            balance=db_account.balance,
            parent_account_id=db_account.parent_account_id,
            iban=db_account.iban
        )
        
        # Set state
        state_map = {
            AccountStateEnum.ACTIVE: ActiveState(),
            AccountStateEnum.FROZEN: FrozenState(),
            AccountStateEnum.SUSPENDED: SuspendedState(),
            AccountStateEnum.CLOSED: ClosedState()
        }
        account.set_state(state_map[db_account.state])
        account.is_closed = db_account.is_closed
        
        return account


class TransactionRepository:
    """Repository for transaction operations"""
    
    @staticmethod
    def create(transaction_id: str, transaction_type: TransactionType,
              account_id: str, amount: float, target_account_id: Optional[str] = None,
              description: str = "") -> TransactionModel:
        """Create transaction in database"""
        transaction = TransactionModel(
            transaction_id=transaction_id,
            transaction_type=TransactionTypeEnum(transaction_type.value),
            account_id=account_id,
            target_account_id=target_account_id,
            amount=amount,
            description=description,
            status=TransactionStatusEnum.PENDING
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction
    
    @staticmethod
    def get(transaction_id: str) -> TransactionModel:
        """Get transaction by ID"""
        return TransactionModel.query.get(transaction_id)
    
    @staticmethod
    def get_by_account(account_id: str) -> List[TransactionModel]:
        """Get transactions for account"""
        return TransactionModel.query.filter(
            (TransactionModel.account_id == account_id) | 
            (TransactionModel.target_account_id == account_id)
        ).all()
    
    @staticmethod
    def get_all() -> List[TransactionModel]:
        """Get all transactions"""
        return TransactionModel.query.all()
    
    @staticmethod
    def get_pending() -> List[TransactionModel]:
        """Get pending transactions"""
        return TransactionModel.query.filter_by(status=TransactionStatusEnum.PENDING).all()
    
    @staticmethod
    def update_status(transaction_id: str, status: TransactionStatusEnum, 
                     approved_by: Optional[str] = None):
        """Update transaction status"""
        transaction = TransactionRepository.get(transaction_id)
        transaction.status = status
        if approved_by:
            transaction.approved_by = approved_by
            transaction.approved_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def to_domain_transaction(db_transaction: TransactionModel) -> Transaction:
        """Convert database model to domain Transaction"""
        transaction = Transaction(
            transaction_id=db_transaction.transaction_id,
            transaction_type=TransactionType(db_transaction.transaction_type.value),
            account_id=db_transaction.account_id,
            amount=db_transaction.amount,
            target_account_id=db_transaction.target_account_id,
            description=db_transaction.description or ""
        )
        
        # Set status
        status_map = {
            TransactionStatusEnum.PENDING: TransactionStatus.PENDING,
            TransactionStatusEnum.APPROVED: TransactionStatus.APPROVED,
            TransactionStatusEnum.REJECTED: TransactionStatus.REJECTED,
            TransactionStatusEnum.COMPLETED: TransactionStatus.COMPLETED
        }
        transaction.status = status_map[db_transaction.status]
        transaction.approved_by = db_transaction.approved_by
        transaction.approved_at = db_transaction.approved_at
        
        return transaction


class FinancialsRepository:
    """Repository for bank financials"""
    
    @staticmethod
    def get_or_create() -> BankFinancials:
        """Get or create financials record"""
        financials = BankFinancials.query.first()
        if not financials:
            financials = BankFinancials(retained_earnings=0.0)
            db.session.add(financials)
            db.session.commit()
        return financials
    
    @staticmethod
    def update_earnings(net_income: float, dividends: float):
        """Update retained earnings"""
        financials = FinancialsRepository.get_or_create()
        financials.retained_earnings += net_income - dividends
        db.session.commit()
        return financials
    
    @staticmethod
    def get_retained_earnings() -> float:
        """Get retained earnings"""
        financials = FinancialsRepository.get_or_create()
        return financials.retained_earnings


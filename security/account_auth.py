"""
Account-based authentication for customers
Customers authenticate using account_id + IBAN
"""

from typing import Optional, Tuple
from database.repository import AccountRepository, validate_iban
from utils.exceptions import UnauthorizedAccessError, AccountNotFoundError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def authenticate_account(account_id: str, iban: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Authenticate customer using account_id and IBAN.
    
    Args:
        account_id: Account ID
        iban: IBAN for the account
        
    Returns:
        Tuple of (success, account_id, error_message)
        - success: True if authentication successful
        - account_id: Authenticated account ID if successful, None otherwise
        - error_message: Error message if failed, None if successful
    """
    # Validate IBAN format
    if not validate_iban(iban):
        error_msg = "Invalid IBAN format"
        logger.warning(f"Failed login attempt: {error_msg} - Account: {account_id}, IBAN: {iban[:4]}***")
        return False, None, error_msg
    
    # Look up account by account_id and IBAN
    account = AccountRepository.get_by_account_id_and_iban(account_id, iban)
    
    if not account:
        error_msg = "Invalid account ID or IBAN"
        logger.warning(f"Failed login attempt: {error_msg} - Account: {account_id}, IBAN: {iban[:4]}***")
        return False, None, error_msg
    
    # Check if account is active
    if account.is_closed:
        error_msg = "Account is closed"
        logger.warning(f"Failed login attempt: {error_msg} - Account: {account_id}")
        return False, None, error_msg
    
    # Check account state
    from database.models import AccountStateEnum
    if account.state == AccountStateEnum.CLOSED:
        error_msg = "Account is closed"
        logger.warning(f"Failed login attempt: {error_msg} - Account: {account_id}")
        return False, None, error_msg
    
    # Authentication successful
    logger.info(f"Successful account authentication - Account: {account_id}")
    return True, account.account_id, None


def verify_account_access(authenticated_account_id: str, requested_account_id: str) -> bool:
    """
    Verify that the requested account matches the authenticated account.
    
    Args:
        authenticated_account_id: Account ID from authenticated session
        requested_account_id: Account ID being accessed
        
    Returns:
        True if access is allowed, False otherwise
    """
    return authenticated_account_id == requested_account_id


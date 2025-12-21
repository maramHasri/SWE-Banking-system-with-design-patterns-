"""
Centralized logging for Banking System
"""
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('banking_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('banking_system')


def log_transaction(transaction_id: str, account_id: str, amount: float, transaction_type: str):
    """Log transaction details"""
    logger.info(f"Transaction {transaction_id}: {transaction_type} of ${amount:.2f} on account {account_id}")


def log_approval(transaction_id: str, approver: str, decision: str):
    """Log approval decisions"""
    logger.info(f"Approval {transaction_id}: {decision} by {approver}")


def log_error(error: Exception, context: str = ""):
    """Log errors"""
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)


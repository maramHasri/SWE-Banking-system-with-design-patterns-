"""
Reporting service for generating reports
"""
from typing import List, Dict, Any
from datetime import datetime
from patterns.facade.banking_facade_db import BankingFacadeDB
from domain.transaction.transaction import Transaction


class ReportService:
    """Service for generating reports"""
    
    def __init__(self, banking_facade: BankingFacadeDB):
        self.facade = banking_facade
    
    def get_daily_transaction_report(self, date: datetime = None) -> Dict[str, Any]:
        """Generate daily transaction report"""
        if date is None:
            date = datetime.now()
        
        transactions = self.facade.get_all_transactions()
        day_transactions = [
            t for t in transactions 
            if t.created_at.date() == date.date()
        ]
        
        total_deposits = sum(t.amount for t in day_transactions 
                            if t.transaction_type.value == 'deposit')
        total_withdrawals = sum(t.amount for t in day_transactions 
                              if t.transaction_type.value == 'withdrawal')
        total_transfers = sum(t.amount for t in day_transactions 
                            if t.transaction_type.value == 'transfer')
        
        return {
            'date': date.date().isoformat(),
            'total_transactions': len(day_transactions),
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'total_transfers': total_transfers,
            'transactions': [t.to_dict() for t in day_transactions]
        }
    
    def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get account summary report"""
        account = self.facade.get_account(account_id)
        transactions = self.facade.get_transactions_by_account(account_id)
        
        return {
            'account': account.to_dict(),
            'transaction_count': len(transactions),
            'recent_transactions': [t.to_dict() for t in transactions[-10:]]
        }
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get audit log"""
        # In a real system, this would query a proper audit log
        # For now, return transaction history
        transactions = self.facade.get_all_transactions()
        return [t.to_dict() for t in transactions]
    
    def get_financial_summary(self) -> Dict[str, Any]:
        """Get bank-wide financial summary (admin only)"""
        accounts = self.facade.get_all_accounts()
        total_deposits = sum(acc.balance for acc in accounts if acc.balance > 0)
        total_loans = sum(abs(acc.balance) for acc in accounts if acc.balance < 0)
        retained_earnings = self.facade.get_retained_earnings()
        
        return {
            'total_deposits': total_deposits,
            'total_loans': total_loans,
            'retained_earnings': retained_earnings,
            'total_accounts': len(accounts),
            'active_accounts': len([a for a in accounts if a.get_state_name() == 'Active'])
        }


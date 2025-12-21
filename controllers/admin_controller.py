"""
Admin controller - handles admin routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from domain.roles.role import Role
from services.transaction_service import TransactionService
from services.approval_service import ApprovalService
from services.account_service import AccountService
from reporting.report_service import ReportService
from security.rbac import require_role, get_current_user_role, get_current_user_id
from utils.exceptions import BankingSystemError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def init_admin_controller(transaction_service: TransactionService,
                         approval_service: ApprovalService,
                         account_service: AccountService,
                         report_service: ReportService,
                         banking_facade):
    """Initialize admin controller with services"""
    
    @admin_bp.route('/')
    @require_role(Role.ADMIN)
    def dashboard():
        """Admin dashboard"""
        pending_approvals = approval_service.get_pending_approvals(Role.ADMIN)
        financial_summary = report_service.get_financial_summary()
        daily_report = report_service.get_daily_transaction_report()
        
        return render_template('admin/dashboard.html',
                             pending_approvals=pending_approvals,
                             financial_summary=financial_summary,
                             daily_report=daily_report)
    
    @admin_bp.route('/approve/<transaction_id>', methods=['POST'])
    @require_role(Role.ADMIN)
    def approve_transaction(transaction_id):
        """Approve a high-value transaction"""
        try:
            user_id = get_current_user_id()
            approval_service.approve_transaction(transaction_id, Role.ADMIN, user_id)
            flash(f'Transaction {transaction_id} approved successfully!', 'success')
        except BankingSystemError as e:
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('admin.dashboard'))
    
    @admin_bp.route('/financials')
    @require_role(Role.ADMIN)
    def financials():
        """View financial reports"""
        financial_summary = report_service.get_financial_summary()
        audit_log = report_service.get_audit_log()
        return render_template('admin/financials.html',
                             financial_summary=financial_summary,
                             audit_log=audit_log[:50])  # Last 50 entries
    
    @admin_bp.route('/update_earnings', methods=['POST'])
    @require_role(Role.ADMIN)
    def update_earnings():
        """Update retained earnings"""
        try:
            net_income = float(request.form.get('net_income', 0))
            dividends = float(request.form.get('dividends', 0))
            banking_facade.update_retained_earnings(net_income, dividends)
            flash('Retained earnings updated successfully!', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('admin.financials'))
    
    @admin_bp.route('/all_transactions')
    @require_role(Role.ADMIN)
    def all_transactions():
        """View all transactions"""
        transactions = transaction_service.get_all_transactions()
        return render_template('admin/all_transactions.html', 
                             transactions=transactions)
    
    @admin_bp.route('/database_dashboard')
    @require_role(Role.ADMIN)
    def database_dashboard():
        """Database/Data Dashboard - View all system data"""
        # Get all data from the facade
        all_accounts = account_service.get_all_accounts()
        all_transactions = transaction_service.get_all_transactions()
        
        # Organize accounts by owner
        accounts_by_owner = {}
        for account in all_accounts:
            owner_id = account.owner_id
            if owner_id not in accounts_by_owner:
                accounts_by_owner[owner_id] = []
            accounts_by_owner[owner_id].append(account)
        
        # Organize transactions by account
        transactions_by_account = {}
        for transaction in all_transactions:
            acc_id = transaction.account_id
            if acc_id not in transactions_by_account:
                transactions_by_account[acc_id] = []
            transactions_by_account[acc_id].append(transaction)
        
        # Calculate statistics
        total_balance = sum(acc.balance for acc in all_accounts)
        total_deposits = sum(t.amount for t in all_transactions if t.transaction_type.value == 'deposit')
        total_withdrawals = sum(t.amount for t in all_transactions if t.transaction_type.value == 'withdrawal')
        total_transfers = sum(t.amount for t in all_transactions if t.transaction_type.value == 'transfer')
        
        # Account type distribution
        account_type_count = {}
        for account in all_accounts:
            acc_type = account.account_type.value
            account_type_count[acc_type] = account_type_count.get(acc_type, 0) + 1
        
        # State distribution
        state_count = {}
        for account in all_accounts:
            state = account.get_state_name()
            state_count[state] = state_count.get(state, 0) + 1
        
        return render_template('admin/database_dashboard.html',
                             all_accounts=all_accounts,
                             all_transactions=all_transactions,
                             accounts_by_owner=accounts_by_owner,
                             transactions_by_account=transactions_by_account,
                             total_balance=total_balance,
                             total_deposits=total_deposits,
                             total_withdrawals=total_withdrawals,
                             total_transfers=total_transfers,
                             account_type_count=account_type_count,
                             state_count=state_count,
                             total_accounts=len(all_accounts),
                             total_transactions=len(all_transactions))


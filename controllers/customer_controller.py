"""
Customer controller - handles customer-facing routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from domain.account.account_type import AccountType
from domain.roles.role import Role
from services.account_service import AccountService
from services.transaction_service import TransactionService
from services.notification_service import NotificationService
from security.rbac import get_current_user_role, get_current_user_id
from utils.exceptions import BankingSystemError

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')


def init_customer_controller(account_service: AccountService, 
                             transaction_service: TransactionService,
                             notification_service: NotificationService):
    """Initialize customer controller with services"""
    
    @customer_bp.route('/')
    def dashboard():
        """Customer dashboard"""
        user_id = get_current_user_id()
        accounts = account_service.get_user_accounts(user_id)
        notifications = notification_service.get_notifications(user_id)
        return render_template('customer/dashboard.html', 
                             accounts=accounts, 
                             notifications=notifications[-5:])
    
    @customer_bp.route('/transaction', methods=['GET', 'POST'])
    def transaction():
        """Perform a transaction"""
        user_id = get_current_user_id()
        accounts = account_service.get_user_accounts(user_id)
        
        # Debug: Log user_id and account count
        print(f"🔍 Transaction page - User ID: {user_id}, Found {len(accounts)} account(s)")
        if not accounts:
            print(f"⚠️  No accounts found for user_id: {user_id}")
            print(f"   Session data: user_id={session.get('user_id')}, username={session.get('username')}")
        
        if request.method == 'POST':
            transaction_type = request.form.get('transaction_type')
            account_id = request.form.get('account_id')
            amount = float(request.form.get('amount', 0))
            description = request.form.get('description', '')
            target_account_id = request.form.get('target_account_id')
            
            try:
                user_role = get_current_user_role()
                user_id = get_current_user_id()
                
                if transaction_type == 'deposit':
                    # Anyone can deposit to any account
                    transaction = transaction_service.deposit(
                        account_id, amount, description, user_role, user_id
                    )
                elif transaction_type == 'withdrawal':
                    # Customers can only withdraw from their own accounts
                    transaction = transaction_service.withdraw(
                        account_id, amount, description, user_role, user_id
                    )
                elif transaction_type == 'transfer':
                    if not target_account_id:
                        flash('Target account is required for transfer', 'error')
                        return redirect(url_for('customer.transaction'))
                    # Customers can only transfer from their own accounts
                    transaction = transaction_service.transfer(
                        account_id, target_account_id, amount, description, user_role, user_id
                    )
                else:
                    flash('Invalid transaction type', 'error')
                    return redirect(url_for('customer.transaction'))
                
                if transaction.status.value == 'completed':
                    flash(f'Transaction {transaction.transaction_id} completed successfully!', 'success')
                elif transaction.status.value == 'pending':
                    flash(f'Transaction {transaction.transaction_id} is pending approval', 'info')
                else:
                    flash(f'Transaction {transaction.transaction_id} was rejected', 'error')
                
                return redirect(url_for('customer.dashboard'))
            except BankingSystemError as e:
                flash(f'Error: {str(e)}', 'error')
            except Exception as e:
                flash(f'Unexpected error: {str(e)}', 'error')
        
        all_accounts = account_service.get_all_accounts()
        return render_template('customer/transaction.html', 
                             accounts=accounts,
                             all_accounts=all_accounts)
    
    @customer_bp.route('/notifications')
    def notifications():
        """View notifications"""
        user_id = get_current_user_id()
        notifications = notification_service.get_notifications(user_id)
        return render_template('customer/notifications.html', 
                             notifications=notifications)


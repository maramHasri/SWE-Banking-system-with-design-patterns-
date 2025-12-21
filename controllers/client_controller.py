"""
Client controller - ATM-like interface (no login required)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from domain.account.account_type import AccountType
from domain.roles.role import Role
from services.account_service import AccountService
from services.transaction_service import TransactionService
from services.notification_service import NotificationService
from utils.exceptions import BankingSystemError
from security.account_auth import authenticate_account, verify_account_access
from datetime import datetime

client_bp = Blueprint('client', __name__, url_prefix='/client')


def init_client_controller(account_service: AccountService, 
                          transaction_service: TransactionService,
                          notification_service: NotificationService):
    """Initialize client controller with services"""
    
    @client_bp.route('/', methods=['GET', 'POST'])
    def access():
        """Customer account login page"""
        if request.method == 'POST':
            account_id = request.form.get('account_id', '').strip()
            iban = request.form.get('iban', '').strip()
            
            if not account_id or not iban:
                flash('Both Account ID and IBAN are required', 'error')
                return render_template('client/access.html')
            
            # Authenticate using account_id + IBAN
            success, authenticated_account_id, error_msg = authenticate_account(account_id, iban)
            
            if success:
                # Store authenticated account in session
                session['authenticated_account_id'] = authenticated_account_id
                session['account_login_time'] = datetime.now().isoformat()
                flash(f'Successfully logged in to account {authenticated_account_id}', 'success')
                return redirect(url_for('client.account_view', account_id=authenticated_account_id))
            else:
                flash(f'Login failed: {error_msg}', 'error')
                return render_template('client/access.html')
        
        return render_template('client/access.html')
    
    @client_bp.route('/account/<account_id>')
    def account_view(account_id):
        """View account and perform operations (requires authentication)"""
        try:
            # Strip any whitespace from account_id
            account_id = account_id.strip()
            
            # Check if account is authenticated
            authenticated_account_id = session.get('authenticated_account_id')
            if not authenticated_account_id:
                flash('You must login with your Account ID and IBAN to access this account', 'error')
                return redirect(url_for('client.access'))
            
            # Verify account access
            if not verify_account_access(authenticated_account_id, account_id):
                flash('You can only access the account you logged in with. Please login again.', 'error')
                session.pop('authenticated_account_id', None)
                return redirect(url_for('client.access'))
            
            account = account_service.get_account(account_id)
            transactions = transaction_service.get_account_transactions(account_id)
            
            return render_template('client/account.html', 
                                 account=account, 
                                 transactions=transactions[-10:],  # Last 10
                                 is_own_account=True,
                                 authenticated_account_id=authenticated_account_id)
        except BankingSystemError as e:
            error_msg = str(e)
            flash(f'Error: {error_msg}', 'error')
            # Add helpful debugging info
            print(f"❌ Account lookup failed for: '{account_id}'")
            print(f"   Error: {error_msg}")
            return redirect(url_for('client.access'))
        except Exception as e:
            error_msg = str(e)
            flash(f'Unexpected error: {error_msg}', 'error')
            print(f"❌ Unexpected error looking up account '{account_id}': {error_msg}")
            import traceback
            traceback.print_exc()
            return redirect(url_for('client.access'))
    
    @client_bp.route('/transaction', methods=['POST'])
    def transaction():
        """
        Perform transaction on authenticated account.
        All operations are restricted to the account that was authenticated via account_id + IBAN.
        """
        account_id = request.form.get('account_id')
        transaction_type = request.form.get('transaction_type')
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        target_account_id = request.form.get('target_account_id')
        
        # Verify account authentication
        authenticated_account_id = session.get('authenticated_account_id')
        if not authenticated_account_id:
            flash('You must login with your Account ID and IBAN to perform transactions', 'error')
            return redirect(url_for('client.access'))
        
        # Verify the account being operated on matches the authenticated account
        if not verify_account_access(authenticated_account_id, account_id):
            flash('Security violation: You can only perform operations on the account you logged in with', 'error')
            return redirect(url_for('client.account_view', account_id=authenticated_account_id))
        
        # Get account owner_id for transaction service
        account = account_service.get_account(account_id)
        user_role = Role.CUSTOMER  # Account-based login is always customer role
        
        try:
            if transaction_type == 'deposit':
                # Deposits allowed on authenticated account
                transaction = transaction_service.deposit(
                    account_id, amount, description, user_role, account.owner_id
                )
            elif transaction_type == 'withdrawal':
                # Withdrawals allowed on authenticated account only
                transaction = transaction_service.withdraw(
                    account_id, amount, description, user_role, account.owner_id, authenticated_account_id
                )
            elif transaction_type == 'transfer':
                if not target_account_id:
                    flash('Target account is required for transfer', 'error')
                    return redirect(url_for('client.account_view', account_id=account_id))
                
                # Transfers allowed from authenticated account to any account
                transaction = transaction_service.transfer(
                    account_id, target_account_id, amount, description, user_role, account.owner_id, authenticated_account_id
                )
            else:
                flash('Invalid transaction type', 'error')
                return redirect(url_for('client.account_view', account_id=account_id))
            
            if transaction.status.value == 'completed':
                flash(f'Transaction {transaction.transaction_id} completed successfully!', 'success')
            elif transaction.status.value == 'pending':
                flash(f'Transaction {transaction.transaction_id} is pending approval (Amount: ${amount:.2f})', 'info')
            else:
                flash(f'Transaction {transaction.transaction_id} was rejected', 'error')
            
            return redirect(url_for('client.account_view', account_id=account_id))
        except BankingSystemError as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('client.account_view', account_id=account_id))
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'error')
            return redirect(url_for('client.account_view', account_id=account_id))
    
    @client_bp.route('/logout')
    def logout():
        """Logout from authenticated account"""
        account_id = session.get('authenticated_account_id')
        session.pop('authenticated_account_id', None)
        session.pop('account_login_time', None)
        if account_id:
            flash(f'Logged out from account {account_id} successfully', 'info')
        return redirect(url_for('client.access'))


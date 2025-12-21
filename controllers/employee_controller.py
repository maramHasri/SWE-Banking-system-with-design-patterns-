"""
Employee controller - handles employee routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from domain.roles.role import Role
from domain.account.account_type import AccountType
from services.transaction_service import TransactionService
from services.approval_service import ApprovalService
from services.account_service import AccountService
from reporting.report_service import ReportService
from security.rbac import require_role, get_current_user_role, get_current_user_id
from utils.exceptions import BankingSystemError
from database.repository import UserRepository
from database.models import RoleEnum

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


def init_employee_controller(transaction_service: TransactionService,
                             approval_service: ApprovalService,
                             account_service: AccountService,
                             report_service: ReportService):
    """Initialize employee controller with services"""
    
    @employee_bp.route('/')
    @require_role(Role.EMPLOYEE, Role.ADMIN)
    def dashboard():
        """Employee dashboard"""
        user_role = get_current_user_role()
        pending_approvals = approval_service.get_pending_approvals(user_role)
        daily_report = report_service.get_daily_transaction_report()
        return render_template('employee/dashboard.html',
                             pending_approvals=pending_approvals,
                             daily_report=daily_report)
    
    @employee_bp.route('/approve/<transaction_id>', methods=['POST'])
    @require_role(Role.EMPLOYEE, Role.ADMIN)
    def approve_transaction(transaction_id):
        """Approve a transaction"""
        try:
            user_role = get_current_user_role()
            user_id = get_current_user_id()
            approval_service.approve_transaction(transaction_id, user_role, user_id)
            flash(f'Transaction {transaction_id} approved successfully!', 'success')
        except BankingSystemError as e:
            flash(f'Error: {str(e)}', 'error')
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'error')
        
        return redirect(url_for('employee.dashboard'))
    
    @employee_bp.route('/reports')
    @require_role(Role.EMPLOYEE, Role.ADMIN)
    def reports():
        """View daily reports"""
        daily_report = report_service.get_daily_transaction_report()
        return render_template('employee/reports.html', report=daily_report)
    
    @employee_bp.route('/accounts')
    @require_role(Role.EMPLOYEE, Role.ADMIN)
    def view_accounts():
        """View all accounts"""
        accounts = account_service.get_all_accounts()
        return render_template('employee/accounts.html', accounts=accounts)
    
    @employee_bp.route('/account/<account_id>/change_state', methods=['POST'])
    @require_role(Role.EMPLOYEE, Role.ADMIN)
    def change_account_state(account_id):
        """Change account state"""
        state = request.form.get('state')
        try:
            user_role = get_current_user_role()
            account_service.change_account_state(account_id, state, user_role)
            flash(f'Account {account_id} state changed to {state}', 'success')
        except BankingSystemError as e:
            flash(f'Error: {str(e)}', 'error')
        
        return redirect(url_for('employee.view_accounts'))
    
    @employee_bp.route('/create_account', methods=['GET', 'POST'])
    @require_role(Role.EMPLOYEE, Role.ADMIN)
    def create_account():
        """Create a new customer account"""
        if request.method == 'POST':
            account_type_str = request.form.get('account_type')
            owner_input = request.form.get('owner_id', '').strip()
            initial_balance = float(request.form.get('initial_balance', 0))
            
            if not owner_input:
                flash('Customer ID/Username is required', 'error')
                return render_template('employee/create_account.html', 
                                     account_types=AccountType)
            
            if not account_type_str:
                flash('Account type is required', 'error')
                return render_template('employee/create_account.html', 
                                     account_types=AccountType)
            
            try:
                # Look up user by user_id first, then by username
                user = UserRepository.get(owner_input)
                if not user:
                    user = UserRepository.get_by_username(owner_input)
                
                # If customer doesn't exist, create a new customer
                if not user:
                    # Create new customer with the provided username
                    customer_email = request.form.get('customer_email', '').strip()
                    customer_phone = request.form.get('customer_phone', '').strip()
                    
                    # Sanitize username: replace spaces with underscores, remove special chars
                    sanitized_username = owner_input.replace(' ', '_').lower()
                    
                    # Generate user_id from sanitized username
                    user_id = f"USER_{sanitized_username.upper().replace(' ', '_')}"
                    
                    # Check if username already exists (might be different user_id)
                    existing_username = UserRepository.get_by_username(sanitized_username)
                    if existing_username:
                        flash(f'Username "{sanitized_username}" already exists. Please use a different username or the existing customer ID.', 'error')
                        return render_template('employee/create_account.html', 
                                             account_types=AccountType)
                    
                    # Check if user_id already exists
                    existing_user_id = UserRepository.get(user_id)
                    if existing_user_id:
                        # If user_id exists but different username, use existing user
                        user = existing_user_id
                        flash(f'Using existing customer with ID {user_id}', 'info')
                    else:
                        # Create new customer
                        user = UserRepository.create(
                            user_id=user_id,
                            username=sanitized_username,
                            role=Role.CUSTOMER,
                            email=customer_email if customer_email else None,
                            phone=customer_phone if customer_phone else None,
                            password_hash=None  # Customers don't need passwords for login
                        )
                        flash(f'New customer "{sanitized_username}" created successfully!', 'info')
                
                # Validate that the user is a customer
                if user.role != RoleEnum.CUSTOMER:
                    flash(f'User "{owner_input}" is not a customer. Only customers can have accounts created for them.', 'error')
                    return render_template('employee/create_account.html', 
                                         account_types=AccountType)
                
                # Check if customer already has accounts (to ensure proper relationship)
                actual_user_id = user.user_id
                existing_accounts = account_service.get_user_accounts(actual_user_id)
                
                # Show information about existing accounts
                if existing_accounts:
                    account_count = len(existing_accounts)
                    account_list = ", ".join([acc.account_id for acc in existing_accounts[:5]])
                    if account_count > 5:
                        account_list += f" and {account_count - 5} more"
                    flash(f'Customer {user.username} already has {account_count} account(s): {account_list}', 'info')
                    flash(f'New account will be linked to the same customer ({actual_user_id})', 'info')
                else:
                    flash(f'This is the first account for customer {user.username} ({actual_user_id})', 'info')
                
                # Create the new account for this customer
                account_type = AccountType(account_type_str)
                user_role = get_current_user_role()
                account = account_service.create_account(account_type, actual_user_id, initial_balance, user_role)
                
                # Get the IBAN from the database model
                from database.repository import AccountRepository
                db_account = AccountRepository.get(account.account_id)
                iban = db_account.iban if db_account else None
                
                # Verify the account was created and linked correctly
                flash(f'✅ Account {account.account_id} created successfully for customer {user.username}!', 'success')
                if iban:
                    flash(f'📋 IBAN: {iban} - Please provide this to the customer for account access', 'info')
                flash(f'Customer {user.username} now has {len(existing_accounts) + 1} account(s) total', 'success')
                
                return redirect(url_for('employee.view_accounts'))
            except BankingSystemError as e:
                flash(f'Error: {str(e)}', 'error')
            except Exception as e:
                flash(f'Unexpected error: {str(e)}', 'error')
        
        return render_template('employee/create_account.html', 
                             account_types=AccountType)


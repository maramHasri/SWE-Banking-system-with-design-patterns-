"""
Flask Banking System - Main Application Entry Point
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash

from config import SECRET_KEY
from domain.roles.role import Role
from utils.exceptions import BankingSystemError

from patterns.observer.observer import AuditLogObserver

from services.account_service import AccountService
from services.transaction_service import TransactionService
from services.notification_service import NotificationService
from services.approval_service import ApprovalService
from reporting.report_service import ReportService

from controllers.customer_controller import customer_bp, init_customer_controller
from controllers.client_controller import client_bp, init_client_controller
from controllers.employee_controller import employee_bp, init_employee_controller
from controllers.admin_controller import admin_bp, init_admin_controller


# --------------------------------------------------
# Flask App Initialization
# --------------------------------------------------

app = Flask(__name__)
app.secret_key = SECRET_KEY


# --------------------------------------------------
# Database & Facade Initialization
# --------------------------------------------------

# Always use database facade (BankingFacadeDB) for persistent storage
# The in-memory facade (BankingFacade) has been removed
try:
    print("🔌 Connecting to PostgreSQL...")

    from database.db import init_db
    from patterns.facade.banking_facade_db import BankingFacadeDB

    init_db(app)
    banking_facade = BankingFacadeDB()

    print("✅ PostgreSQL connected successfully")

except Exception as e:
    print(f"❌ PostgreSQL initialization failed: {e}")
    print("❌ Database connection is required. Please check your database configuration.")
    raise


# --------------------------------------------------
# Observer Initialization
# --------------------------------------------------

audit_observer = AuditLogObserver()
banking_facade.addObserver(audit_observer)


# --------------------------------------------------
# Services Initialization
# --------------------------------------------------

account_service = AccountService(banking_facade)
transaction_service = TransactionService(banking_facade)
notification_service = NotificationService(banking_facade)
approval_service = ApprovalService(banking_facade)
report_service = ReportService(banking_facade)


# --------------------------------------------------
# Controllers Initialization
# --------------------------------------------------

init_customer_controller(account_service, transaction_service, notification_service)
init_client_controller(account_service, transaction_service, notification_service)
init_employee_controller(transaction_service, approval_service, account_service, report_service)
init_admin_controller(
    transaction_service,
    approval_service,
    account_service,
    report_service,
    banking_facade
)


# --------------------------------------------------
# Blueprints Registration
# --------------------------------------------------

app.register_blueprint(customer_bp)
app.register_blueprint(client_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(admin_bp)


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role_str = request.form.get('role') or request.args.get('role')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email_or_phone = request.form.get('email_or_phone', '').strip()

        if not role_str:
            flash('Role is required.', 'error')
            return redirect(url_for('index'))

        if not username:
            flash('Username is required.', 'error')
            return render_template('login.html', role=role_str)

        try:
            role = Role(role_str)

            # For employees and admins, require password + email/phone
            if role in [Role.EMPLOYEE, Role.ADMIN]:
                if not password:
                    flash('Password is required for employee/admin login.', 'error')
                    return render_template('login.html', role=role_str)
                
                if not email_or_phone:
                    flash('Email or phone number is required for employee/admin login.', 'error')
                    return render_template('login.html', role=role_str)

            # Database is always required - use UserRepository for authentication
            try:
                from database.repository import UserRepository
                from security.password import verify_password

                user = UserRepository.get_by_username(username)
                
                # For employees and admins, verify authentication
                if role in [Role.EMPLOYEE, Role.ADMIN]:
                    if not user:
                        flash('Invalid username, email/phone, or password.', 'error')
                        return render_template('login.html', role=role_str)
                    
                    # Verify email or phone matches (handle phone with/without + prefix)
                    email_match = user.email and user.email.lower() == email_or_phone.lower()
                    phone_match = user.phone and (user.phone == email_or_phone or 
                                                  user.phone == f"+{email_or_phone}" or
                                                  user.phone.lstrip('+') == email_or_phone.lstrip('+'))
                    
                    if not email_match and not phone_match:
                        flash('Invalid username, email/phone, or password.', 'error')
                        return render_template('login.html', role=role_str)
                    
                    # Verify password
                    if not verify_password(user.password_hash, password):
                        flash('Invalid username, email/phone, or password.', 'error')
                        return render_template('login.html', role=role_str)
                    
                    # Verify role matches
                    if user.role.value != role.value:
                        flash(f'User {username} is not registered as {role.value}.', 'error')
                        return render_template('login.html', role=role_str)
                    
                    # Check if user is active
                    if not user.is_active:
                        flash('Your account has been deactivated. Please contact an administrator.', 'error')
                        return render_template('login.html', role=role_str)
                
                # For customers, create user if doesn't exist (backward compatibility)
                elif role == Role.CUSTOMER:
                    if not user:
                        user = UserRepository.create(
                            user_id=f"USER_{username.upper()}",
                            username=username,
                            role=role
                        )
                    elif user.role.value != role.value:
                        UserRepository.update_role(user.user_id, role)

                session['user_id'] = user.user_id
                session['username'] = user.username
                session['user_role'] = user.role.value

            except Exception as e:
                flash(f'Login failed: {str(e)}. Database connection required.', 'error')
                return render_template('login.html', role=role_str)

            banking_facade.set_current_user(session['user_id'])

            flash(f'Logged in as {role.value.title()} ({username})', 'success')

            if role == Role.CUSTOMER:
                return redirect(url_for('customer.dashboard'))
            if role == Role.EMPLOYEE:
                return redirect(url_for('employee.dashboard'))
            if role == Role.ADMIN:
                return redirect(url_for('admin.dashboard'))

        except ValueError:
            flash('Invalid role.', 'error')
            return redirect(url_for('index'))

    role_str = request.args.get('role')
    if not role_str:
        flash('Please select a role first.', 'error')
        return redirect(url_for('index'))

    return render_template('login.html', role=role_str)


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))


# --------------------------------------------------
# Error Handling
# --------------------------------------------------

@app.errorhandler(BankingSystemError)
def handle_banking_error(error):
    """Handle banking system errors and prevent redirect loops"""
    from utils.exceptions import UnauthorizedAccessError, UnauthorizedOperationError
    
    flash(str(error), 'error')
    
    # For unauthorized access or unauthorized operations
    if isinstance(error, (UnauthorizedAccessError, UnauthorizedOperationError)):
        # Clear session if unauthorized
        if 'user_role' not in session:
            session.clear()
            return redirect(url_for('index'))
        # If user is logged in but lacks permission, go to their dashboard
        user_role = session.get('user_role')
        if user_role == 'customer':
            return redirect(url_for('customer.dashboard'))
        elif user_role == 'employee':
            return redirect(url_for('employee.dashboard'))
        elif user_role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('index'))
    
    # For other errors, redirect to index if referrer is same page or missing
    referrer = request.referrer
    if referrer and referrer != request.url:
        return redirect(referrer)
    return redirect(url_for('index'))


# --------------------------------------------------
# Application Entry Point
# --------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

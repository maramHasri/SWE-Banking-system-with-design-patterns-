# Flask Banking System

A professional Flask-based Banking System demonstrating structural and behavioral design patterns, SOLID principles, and clean architecture.

## Features

### Role-Based Access Control
- **ATM/Client**: Perform transactions (deposit, withdraw, transfer) using account number - no login required
- **Employee**: Create customer accounts, approve medium-value transactions ($25,000 - $75,000), view daily reports, manage accounts
- **Admin**: Approve high-value transactions (>$75,000), view financial summaries, manage retained earnings, audit logs

### Account Management
- Multiple account types: Checking, Savings, Investment, Loan, Business Loan
- Account states: Active, Frozen, Suspended, Closed
- Hierarchical accounts (parent/child) support via Composite pattern

### Transaction System
- Deposit, Withdrawal, Transfer operations
- Automatic approval workflow based on amount:
  - ≤ $25,000: Auto-approved
  - $25,000 - $75,000: Employee approval required
  - > $75,000: Admin approval required
- State-based operation restrictions

### Design Patterns Implemented

#### Structural Patterns
1. **Facade**: Unified interface (`BankingFacade`) for all banking operations
2. **Composite**: Hierarchical account structures (`AccountComponent`, `AccountComposite`, `AccountLeaf`)
3. **Decorator**: Dynamic account features (Overdraft Protection, Investment Bonus, Premium Savings, Business Loan Extension)
4. **Adapter**: External payment gateway integration (`PaymentGatewayAdapter`, `LegacyBankingAdapter`)

#### Behavioral Patterns
1. **State**: Account state management (`ActiveState`, `FrozenState`, `SuspendedState`, `ClosedState`)
2. **Chain of Responsibility**: Transaction approval workflow (`AutoApprovalHandler`, `EmployeeApprovalHandler`, `AdminApprovalHandler`)
3. **Observer**: Event notifications and audit logging (`NotificationObserver`, `AuditLogObserver`, `ReportingObserver`)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Login
1. Select your role (Customer, Employee, or Admin)
2. Enter a user ID (optional, defaults to "user1")
3. Click Login

### Customer Workflow
1. **Create Account**: Choose account type and initial balance
2. **Make Transaction**: 
   - Select transaction type (Deposit/Withdrawal/Transfer)
   - Choose account(s)
   - Enter amount
   - Submit (may require approval for large amounts)
3. **View Notifications**: See transaction updates and balance changes

### Employee Workflow
1. **Dashboard**: View pending approvals and daily transaction summary
2. **Approve Transactions**: Approve medium-value transactions ($25K-$75K)
3. **View Reports**: See daily transaction reports
4. **Manage Accounts**: Change account states (Active/Frozen/Suspended/Closed)

### Admin Workflow
1. **Dashboard**: View pending high-value approvals and financial summary
2. **Approve Transactions**: Approve transactions over $75,000
3. **Financials**: View retained earnings, update financial data, view audit logs
4. **All Transactions**: View complete transaction history

## Project Structure

```
banking_system/
├── app.py                  # Flask application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── domain/                # Domain models
│   ├── account/          # Account models and types
│   ├── transaction/      # Transaction models
│   ├── state/            # Account state pattern
│   └── roles/            # Role definitions
├── patterns/             # Design patterns
│   ├── facade/           # Facade pattern
│   ├── composite/        # Composite pattern
│   ├── decorator/        # Decorator pattern
│   ├── adapter/          # Adapter pattern
│   ├── observer/         # Observer pattern
│   ├── state/            # State pattern (domain/state)
│   └── chain/            # Chain of Responsibility
├── services/             # Business logic services
│   ├── account_service.py
│   ├── transaction_service.py
│   ├── notification_service.py
│   └── approval_service.py
├── controllers/          # Flask route handlers
│   ├── customer_controller.py
│   ├── employee_controller.py
│   └── admin_controller.py
├── security/             # RBAC and authentication
├── reporting/            # Report generation
├── utils/                # Utilities (exceptions, logging)
└── templates/            # HTML templates
    ├── customer/
    ├── employee/
    └── admin/
```

## Architecture Principles

- **SOLID Principles**: Strictly followed throughout
- **Separation of Concerns**: Clear separation between domain, services, controllers, and presentation
- **Dependency Injection**: Services injected via constructors
- **Interface Segregation**: Abstract base classes for all patterns
- **Open/Closed Principle**: Extensible without modifying existing code

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## Database Support

The system now supports **PostgreSQL** for persistent storage!

### Quick Setup:
1. Install PostgreSQL (see `POSTGRESQL_SETUP_GUIDE.md`)
2. Create database and user (see `DATABASE_SETUP_STEPS.md`)
3. Install dependencies: `pip install -r requirements.txt`
4. Test connection: `python test_db_connection.py`
5. Run app: `python app.py`

### Configuration:
- **PostgreSQL**: Set `USE_POSTGRESQL = True` in `config.py`
- **In-Memory**: Set `USE_POSTGRESQL = False` (default fallback)

The system automatically:
- Creates tables on first run
- Falls back to in-memory storage if PostgreSQL is unavailable
- Uses database for all persistent operations

## Notes

- PostgreSQL is recommended for production use
- In-memory storage is available for development/testing
- Session-based authentication is simplified for demonstration
- All design patterns are explicitly implemented and documented

## License

This project is for educational and demonstration purposes.


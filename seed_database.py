"""
Database Seeding Script
Populates the database with sample users, accounts, and transactions for testing
"""
import sys
from datetime import datetime

# Fix Windows console encoding
from utils.console import setup_console_encoding
setup_console_encoding()

from config import USE_POSTGRESQL
from database.db import db
from database.repository import (
    UserRepository, AccountRepository, TransactionRepository, FinancialsRepository
)
from database.models import TransactionStatusEnum
from domain.roles.role import Role
from domain.account.account_type import AccountType
from domain.transaction.transaction import TransactionType
from security.password import hash_password

print("=" * 60)
print("Database Seeding Script")
print("=" * 60)

# Create Flask app with database
if USE_POSTGRESQL:
    try:
        from utils.console import create_app_with_db
        app = create_app_with_db()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("💡 Make sure PostgreSQL is running and configured correctly")
        sys.exit(1)
else:
    print("⚠️  PostgreSQL is disabled. This script requires PostgreSQL.")
    sys.exit(1)

with app.app_context():
    try:
        print("\n🌱 Starting database seeding...\n")
        
        # Check what exists first
        existing_users = UserRepository.get_all()
        if existing_users:
            print(f"⚠️  Found {len(existing_users)} existing user(s)")
            response = input("Do you want to clear existing data? (yes/no): ").strip().lower()
            if response == 'yes':
                print("🗑️  Clearing existing data...")
                # Delete in correct order (transactions -> accounts -> users)
                from database.models import Transaction as TransactionModel
                from database.models import Account as AccountModel
                from database.models import User as UserModel
                
                TransactionModel.query.delete()
                AccountModel.query.delete()
                UserModel.query.delete()
                db.session.commit()
                print("✅ Existing data cleared")
            else:
                print("ℹ️  Keeping existing data, will skip duplicates")
        else:
            print("✅ No existing data found")
        
        print("\n" + "=" * 60)
        print("Creating Users")
        print("=" * 60)
        
        # Create Admin Users (with passwords and phone numbers)
        admin_users = [
            {
                "user_id": "USER_ADMIN1", 
                "username": "admin1", 
                "email": "admin1@bank.com", 
                "phone": "+1234567890",
                "password": "admin123",
                "role": Role.ADMIN
            },
            {
                "user_id": "USER_ADMIN2", 
                "username": "admin2", 
                "email": "admin2@bank.com", 
                "phone": "+1234567891",
                "password": "admin456",
                "role": Role.ADMIN
            },
        ]
        
        # Create Employee Users (with passwords and phone numbers)
        employee_users = [
            {
                "user_id": "USER_EMP1", 
                "username": "employee1", 
                "email": "emp1@bank.com", 
                "phone": "+1234567892",
                "password": "emp123",
                "role": Role.EMPLOYEE
            },
            {
                "user_id": "USER_EMP2", 
                "username": "employee2", 
                "email": "emp2@bank.com", 
                "phone": "+1234567893",
                "password": "emp456",
                "role": Role.EMPLOYEE
            },
            {
                "user_id": "USER_EMP3", 
                "username": "employee3", 
                "email": "emp3@bank.com", 
                "phone": "+1234567894",
                "password": "emp789",
                "role": Role.EMPLOYEE
            },
        ]
        
        # Create Customer Users
        customer_users = [
            {"user_id": "USER_CUST1", "username": "john_doe", "email": "john.doe@email.com", "role": Role.CUSTOMER},
            {"user_id": "USER_CUST2", "username": "jane_smith", "email": "jane.smith@email.com", "role": Role.CUSTOMER},
            {"user_id": "USER_CUST3", "username": "bob_wilson", "email": "bob.wilson@email.com", "role": Role.CUSTOMER},
            {"user_id": "USER_CUST4", "username": "alice_brown", "email": "alice.brown@email.com", "role": Role.CUSTOMER},
            {"user_id": "USER_CUST5", "username": "charlie_davis", "email": "charlie.davis@email.com", "role": Role.CUSTOMER},
        ]
        
        all_users = admin_users + employee_users + customer_users
        created_users = {}
        
        for user_data in all_users:
            try:
                # Check if user already exists
                existing = UserRepository.get_by_username(user_data["username"])
                if existing:
                    print(f"⏭️  User '{user_data['username']}' already exists, skipping...")
                    created_users[user_data["user_id"]] = existing
                else:
                    # Hash password for employees and admins
                    password_hash = None
                    if "password" in user_data:
                        password_hash = hash_password(user_data["password"])
                    
                    user = UserRepository.create(
                        user_id=user_data["user_id"],
                        username=user_data["username"],
                        role=user_data["role"],
                        email=user_data.get("email"),
                        phone=user_data.get("phone"),
                        password_hash=password_hash
                    )
                    created_users[user_data["user_id"]] = user
                    
                    # Print login info for employees and admins
                    if user_data["role"] in [Role.EMPLOYEE, Role.ADMIN]:
                        login_info = f"Email: {user_data.get('email')} or Phone: {user_data.get('phone')}, Password: {user_data.get('password')}"
                        print(f"✅ Created {user_data['role'].value}: {user_data['username']} ({login_info})")
                    else:
                        print(f"✅ Created {user_data['role'].value}: {user_data['username']} ({user_data.get('email', 'N/A')})")
            except Exception as e:
                print(f"❌ Failed to create user {user_data['username']}: {e}")
        
        print("\n" + "=" * 60)
        print("Creating Accounts")
        print("=" * 60)
        
        # Create accounts for customers
        # Note: Account IDs use format ACC_XXXXXXXX (8 alphanumeric chars) to match system pattern ACC_[A-Z0-9]+
        accounts_data = [
            # Customer 1 (john_doe) - Multiple accounts
            {"account_id": "ACC_00000001", "owner_id": "USER_CUST1", "account_type": AccountType.CHECKING, "balance": 5000.00},
            {"account_id": "ACC_00000002", "owner_id": "USER_CUST1", "account_type": AccountType.SAVINGS, "balance": 15000.00},
            {"account_id": "ACC_00000003", "owner_id": "USER_CUST1", "account_type": AccountType.INVESTMENT, "balance": 25000.00},
            
            # Customer 2 (jane_smith) - Multiple accounts
            {"account_id": "ACC_00000004", "owner_id": "USER_CUST2", "account_type": AccountType.CHECKING, "balance": 3500.00},
            {"account_id": "ACC_00000005", "owner_id": "USER_CUST2", "account_type": AccountType.SAVINGS, "balance": 12000.00},
            
            # Customer 3 (bob_wilson) - Single account
            {"account_id": "ACC_00000006", "owner_id": "USER_CUST3", "account_type": AccountType.CHECKING, "balance": 8000.00},
            
            # Customer 4 (alice_brown) - Multiple accounts including loan
            {"account_id": "ACC_00000007", "owner_id": "USER_CUST4", "account_type": AccountType.CHECKING, "balance": 2000.00},
            {"account_id": "ACC_00000008", "owner_id": "USER_CUST4", "account_type": AccountType.SAVINGS, "balance": 5000.00},
            {"account_id": "ACC_00000009", "owner_id": "USER_CUST4", "account_type": AccountType.LOAN, "balance": -15000.00},
            
            # Customer 5 (charlie_davis) - Business account
            {"account_id": "ACC_00000010", "owner_id": "USER_CUST5", "account_type": AccountType.CHECKING, "balance": 10000.00},
            {"account_id": "ACC_00000011", "owner_id": "USER_CUST5", "account_type": AccountType.BUSINESS_LOAN, "balance": -50000.00},
        ]
        
        created_accounts = {}
        
        for account_data in accounts_data:
            try:
                # Check if account already exists
                existing = AccountRepository.get(account_data["account_id"])
                if existing:
                    print(f"⏭️  Account '{account_data['account_id']}' already exists, skipping...")
                    created_accounts[account_data["account_id"]] = existing
                else:
                    account = AccountRepository.create(
                        account_id=account_data["account_id"],
                        account_type=account_data["account_type"],
                        owner_id=account_data["owner_id"],
                        balance=account_data["balance"]
                    )
                    created_accounts[account_data["account_id"]] = account
                    owner = created_users.get(account_data["owner_id"])
                    owner_name = owner.username if owner else account_data["owner_id"]
                    iban_display = account.iban if account.iban else "IBAN pending"
                    print(f"✅ Created {account_data['account_type'].value} account {account_data['account_id']} for {owner_name}: ${account_data['balance']:,.2f} (IBAN: {iban_display})")
            except Exception as e:
                if "not found" not in str(e).lower():
                    print(f"❌ Failed to create account {account_data['account_id']}: {e}")
                else:
                    # Account doesn't exist, create it
                    account = AccountRepository.create(
                        account_id=account_data["account_id"],
                        account_type=account_data["account_type"],
                        owner_id=account_data["owner_id"],
                        balance=account_data["balance"]
                    )
                    created_accounts[account_data["account_id"]] = account
                    owner = created_users.get(account_data["owner_id"])
                    owner_name = owner.username if owner else account_data["owner_id"]
                    print(f"✅ Created {account_data['account_type'].value} account {account_data['account_id']} for {owner_name}: ${account_data['balance']:,.2f}")
        
        print("\n" + "=" * 60)
        print("Creating Transactions")
        print("=" * 60)
        
        # Create sample transactions
        # Note: Account IDs must match the format used above (ACC_XXXXXXXX)
        transactions_data = [
            # Deposits
            {"transaction_id": "TXN001", "type": TransactionType.DEPOSIT, "account_id": "ACC_00000001", "amount": 1000.00, "description": "Initial deposit", "status": TransactionStatusEnum.COMPLETED},
            {"transaction_id": "TXN002", "type": TransactionType.DEPOSIT, "account_id": "ACC_00000002", "amount": 5000.00, "description": "Savings deposit", "status": TransactionStatusEnum.COMPLETED},
            {"transaction_id": "TXN003", "type": TransactionType.DEPOSIT, "account_id": "ACC_00000004", "amount": 500.00, "description": "Paycheck deposit", "status": TransactionStatusEnum.COMPLETED},
            
            # Withdrawals
            {"transaction_id": "TXN004", "type": TransactionType.WITHDRAWAL, "account_id": "ACC_00000001", "amount": 200.00, "description": "ATM withdrawal", "status": TransactionStatusEnum.COMPLETED},
            {"transaction_id": "TXN005", "type": TransactionType.WITHDRAWAL, "account_id": "ACC_00000006", "amount": 500.00, "description": "Cash withdrawal", "status": TransactionStatusEnum.COMPLETED},
            
            # Transfers
            {"transaction_id": "TXN006", "type": TransactionType.TRANSFER, "account_id": "ACC_00000001", "target_account_id": "ACC_00000002", "amount": 1000.00, "description": "Transfer to savings", "status": TransactionStatusEnum.COMPLETED},
            {"transaction_id": "TXN007", "type": TransactionType.TRANSFER, "account_id": "ACC_00000004", "target_account_id": "ACC_00000005", "amount": 300.00, "description": "Monthly savings transfer", "status": TransactionStatusEnum.COMPLETED},
            
            # Pending transactions (for employee/admin approval)
            {"transaction_id": "TXN008", "type": TransactionType.WITHDRAWAL, "account_id": "ACC_00000001", "amount": 5000.00, "description": "Large withdrawal - pending approval", "status": TransactionStatusEnum.PENDING},
            {"transaction_id": "TXN009", "type": TransactionType.TRANSFER, "account_id": "ACC_00000002", "target_account_id": "ACC_00000004", "amount": 10000.00, "description": "Large transfer - pending approval", "status": TransactionStatusEnum.PENDING},
            {"transaction_id": "TXN010", "type": TransactionType.WITHDRAWAL, "account_id": "ACC_00000006", "amount": 8000.00, "description": "Large withdrawal request", "status": TransactionStatusEnum.PENDING},
            
            # More completed transactions
            {"transaction_id": "TXN011", "type": TransactionType.DEPOSIT, "account_id": "ACC_00000007", "amount": 1500.00, "description": "Salary deposit", "status": TransactionStatusEnum.COMPLETED},
            {"transaction_id": "TXN012", "type": TransactionType.DEPOSIT, "account_id": "ACC_00000010", "amount": 5000.00, "description": "Business deposit", "status": TransactionStatusEnum.COMPLETED},
        ]
        
        created_transactions = {}
        
        for txn_data in transactions_data:
            try:
                # Check if transaction already exists
                existing = TransactionRepository.get(txn_data["transaction_id"])
                if existing:
                    print(f"⏭️  Transaction '{txn_data['transaction_id']}' already exists, skipping...")
                    created_transactions[txn_data["transaction_id"]] = existing
                else:
                    # Create transaction
                    transaction = TransactionRepository.create(
                        transaction_id=txn_data["transaction_id"],
                        transaction_type=txn_data["type"],
                        account_id=txn_data["account_id"],
                        amount=txn_data["amount"],
                        target_account_id=txn_data.get("target_account_id"),
                        description=txn_data["description"]
                    )
                    
                    # Update status if not pending
                    if txn_data["status"] != TransactionStatusEnum.PENDING:
                        approved_by = "USER_EMP1" if txn_data["status"] == TransactionStatusEnum.COMPLETED else None
                        TransactionRepository.update_status(
                            transaction_id=txn_data["transaction_id"],
                            status=txn_data["status"],
                            approved_by=approved_by
                        )
                    
                    created_transactions[txn_data["transaction_id"]] = transaction
                    status_emoji = "✅" if txn_data["status"] == TransactionStatusEnum.COMPLETED else "⏳" if txn_data["status"] == TransactionStatusEnum.PENDING else "❌"
                    print(f"{status_emoji} Created {txn_data['type'].value} transaction {txn_data['transaction_id']}: ${txn_data['amount']:,.2f} - {txn_data['status'].value}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    print(f"❌ Failed to create transaction {txn_data['transaction_id']}: {e}")
                else:
                    # Create it anyway
                    transaction = TransactionRepository.create(
                        transaction_id=txn_data["transaction_id"],
                        transaction_type=txn_data["type"],
                        account_id=txn_data["account_id"],
                        amount=txn_data["amount"],
                        target_account_id=txn_data.get("target_account_id"),
                        description=txn_data["description"]
                    )
                    
                    if txn_data["status"] != TransactionStatusEnum.PENDING:
                        approved_by = "USER_EMP1" if txn_data["status"] == TransactionStatusEnum.COMPLETED else None
                        TransactionRepository.update_status(
                            transaction_id=txn_data["transaction_id"],
                            status=txn_data["status"],
                            approved_by=approved_by
                        )
                    
                    created_transactions[txn_data["transaction_id"]] = transaction
                    status_emoji = "✅" if txn_data["status"] == TransactionStatusEnum.COMPLETED else "⏳" if txn_data["status"] == TransactionStatusEnum.PENDING else "❌"
                    print(f"{status_emoji} Created {txn_data['type'].value} transaction {txn_data['transaction_id']}: ${txn_data['amount']:,.2f} - {txn_data['status'].value}")
        
        # Initialize bank financials
        print("\n" + "=" * 60)
        print("Initializing Bank Financials")
        print("=" * 60)
        
        try:
            financials = FinancialsRepository.get_or_create()
            print(f"✅ Bank financials initialized: Retained Earnings = ${financials.retained_earnings:,.2f}")
        except Exception as e:
            print(f"⚠️  Could not initialize financials: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Database Seeding Completed!")
        print("=" * 60)
        
        # Summary
        print("\n📊 Summary:")
        print(f"   Users created: {len(created_users)}")
        print(f"   Accounts created: {len(created_accounts)}")
        print(f"   Transactions created: {len(created_transactions)}")
        
        print("\n👥 Test Users:")
        print("\n   Admins (Login: Username + Email/Phone + Password):")
        print("     - admin1")
        print("       Email: admin1@bank.com or Phone: +1234567890")
        print("       Password: admin123")
        print("     - admin2")
        print("       Email: admin2@bank.com or Phone: +1234567891")
        print("       Password: admin456")
        print("\n   Employees (Login: Username + Email/Phone + Password):")
        print("     - employee1")
        print("       Email: emp1@bank.com or Phone: +1234567892")
        print("       Password: emp123")
        print("     - employee2")
        print("       Email: emp2@bank.com or Phone: +1234567893")
        print("       Password: emp456")
        print("     - employee3")
        print("       Email: emp3@bank.com or Phone: +1234567894")
        print("       Password: emp789")
        print("\n   Customers:")
        print("     - john_doe (john.doe@email.com) - 3 accounts")
        print("     - jane_smith (jane.smith@email.com) - 2 accounts")
        print("     - bob_wilson (bob.wilson@email.com) - 1 account")
        print("     - alice_brown (alice.brown@email.com) - 3 accounts (including loan)")
        print("     - charlie_davis (charlie.davis@email.com) - 2 accounts (including business loan)")
        
        print("\n💡 You can now:")
        print("   1. Run: python app.py")
        print("   2. Login with any of the usernames above")
        print("   3. Test different user roles and workflows")
        print("\n📝 Test Accounts for Customer Login (Account ID + IBAN):")
        print("   Note: Each account has a unique IBAN. Check the account creation output above for IBANs.")
        print("   Login format: Account ID + IBAN (both required)")
        print("\n   Example accounts:")
        for acc_id, acc in list(created_accounts.items())[:5]:
            if acc and hasattr(acc, 'iban') and acc.iban:
                print(f"     - Account: {acc_id}, IBAN: {acc.iban}")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        sys.exit(1)

print("\n" + "=" * 60)


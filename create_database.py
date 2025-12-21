"""
Automated Database Creation Script
This script will create the database and user for you
Uses database.db.setup_database() function
"""
import sys
from utils.console import setup_console_encoding
from database.db import setup_database

setup_console_encoding()

print("=" * 60)
print("Automated Database Setup")
print("=" * 60)

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Get PostgreSQL admin credentials
print("\n📋 PostgreSQL Admin Credentials")
print("-" * 60)
print("You need your PostgreSQL admin (postgres user) password.")
print("This is the password you set during PostgreSQL installation.\n")

postgres_password = input("Enter PostgreSQL admin password (postgres user): ").strip()

if not postgres_password:
    print("❌ Password is required!")
    sys.exit(1)

try:
    print("\n🔌 Setting up database...")
    
    if setup_database(postgres_password):
        print("\n" + "=" * 60)
        print("✅ Database setup completed successfully!")
        print("=" * 60)
        print("\n📋 Summary:")
        print("   Database: banking_system")
        print("   User: banking_user")
        print("   Password: banking_pass")
        print("\n🧪 Testing connection...")
        
        # Test connection
        test_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="banking_user",
            password="banking_pass",
            database="banking_system"
        )
        test_conn.close()
        print("✅ Connection test passed!")
        print("\n🚀 You can now run: python app.py")
        print("   Tables will be created automatically on first run.")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)
    
except psycopg2.OperationalError as e:
    if "password authentication failed" in str(e):
        print("\n❌ Password authentication failed!")
        print("   Please check your PostgreSQL admin password.")
    elif "could not connect" in str(e).lower():
        print("\n❌ Cannot connect to PostgreSQL!")
        print("   Make sure PostgreSQL is running:")
        print("   - Check Services (services.msc)")
        print("   - Or start from Start Menu > PostgreSQL")
    else:
        print(f"\n❌ Connection error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)



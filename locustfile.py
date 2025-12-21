"""
Locust Load Test for Bank Account Creation
Simulates an employee creating 1000 bank accounts
"""

from locust import HttpUser, task, between
import random


class BankAccountCreationUser(HttpUser):
    """
    Simulates an employee user creating bank accounts
    """
    # Wait between 1 and 3 seconds between requests
    wait_time = between(1, 3)
    
    # Counter for generating unique account IDs
    account_counter = 0
    
    def on_start(self):
        """
        Called when a simulated user starts.
        Logs in as an employee to get authenticated session.
        """
        # Employee credentials (adjust these based on your seed data)
        self.username = "employee1"
        self.password = "emp123"
        self.email_or_phone = "emp1@bank.com"  # or "+1234567892"
        
        # Login as employee
        login_data = {
            "role": "employee",
            "username": self.username,
            "password": self.password,
            "email_or_phone": self.email_or_phone
        }
        
        response = self.client.post("/login", data=login_data, name="Employee Login")
        
        if response.status_code == 200 or response.status_code == 302:
            print(f"✅ Successfully logged in as {self.username}")
        else:
            print(f"❌ Login failed with status {response.status_code}")
    
    @task
    def create_bank_account(self):
        """
        Creates a new bank account for a customer.
        Generates unique customer usernames and account IDs.
        """
        # Increment counter for unique IDs
        BankAccountCreationUser.account_counter += 1
        account_number = BankAccountCreationUser.account_counter
        
        # Generate unique customer username
        customer_username = f"load_test_customer_{account_number}"
        
        # Account types available in the system
        account_types = ["checking", "savings", "investment"]
        
        # Random account type
        account_type = random.choice(account_types)
        
        # Random initial balance between $0 and $10,000
        initial_balance = round(random.uniform(0, 10000), 2)
        
        # Prepare form data for account creation
        account_data = {
            "owner_id": customer_username,
            "account_type": account_type,
            "initial_balance": initial_balance,
            "customer_email": f"customer_{account_number}@test.com",
            "customer_phone": f"+1234567{account_number:04d}"
        }
        
        # Create account
        response = self.client.post(
            "/employee/create_account",
            data=account_data,
            name="Create Bank Account",
            catch_response=True
        )
        
        # Check if account creation was successful
        if response.status_code == 200 or response.status_code == 302:
            # Check response content for success indicators
            if "created successfully" in response.text.lower() or response.status_code == 302:
                response.success()
                print(f"✅ Account #{account_number} created: {customer_username} - {account_type} - ${initial_balance}")
            else:
                response.failure(f"Account creation may have failed. Status: {response.status_code}")
        else:
            response.failure(f"Failed to create account. Status: {response.status_code}")
    
    def on_stop(self):
        """
        Called when a simulated user stops.
        """
        print(f"🏁 Finished creating accounts. Total accounts created: {BankAccountCreationUser.account_counter}")


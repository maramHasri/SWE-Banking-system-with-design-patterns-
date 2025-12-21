# Load Test Guide - Bank Account Creation

This guide explains how to run load tests using Locust to simulate creating 1000 bank accounts.

## Prerequisites

1. **Locust is installed** (already installed ✅)
2. **Flask application is running** on `http://localhost:5000`
3. **Database is seeded** with employee credentials:
   - Username: `employee1`
   - Password: `emp123`
   - Email: `emp1@bank.com` (or Phone: `+1234567892`)

## Running the Load Test

### Option 1: Web UI (Recommended)

1. **Start the Flask application** (in one terminal):
   ```bash
   python app.py
   ```

2. **Start Locust** (in another terminal):
   ```bash
   locust
   ```

3. **Open your browser** and go to:
   ```
   http://localhost:8089
   ```

4. **Configure the test**:
   - Number of users: `10` (or more for faster testing)
   - Spawn rate: `2` (users per second)
   - Host: `http://localhost:5000`

5. **Start the test** and watch the real-time statistics!

### Option 2: Command Line (Headless Mode)

Run without the web UI:

```bash
locust --headless -u 10 -r 2 -t 5m --host http://localhost:5000
```

**Parameters:**
- `--headless`: Run without web UI
- `-u 10`: 10 concurrent users
- `-r 2`: Spawn 2 users per second
- `-t 5m`: Run for 5 minutes
- `--host`: Target server URL

### Option 3: Create Exactly 1000 Accounts

To create exactly 1000 accounts, you can modify the locustfile or run:

```bash
locust --headless -u 1 -r 1 -t 30m --host http://localhost:5000
```

This runs with 1 user creating accounts sequentially (with 1-3 second delays).

## What the Test Does

1. **Logs in as employee** (`employee1`) to authenticate
2. **Creates accounts** with:
   - Unique customer usernames: `load_test_customer_1`, `load_test_customer_2`, etc.
   - Random account types: checking, savings, or investment
   - Random initial balances: $0 to $10,000
   - Unique email and phone numbers
3. **Waits 1-3 seconds** between each account creation (realistic behavior)

## Monitoring Results

The Locust web UI shows:
- **Total requests**: Number of API calls made
- **Requests per second**: Throughput
- **Response times**: Min, max, median, 95th percentile
- **Failures**: Any errors encountered
- **Charts**: Real-time graphs of performance

## Expected Results

- **1000 accounts** should be created successfully
- **Response times** should be reasonable (< 1 second per account)
- **No failures** if the system is healthy
- **Database** will contain accounts with IDs like `ACC_XXXXXXXX`

## Troubleshooting

### Login Fails
- Check that employee credentials match seed data
- Verify Flask app is running on port 5000
- Check database connection

### Account Creation Fails
- Verify database has space
- Check for unique constraint violations
- Review Flask application logs

### Locust Not Found
```bash
pip install locust
```

## Stopping the Test

- **Web UI**: Click "Stop" button
- **Command Line**: Press `Ctrl+C`

## Cleanup After Testing

To remove test accounts from database:

```sql
DELETE FROM accounts WHERE owner_id LIKE 'USER_LOAD_TEST_CUSTOMER_%';
DELETE FROM users WHERE user_id LIKE 'USER_LOAD_TEST_CUSTOMER_%';
```

Or re-seed the database:
```bash
python seed_database.py
```


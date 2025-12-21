"""
Configuration module for Banking System
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Database configuration
# PostgreSQL connection string format: postgresql://username:password@localhost:5432/database_name
DATABASE_URI = "postgresql+psycopg2://banking_user:12345678@localhost:5432/banking_system"
USE_POSTGRESQL = True
# USE_POSTGRESQL = os.getenv('USE_POSTGRESQL', 'True').lower() == 'true'

# Secret key for sessions
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Transaction approval thresholds
AUTO_APPROVE_THRESHOLD = 25000.0
EMPLOYEE_APPROVE_THRESHOLD = 75000.0

# Flask configuration
DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'


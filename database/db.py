"""
Database connection and session management
Uses Flask-SQLAlchemy for ORM and session handling
"""

import sys
import psycopg2
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import DATABASE_URI

# Flask-SQLAlchemy instance
db = SQLAlchemy()


def init_db(app: Flask):
    """
    Initialize database with Flask app.

    This function:
    1. Configures Flask-SQLAlchemy
    2. Binds the database to the Flask app
    3. Creates all tables defined in database.models

    Must be called once when the app starts,
    BEFORE importing any repository modules.
    """

    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Bind SQLAlchemy to app
    db.init_app(app)

    # Create tables inside application context
    with app.app_context():
        db.create_all()


def setup_database(postgres_password: str):
    """
    Setup PostgreSQL database and user.
    This function creates the database and user if they don't exist.
    
    Args:
        postgres_password: PostgreSQL admin (postgres user) password
        
    Returns:
        True if setup successful, False otherwise
    """
    try:
        # Connect as postgres superuser
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=postgres_password,
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'banking_system'")
        if not cursor.fetchone():
            cursor.execute("CREATE DATABASE banking_system")
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'banking_user'")
        if not cursor.fetchone():
            cursor.execute("CREATE USER banking_user WITH PASSWORD 'banking_pass'")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE banking_system TO banking_user")
        
        # Connect to banking_system database to grant schema privileges
        conn.close()
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=postgres_password,
            database="banking_system"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("GRANT ALL ON SCHEMA public TO banking_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO banking_user")
        cursor.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO banking_user")
        cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO banking_user")
        cursor.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO banking_user")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

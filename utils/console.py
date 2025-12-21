"""
Console utilities for cross-platform compatibility
"""
import sys
import os
from flask import Flask
from database.db import init_db
from config import DATABASE_URI


def setup_console_encoding():
    """
    Setup UTF-8 encoding for Windows console.
    Should be called at the start of scripts that output to console.
    """
    if sys.platform == 'win32':
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')


def create_app_with_db():
    """
    Create and configure Flask app with database.
    Returns configured Flask app instance.
    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_db(app)
    return app


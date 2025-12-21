"""
Role definitions for Role-Based Access Control
"""
from enum import Enum


class Role(Enum):
    """User roles in the banking system"""
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    ADMIN = "admin"


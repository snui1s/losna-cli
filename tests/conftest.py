"""
tests/conftest.py — Global fixtures for core Losna CLI tests.
Ensures SQLite schema is initialized for clean test environments (e.g. CI/CD runners).
"""

import os
import pytest
from src.agent import db
from src.agent import config

@pytest.fixture(autouse=True, scope="session")
def initialize_test_database():
    """Initializes SQLite database tables before running the test suite."""
    db.init_db()
    yield

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def clean_test_db():
    """Delete the SQLite test file before each session so tests are idempotent."""
    db_path = "./test_smoke.db"
    if os.path.exists(db_path):
        os.remove(db_path)

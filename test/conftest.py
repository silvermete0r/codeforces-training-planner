import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def app():
    from app import app
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

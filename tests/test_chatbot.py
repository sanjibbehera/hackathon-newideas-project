import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Add project root to path

import pytest
# tests/test.py
from fastapi.testclient import TestClient
from app.main import app  # Import the FastAPI app instance

client = TestClient(app)

def test_app_is_reachable():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
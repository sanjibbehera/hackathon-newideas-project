import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Add project root to path

import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_app_is_reachable():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
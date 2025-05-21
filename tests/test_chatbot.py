import sys
from pathlib import Path

# Add project root to Python path (only once)
sys.path.append(str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app 

@pytest.fixture
def client():
    return TestClient(app)

def test_app_is_reachable(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
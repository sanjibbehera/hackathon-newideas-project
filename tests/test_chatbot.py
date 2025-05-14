import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Add project root to path

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Chatbot is ready"}

@pytest.mark.asyncio
async def test_chatbot_response():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/chat",  # Replace with your actual endpoint
            json={"message": "Hello"}
        )
    assert response.status_code == 200
    assert "response" in response.json()
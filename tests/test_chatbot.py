import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # Add project root to path

import pytest
from httpx import AsyncClient
from app.main import app
from fastapi import FastAPI

# Create a test app fixture
@pytest.fixture
def test_app():
    return app

# Async client fixture
@pytest.fixture
async def async_client(test_app: FastAPI):
    async with AsyncClient(app=test_app, base_url="http://testserver") as client:
        yield client

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Chatbot is ready"}

@pytest.mark.asyncio
async def test_chatbot_response(async_client: AsyncClient):
    response = await async_client.post(
        "/chat",
        json={"message": "Hello"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
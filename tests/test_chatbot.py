import pytest
from httpx import AsyncClient
from main import app  # Replace `main` with your app's module name

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
            "/chat",  # Replace with your chatbot endpoint
            json={"message": "Hello"}
        )
    assert response.status_code == 200
    assert "response" in response.json()  # Validate chatbot reply structure
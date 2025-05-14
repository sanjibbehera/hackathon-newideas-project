import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from app.main import app

@pytest.fixture
def test_app():
    return app

@pytest.fixture
async def async_client(test_app: FastAPI):
    async with AsyncClient(app=test_app, base_url="http://testserver") as client:
        yield client
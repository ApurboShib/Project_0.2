import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """Test the root endpoint of the API."""
    response = client.get("/")
    assert response.status_code == 200

def test_health():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_documents():
    """Test the documents list endpoint."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_rules():
    """Test the rules list endpoint."""
    response = client.get("/api/rules")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

"""Basic API tests"""

import pytest
from fastapi.testclient import TestClient


def test_app_health(client: TestClient):
    """Test that the app is healthy"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_endpoint(client: TestClient):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_openapi_docs(client: TestClient):
    """Test that OpenAPI docs are available"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_api_routes_exist(client: TestClient):
    """Test that main API routes are defined"""
    # Test auth routes
    response = client.post("/auth/register", json={})
    assert response.status_code in [422, 400]  # Should fail due to missing data, not 404

    # Test meals routes
    response = client.post("/meals/log", json={})
    assert response.status_code in [401, 422, 403]  # Should fail due to auth or missing data, not 404 
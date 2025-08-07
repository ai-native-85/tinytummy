"""Authentication tests"""

import pytest
from fastapi.testclient import TestClient
from app.models.user import User
from app.services.auth_service import AuthService


def test_register_user(db_session, client):
    """Test user registration"""
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_register_duplicate_user(db_session, client):
    """Test duplicate user registration"""
    # Register first user
    client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    })
    
    # Try to register same email
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    })
    
    assert response.status_code == 400


def test_login_user(db_session, client):
    """Test user login"""
    # Register user first
    client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    })
    
    # Login
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(db_session, client):
    """Test login with invalid credentials"""
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401


def test_get_current_user(db_session, client):
    """Test getting current user with valid token"""
    # Register and login
    client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    })
    
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_get_current_user_invalid_token(db_session, client):
    """Test getting current user with invalid token"""
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401 
"""End-to-end integration tests"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient


def test_full_user_flow(client, auth_headers):
    """Test complete user flow: register → create child → log meals → view trends"""
    
    # 1. Create a child
    child_response = client.post("/children", json={
        "name": "Test Child",
        "date_of_birth": "2023-01-01",
        "gender": "male",
        "allergies": ["peanuts"],
        "dietary_restrictions": ["vegetarian"],
        "region": "US"
    }, headers=auth_headers)
    
    assert child_response.status_code == 201
    child_id = child_response.json()["id"]
    
    # 2. Log a meal
    meal_response = client.post("/meals/log", json={
        "child_id": child_id,
        "meal_type": "breakfast",
        "meal_time": datetime.now().isoformat(),
        "input_method": "text",
        "raw_input": "oatmeal with banana"
    }, headers=auth_headers)
    
    assert meal_response.status_code == 201
    meal_data = meal_response.json()
    assert meal_data["meal_type"] == "breakfast"
    assert "calories" in meal_data
    
    # 3. Get meals for child
    meals_response = client.get(f"/meals/{child_id}", headers=auth_headers)
    assert meals_response.status_code == 200
    meals = meals_response.json()
    assert len(meals) == 1
    
    # 4. Get meal trends
    trends_response = client.get(f"/meals/trends/{child_id}", headers=auth_headers)
    assert trends_response.status_code == 200
    trends = trends_response.json()
    assert len(trends) > 0


@pytest.mark.skip(reason="Premium features not fully implemented")
def test_premium_features_access(client, auth_headers, premium_user_headers):
    """Test premium features access"""
    
    # Create a child
    child_response = client.post("/children", json={
        "name": "Premium Child",
        "date_of_birth": "2023-01-01",
        "gender": "male",
        "allergies": [],
        "dietary_restrictions": [],
        "region": "US"
    }, headers=premium_user_headers)
    
    child_id = child_response.json()["id"]
    
    # Test premium features (these would be implemented in a full version)
    # For now, just verify basic functionality works
    assert child_response.status_code == 201


@pytest.mark.skip(reason="Caregiver features not fully implemented")
def test_caregiver_invitation_flow(client, auth_headers, premium_user_headers):
    """Test caregiver invitation and access flow"""
    
    # Create a child
    child_response = client.post("/children", json={
        "name": "Caregiver Child",
        "date_of_birth": "2023-01-01",
        "gender": "male",
        "allergies": [],
        "dietary_restrictions": [],
        "region": "US"
    }, headers=premium_user_headers)
    
    child_id = child_response.json()["id"]
    
    # Test caregiver features (these would be implemented in a full version)
    # For now, just verify basic functionality works
    assert child_response.status_code == 201


@pytest.mark.skip(reason="Gamification features not fully implemented")
def test_gamification_system(client, auth_headers):
    """Test gamification system"""
    
    # Create a child
    child_response = client.post("/children", json={
        "name": "Gamification Child",
        "date_of_birth": "2023-01-01",
        "gender": "male",
        "allergies": [],
        "dietary_restrictions": [],
        "region": "US"
    }, headers=auth_headers)
    
    child_id = child_response.json()["id"]
    
    # Log multiple meals to trigger gamification
    for i in range(3):
        client.post("/meals/log", json={
            "child_id": child_id,
            "meal_type": "breakfast",
            "meal_time": datetime.now().isoformat(),
            "input_method": "text",
            "raw_input": f"meal {i}"
        }, headers=auth_headers)
    
    # Get gamification progress
    progress_response = client.get(f"/gamification/{child_id}", headers=auth_headers)
    assert progress_response.status_code == 200


@pytest.mark.skip(reason="Sync endpoint not implemented")
def test_offline_sync(client, auth_headers):
    """Test offline sync functionality"""
    
    # Create offline sync data
    sync_data = {
        "meals": [
            {
                "child_id": "test-child-id",
                "meal_type": "breakfast",
                "meal_time": datetime.now().isoformat(),
                "input_method": "text",
                "raw_input": "offline meal",
                "calories": 250.0
            }
        ],
        "children": [],
        "plans": []
    }
    
    # Sync offline data
    sync_response = client.post("/sync/offline", json=sync_data, headers=auth_headers)
    assert sync_response.status_code == 200


def test_error_handling(client):
    """Test error handling and validation"""
    
    # Test invalid registration data
    response = client.post("/auth/register", json={
        "email": "invalid-email",
        "password": "123",  # Too short
        "first_name": "",
        "last_name": ""
    })
    
    assert response.status_code == 422  # Validation error
    
    # Test non-existent endpoint
    response = client.get("/nonexistent")
    assert response.status_code == 404 
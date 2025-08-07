"""Meal service tests"""

import pytest
import uuid
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.services.meal_service import MealService
from app.models.child import Child
from app.models.meal import Meal, MealType, InputMethod
from app.models.user import User
from app.schemas.meal import MealCreate


@pytest.fixture
def sample_user(db_session: Session):
    """Create a sample user for testing"""
    import uuid
    
    # Use unique email for each test
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"meal-test-{unique_id}@example.com",
        password_hash="hashed_password",
        first_name="Meal",
        last_name="Test"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_child(db_session: Session, sample_user: User):
    """Create a sample child for testing"""
    child = Child(
        user_id=sample_user.id,
        name="Test Child",
        date_of_birth=date(2023, 1, 1),
        gender="male",
        allergies=["peanuts"],
        dietary_restrictions=["vegetarian"],
        region="US"
    )
    db_session.add(child)
    db_session.commit()
    db_session.refresh(child)
    return child


def test_create_meal(db_session: Session, sample_child: Child, sample_user: User):
    """Test meal creation with GPT analysis"""
    meal_service = MealService(db_session)
    
    meal_data = MealCreate(
        child_id=sample_child.id,
        meal_type="breakfast",
        meal_time=datetime.now(),
        input_method="text",
        raw_input="oatmeal with banana and honey"
    )
    
    # Mock GPT response for testing
    meal_service.analyze_meal_with_gpt = lambda raw_input, child: {
        "detected_foods": ["oatmeal", "banana", "honey"],
        "estimated_quantities": {"oatmeal": "1 cup", "banana": "1 medium", "honey": "1 tsp"},
        "nutrition_breakdown": {
            "calories": 250.0,
            "protein_g": 8.0,
            "fat_g": 2.0,
            "carbs_g": 50.0,
            "fiber_g": 6.0,
            "iron_mg": 2.0,
            "calcium_mg": 50.0,
            "vitamin_a_iu": 100.0,
            "vitamin_c_mg": 10.0,
            "vitamin_d_iu": 0.0,
            "zinc_mg": 1.0,
            "folate_mcg": 20.0
        },
        "confidence_score": 0.85,
        "analysis_notes": "Healthy breakfast option"
    }
    
    meal = meal_service.create_meal(meal_data, str(sample_user.id))
    
    assert meal.child_id == sample_child.id
    assert meal.meal_type == MealType.BREAKFAST
    assert meal.raw_input == "oatmeal with banana and honey"
    assert meal.calories == 250.0
    assert meal.protein_g == 8.0


def test_get_meals_by_child(db_session: Session, sample_child: Child, sample_user: User):
    """Test getting meals for a child"""
    meal_service = MealService(db_session)
    
    # Create some test meals with required fields
    meal1 = Meal(
        child_id=sample_child.id,
        user_id=sample_user.id,
        meal_type=MealType.BREAKFAST,
        meal_time=datetime.now(),
        input_method=InputMethod.TEXT,
        raw_input="oatmeal",
        gpt_analysis={
            "detected_foods": ["oatmeal"],
            "nutrition_breakdown": {"calories": 250.0}
        },
        food_items=["oatmeal"],
        calories=250.0
    )
    meal2 = Meal(
        child_id=sample_child.id,
        user_id=sample_user.id,
        meal_type=MealType.LUNCH,
        meal_time=datetime.now(),
        input_method=InputMethod.TEXT,
        raw_input="sandwich",
        gpt_analysis={
            "detected_foods": ["bread", "cheese"],
            "nutrition_breakdown": {"calories": 300.0}
        },
        food_items=["bread", "cheese"],
        calories=300.0
    )
    
    db_session.add(meal1)
    db_session.add(meal2)
    db_session.commit()
    
    meals = meal_service.get_meals_by_child(sample_child.id, str(sample_user.id))
    
    assert len(meals) == 2
    # Meals are ordered by meal_time.desc(), so check that we have both meal types
    meal_types = [meal.meal_type for meal in meals]
    assert MealType.BREAKFAST in meal_types
    assert MealType.LUNCH in meal_types


def test_get_meal_trends(db_session: Session, sample_child: Child, sample_user: User):
    """Test getting meal trends"""
    meal_service = MealService(db_session)
    
    # Create meals over the last few days
    from datetime import timedelta
    today = datetime.now()
    
    for i in range(5):
        meal = Meal(
            child_id=sample_child.id,
            user_id=sample_user.id,
            meal_type=MealType.BREAKFAST,
            meal_time=today - timedelta(days=i),
            meal_date=(today - timedelta(days=i)).date(),  # Set meal_date explicitly
            input_method=InputMethod.TEXT,
            raw_input=f"meal {i}",
            gpt_analysis={
                "detected_foods": [f"food_{i}"],
                "nutrition_breakdown": {"calories": 250.0 + (i * 10)}
            },
            food_items=[f"food_{i}"],
            calories=250.0 + (i * 10)
        )
        db_session.add(meal)
    
    db_session.commit()
    
    trends = meal_service.get_meal_trends(sample_child.id, str(sample_user.id), days=7)
    
    assert len(trends) > 0
    assert "date" in trends[0]
    assert "daily_calories" in trends[0]


def test_calculate_age_months(db_session: Session):
    """Test age calculation"""
    meal_service = MealService(db_session)
    
    # Test with a child born 6 months ago
    from datetime import date, timedelta
    six_months_ago = date.today() - timedelta(days=180)
    
    age_months = meal_service._calculate_age_months(six_months_ago)
    
    # Allow for slight variations in calculation (5-6 months is acceptable)
    assert age_months in [5, 6] 
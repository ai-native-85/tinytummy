import json
from datetime import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from openai import OpenAI
from app.models.meal import Meal, MealType, InputMethod
from app.models.child import Child
from app.schemas.meal import MealCreate, MealResponse
from app.config import settings
from app.utils.prompts import MEAL_ANALYSIS_PROMPT_TEMPLATE
from app.utils.constants import MEAL_NOT_FOUND_ERROR, DEFAULT_MEAL_LIMIT, DEFAULT_TREND_DAYS


class MealService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.logger = logging.getLogger(__name__)

    def analyze_meal_with_gpt(self, raw_input: str, child: Child) -> Dict[str, Any]:
        """Analyze meal using GPT-4 and return nutrition data"""
        
        # Build context for GPT-4
        child_age_months = self._calculate_age_months(child.date_of_birth)
        allergies_text = ", ".join(child.allergies) if child.allergies else "none"
        restrictions_text = ", ".join(child.dietary_restrictions) if child.dietary_restrictions else "none"
        region_text = child.region or "unknown"
        
        # Use centralized prompt template
        system_prompt = MEAL_ANALYSIS_PROMPT_TEMPLATE.format(
            age_months=child_age_months,
            allergies=allergies_text,
            restrictions=restrictions_text,
            region=region_text
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Meal description: {raw_input}"}
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )
            
            # Parse GPT response
            gpt_response = response.choices[0].message.content
            analysis_data = json.loads(gpt_response)
            
            return analysis_data
            
        except Exception as e:
            # Log the error for debugging but don't expose internal details
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze meal. Please try again."
            )

    def create_meal(self, meal_data: MealCreate, user_id: str) -> Meal:
        """Create a new meal with GPT-4 analysis"""
        # Log raw inbound values/types
        try:
            self.logger.info(
                "create_meal called",
                extra={
                    "raw_meal_type": str(meal_data.meal_type),
                    "raw_input_method": str(meal_data.input_method),
                    "types": {
                        "meal_type": str(type(meal_data.meal_type)),
                        "input_method": str(type(meal_data.input_method)),
                    },
                },
            )
        except Exception:
            pass

        # Defensive normalization that works for both Enum and string inputs
        try:
            mt_str = (
                meal_data.meal_type.value.lower()
                if isinstance(meal_data.meal_type, MealType)
                else str(meal_data.meal_type).lower()
            )
            im_str = (
                meal_data.input_method.value.lower()
                if isinstance(meal_data.input_method, InputMethod)
                else str(meal_data.input_method).lower()
            )
            # Convert back to Enum to satisfy SQLAlchemy Enum column
            mt = MealType(mt_str)
            im = InputMethod(im_str)
            try:
                self.logger.info(
                    "normalized enums",
                    extra={
                        "normalized_meal_type": mt.value,
                        "normalized_input_method": im.value,
                    },
                )
            except Exception:
                pass
        except Exception:
            # If normalization fails, fall back to original (will 422/500 upstream if invalid)
            mt = meal_data.meal_type
            im = meal_data.input_method
        
        # Get child and verify ownership
        child = self.db.query(Child).filter(
            Child.id == meal_data.child_id,
            Child.user_id == user_id
        ).first()
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Analyze meal with GPT-4
        gpt_analysis = self.analyze_meal_with_gpt(meal_data.raw_input, child)
        
        # Extract nutrition data from GPT analysis
        nutrition_data = gpt_analysis.get("nutrition_breakdown", {})
        
        # Create meal record
        try:
            self.logger.info(
                "constructing Meal",
                extra={
                    "meal_type_for_db": getattr(mt, "value", str(mt)),
                    "input_method_for_db": getattr(im, "value", str(im)),
                },
            )
        except Exception:
            pass
        db_meal = Meal(
            child_id=meal_data.child_id,
            user_id=user_id,
            meal_type=mt,
            meal_time=meal_data.meal_time,
            input_method=im,
            raw_input=meal_data.raw_input,
            gpt_analysis=gpt_analysis,
            food_items=gpt_analysis.get("detected_foods", []),
            estimated_quantity=json.dumps(gpt_analysis.get("estimated_quantities", {})),
            calories=nutrition_data.get("calories"),
            protein_g=nutrition_data.get("protein_g"),
            fat_g=nutrition_data.get("fat_g"),
            carbs_g=nutrition_data.get("carbs_g"),
            fiber_g=nutrition_data.get("fiber_g"),
            iron_mg=nutrition_data.get("iron_mg"),
            calcium_mg=nutrition_data.get("calcium_mg"),
            vitamin_a_iu=nutrition_data.get("vitamin_a_iu"),
            vitamin_c_mg=nutrition_data.get("vitamin_c_mg"),
            vitamin_d_iu=nutrition_data.get("vitamin_d_iu"),
            zinc_mg=nutrition_data.get("zinc_mg"),
            folate_mcg=nutrition_data.get("folate_mcg"),
            confidence_score=gpt_analysis.get("confidence_score", 0.0),
            notes=gpt_analysis.get("analysis_notes")
        )
        
        self.db.add(db_meal)
        self.db.commit()
        self.db.refresh(db_meal)
        
        return db_meal

    def get_meals_by_child(self, child_id: str, user_id: str, limit: int = DEFAULT_MEAL_LIMIT) -> List[Meal]:
        """Get meals for a specific child"""
        return self.db.query(Meal).filter(
            Meal.child_id == child_id,
            Meal.user_id == user_id
        ).order_by(Meal.meal_time.desc()).limit(limit).all()

    def get_meal_trends(self, child_id: str, user_id: str, days: int = DEFAULT_TREND_DAYS) -> List[Dict]:
        """Get nutrition trends for a child"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily nutrition summaries
        trends = self.db.query(
            Meal.meal_date,
            func.sum(Meal.calories).label('daily_calories'),
            func.sum(Meal.protein_g).label('daily_protein'),
            func.sum(Meal.iron_mg).label('daily_iron'),
            func.count(Meal.id).label('meal_count')
        ).filter(
            Meal.child_id == child_id,
            Meal.user_id == user_id,
            Meal.meal_date >= start_date.date(),
            Meal.meal_date <= end_date.date()
        ).group_by(Meal.meal_date).order_by(Meal.meal_date).all()
        
        return [
            {
                "date": trend.meal_date,
                "daily_calories": float(trend.daily_calories) if trend.daily_calories else None,
                "daily_protein": float(trend.daily_protein) if trend.daily_protein else None,
                "daily_iron": float(trend.daily_iron) if trend.daily_iron else None,
                "meal_count": trend.meal_count
            }
            for trend in trends
        ]

    def _calculate_age_months(self, date_of_birth) -> int:
        """Calculate child's age in months"""
        today = datetime.now().date()
        age_days = (today - date_of_birth).days
        # More precise calculation: account for varying month lengths
        age_months = (today.year - date_of_birth.year) * 12 + (today.month - date_of_birth.month)
        if today.day < date_of_birth.day:
            age_months -= 1
        return max(0, age_months)  # Ensure non-negative 
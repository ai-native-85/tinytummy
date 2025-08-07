"""Plan service for meal plan generation and management"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from openai import OpenAI
from app.models.plan import Plan
from app.models.child import Child
from app.schemas.plan import PlanCreate, PlanResponse
from app.config import settings
from app.utils.prompts import MEAL_PLAN_GENERATION_PROMPT_TEMPLATE


class PlanService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def generate_meal_plan(self, child_id: str, user_id: str) -> Plan:
        """Generate a 21-day meal plan for a child using GPT-4"""
        
        # Get child and verify ownership
        child = self.db.query(Child).filter(
            Child.id == child_id,
            Child.user_id == user_id
        ).first()
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )
        
        # Calculate child's age
        child_age_months = self._calculate_age_months(child.date_of_birth)
        
        # Build context for GPT-4
        allergies_text = ", ".join(child.allergies) if child.allergies else "none"
        restrictions_text = ", ".join(child.dietary_restrictions) if child.dietary_restrictions else "none"
        region_text = child.region or "unknown"
        preferences_text = child.food_preferences or "none"
        
        # Use centralized prompt template
        system_prompt = MEAL_PLAN_GENERATION_PROMPT_TEMPLATE.format(
            age_months=child_age_months,
            allergies=allergies_text,
            restrictions=restrictions_text,
            region=region_text,
            preferences=preferences_text
        )

        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate a 21-day meal plan"}
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )
            
            # Parse GPT response
            gpt_response = response.choices[0].message.content
            plan_data = json.loads(gpt_response)
            
            # Create plan record
            plan = Plan(
                child_id=child_id,
                user_id=user_id,
                plan_data=plan_data,
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=20)).date(),
                status="active"
            )
            
            self.db.add(plan)
            self.db.commit()
            self.db.refresh(plan)
            
            return plan
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate meal plan. Please try again."
            )

    def get_active_plan(self, child_id: str, user_id: str) -> Optional[Plan]:
        """Get the active meal plan for a child"""
        return self.db.query(Plan).filter(
            Plan.child_id == child_id,
            Plan.user_id == user_id,
            Plan.status == "active"
        ).first()

    def get_plan_history(self, child_id: str, user_id: str) -> List[Plan]:
        """Get meal plan history for a child"""
        return self.db.query(Plan).filter(
            Plan.child_id == child_id,
            Plan.user_id == user_id
        ).order_by(Plan.created_at.desc()).all()

    def update_plan(self, plan_id: str, user_id: str, plan_data: Dict[str, Any]) -> Plan:
        """Update a meal plan"""
        plan = self.db.query(Plan).filter(
            Plan.id == plan_id,
            Plan.user_id == user_id
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        plan.plan_data = plan_data
        plan.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def _calculate_age_months(self, date_of_birth) -> int:
        """Calculate child's age in months"""
        today = datetime.now().date()
        age_months = (today.year - date_of_birth.year) * 12 + (today.month - date_of_birth.month)
        if today.day < date_of_birth.day:
            age_months -= 1
        return max(0, age_months) 
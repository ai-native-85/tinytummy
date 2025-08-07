"""Sync service for offline data synchronization"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.sync import OfflineSync
from app.models.meal import Meal
from app.models.child import Child
from app.models.plan import Plan
from app.schemas.sync import SyncRequest, SyncResponse


class SyncService:
    def __init__(self, db: Session):
        self.db = db

    def sync_offline_data(self, sync_data: SyncRequest, user_id: str) -> SyncResponse:
        """Sync offline data with server"""
        
        synced_count = 0
        total_count = 0
        
        # Sync meals
        if sync_data.meals:
            total_count += len(sync_data.meals)
            for meal_data in sync_data.meals:
                try:
                    # Check if meal already exists
                    existing_meal = self.db.query(Meal).filter(
                        Meal.id == meal_data.get("id"),
                        Meal.user_id == user_id
                    ).first()
                    
                    if not existing_meal:
                        # Create new meal
                        meal = Meal(
                            child_id=meal_data["child_id"],
                            user_id=user_id,
                            meal_type=meal_data["meal_type"],
                            meal_time=datetime.fromisoformat(meal_data["meal_time"]),
                            input_method=meal_data["input_method"],
                            raw_input=meal_data["raw_input"],
                            gpt_analysis=meal_data.get("gpt_analysis", {}),
                            food_items=meal_data.get("food_items", []),
                            estimated_quantity=meal_data.get("estimated_quantity", "{}"),
                            calories=meal_data.get("calories"),
                            protein_g=meal_data.get("protein_g"),
                            fat_g=meal_data.get("fat_g"),
                            carbs_g=meal_data.get("carbs_g"),
                            fiber_g=meal_data.get("fiber_g"),
                            iron_mg=meal_data.get("iron_mg"),
                            calcium_mg=meal_data.get("calcium_mg"),
                            vitamin_a_iu=meal_data.get("vitamin_a_iu"),
                            vitamin_c_mg=meal_data.get("vitamin_c_mg"),
                            vitamin_d_iu=meal_data.get("vitamin_d_iu"),
                            zinc_mg=meal_data.get("zinc_mg"),
                            folate_mcg=meal_data.get("folate_mcg")
                        )
                        self.db.add(meal)
                        synced_count += 1
                except Exception as e:
                    # Log error but continue with other items
                    continue
        
        # Sync children
        if sync_data.children:
            total_count += len(sync_data.children)
            for child_data in sync_data.children:
                try:
                    # Check if child already exists
                    existing_child = self.db.query(Child).filter(
                        Child.id == child_data.get("id"),
                        Child.user_id == user_id
                    ).first()
                    
                    if not existing_child:
                        # Create new child
                        child = Child(
                            user_id=user_id,
                            name=child_data["name"],
                            date_of_birth=datetime.fromisoformat(child_data["date_of_birth"]).date(),
                            gender=child_data["gender"],
                            allergies=child_data.get("allergies", []),
                            dietary_restrictions=child_data.get("dietary_restrictions", []),
                            region=child_data.get("region"),
                            food_preferences=child_data.get("food_preferences")
                        )
                        self.db.add(child)
                        synced_count += 1
                except Exception as e:
                    # Log error but continue with other items
                    continue
        
        # Sync plans
        if sync_data.plans:
            total_count += len(sync_data.plans)
            for plan_data in sync_data.plans:
                try:
                    # Check if plan already exists
                    existing_plan = self.db.query(Plan).filter(
                        Plan.id == plan_data.get("id"),
                        Plan.user_id == user_id
                    ).first()
                    
                    if not existing_plan:
                        # Create new plan
                        plan = Plan(
                            child_id=plan_data["child_id"],
                            user_id=user_id,
                            plan_data=plan_data.get("plan_data", {}),
                            start_date=datetime.fromisoformat(plan_data["start_date"]).date(),
                            end_date=datetime.fromisoformat(plan_data["end_date"]).date(),
                            status=plan_data.get("status", "active")
                        )
                        self.db.add(plan)
                        synced_count += 1
                except Exception as e:
                    # Log error but continue with other items
                    continue
        
        # Commit all changes
        self.db.commit()
        
        # Create sync record
        sync_record = OfflineSync(
            user_id=user_id,
            sync_type="offline_to_server",
            synced_count=synced_count,
            total_count=total_count,
            sync_data={
                "meals_count": len(sync_data.meals) if sync_data.meals else 0,
                "children_count": len(sync_data.children) if sync_data.children else 0,
                "plans_count": len(sync_data.plans) if sync_data.plans else 0
            }
        )
        self.db.add(sync_record)
        self.db.commit()
        
        return SyncResponse(
            synced_count=synced_count,
            total_count=total_count,
            success_rate=synced_count / total_count if total_count > 0 else 0
        )

    def get_server_data(self, user_id: str, last_sync_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get server data for client sync"""
        
        # Get meals since last sync
        meals_query = self.db.query(Meal).filter(Meal.user_id == user_id)
        if last_sync_time:
            meals_query = meals_query.filter(Meal.updated_at > last_sync_time)
        meals = meals_query.all()
        
        # Get children since last sync
        children_query = self.db.query(Child).filter(Child.user_id == user_id)
        if last_sync_time:
            children_query = children_query.filter(Child.updated_at > last_sync_time)
        children = children_query.all()
        
        # Get plans since last sync
        plans_query = self.db.query(Plan).filter(Plan.user_id == user_id)
        if last_sync_time:
            plans_query = plans_query.filter(Plan.updated_at > last_sync_time)
        plans = plans_query.all()
        
        return {
            "meals": [self._meal_to_dict(meal) for meal in meals],
            "children": [self._child_to_dict(child) for child in children],
            "plans": [self._plan_to_dict(plan) for plan in plans],
            "server_time": datetime.now().isoformat()
        }

    def _meal_to_dict(self, meal: Meal) -> Dict[str, Any]:
        """Convert meal to dictionary for sync"""
        return {
            "id": str(meal.id),
            "child_id": str(meal.child_id),
            "meal_type": meal.meal_type,
            "meal_time": meal.meal_time.isoformat(),
            "input_method": meal.input_method,
            "raw_input": meal.raw_input,
            "gpt_analysis": meal.gpt_analysis,
            "food_items": meal.food_items,
            "estimated_quantity": meal.estimated_quantity,
            "calories": meal.calories,
            "protein_g": meal.protein_g,
            "fat_g": meal.fat_g,
            "carbs_g": meal.carbs_g,
            "fiber_g": meal.fiber_g,
            "iron_mg": meal.iron_mg,
            "calcium_mg": meal.calcium_mg,
            "vitamin_a_iu": meal.vitamin_a_iu,
            "vitamin_c_mg": meal.vitamin_c_mg,
            "vitamin_d_iu": meal.vitamin_d_iu,
            "zinc_mg": meal.zinc_mg,
            "folate_mcg": meal.folate_mcg,
            "created_at": meal.created_at.isoformat(),
            "updated_at": meal.updated_at.isoformat()
        }

    def _child_to_dict(self, child: Child) -> Dict[str, Any]:
        """Convert child to dictionary for sync"""
        return {
            "id": str(child.id),
            "name": child.name,
            "date_of_birth": child.date_of_birth.isoformat(),
            "gender": child.gender,
            "allergies": child.allergies,
            "dietary_restrictions": child.dietary_restrictions,
            "region": child.region,
            "food_preferences": child.food_preferences,
            "created_at": child.created_at.isoformat(),
            "updated_at": child.updated_at.isoformat()
        }

    def _plan_to_dict(self, plan: Plan) -> Dict[str, Any]:
        """Convert plan to dictionary for sync"""
        return {
            "id": str(plan.id),
            "child_id": str(plan.child_id),
            "plan_data": plan.plan_data,
            "start_date": plan.start_date.isoformat(),
            "end_date": plan.end_date.isoformat(),
            "status": plan.status,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat()
        } 
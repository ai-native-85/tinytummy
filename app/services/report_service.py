"""Report service for generating nutrition reports"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.report import Report
from app.models.child import Child
from app.models.meal import Meal
from app.schemas.report import ReportCreate, ReportResponse


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_nutrition_report(self, child_id: str, user_id: str, report_type: str = "monthly") -> Report:
        """Generate a nutrition report for a child"""
        
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
        
        # Calculate date range
        end_date = datetime.now()
        if report_type == "weekly":
            start_date = end_date - timedelta(days=7)
        elif report_type == "monthly":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get meals for the period
        meals = self.db.query(Meal).filter(
            Meal.child_id == child_id,
            Meal.meal_time >= start_date,
            Meal.meal_time <= end_date
        ).all()
        
        # Calculate nutrition summary
        total_meals = len(meals)
        total_calories = sum(m.calories or 0 for m in meals)
        total_protein = sum(m.protein_g or 0 for m in meals)
        total_iron = sum(m.iron_mg or 0 for m in meals)
        total_calcium = sum(m.calcium_mg or 0 for m in meals)
        
        # Calculate averages
        avg_daily_calories = total_calories / ((end_date - start_date).days + 1)
        avg_daily_protein = total_protein / ((end_date - start_date).days + 1)
        avg_daily_iron = total_iron / ((end_date - start_date).days + 1)
        avg_daily_calcium = total_calcium / ((end_date - start_date).days + 1)
        
        # Generate report data
        report_data = {
            "report_type": report_type,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_meals": total_meals,
                "avg_daily_calories": round(avg_daily_calories, 1),
                "avg_daily_protein": round(avg_daily_protein, 1),
                "avg_daily_iron": round(avg_daily_iron, 1),
                "avg_daily_calcium": round(avg_daily_calcium, 1)
            },
            "nutrition_breakdown": {
                "calories": total_calories,
                "protein_g": total_protein,
                "iron_mg": total_iron,
                "calcium_mg": total_calcium
            },
            "insights": self._generate_insights(child, meals, report_data["summary"])
        }
        
        # Create report record
        report = Report(
            child_id=child_id,
            user_id=user_id,
            report_type=report_type,
            report_data=report_data,
            generated_at=datetime.now()
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        return report

    def get_report_history(self, child_id: str, user_id: str) -> List[Report]:
        """Get report history for a child"""
        return self.db.query(Report).filter(
            Report.child_id == child_id,
            Report.user_id == user_id
        ).order_by(Report.created_at.desc()).all()

    def get_report_by_id(self, report_id: str, user_id: str) -> Report:
        """Get a specific report by ID"""
        report = self.db.query(Report).filter(
            Report.id == report_id,
            Report.user_id == user_id
        ).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return report

    def _generate_insights(self, child: Child, meals: List[Meal], summary: Dict[str, Any]) -> List[str]:
        """Generate nutrition insights based on data"""
        insights = []
        
        # Age-appropriate insights
        child_age_months = self._calculate_age_months(child.date_of_birth)
        
        if child_age_months < 6:
            insights.append("Your baby is in the early stages of solid food introduction.")
        elif child_age_months < 12:
            insights.append("Your baby is developing important eating habits and preferences.")
        else:
            insights.append("Your toddler is building a foundation for lifelong healthy eating.")
        
        # Nutrition insights
        if summary["avg_daily_calories"] < 400:
            insights.append("Consider increasing calorie intake for healthy growth.")
        elif summary["avg_daily_calories"] > 800:
            insights.append("Calorie intake is good for your child's age and activity level.")
        
        if summary["avg_daily_iron"] < 7:
            insights.append("Iron intake may need attention - consider iron-rich foods.")
        
        if summary["total_meals"] < 3:
            insights.append("Try to offer 3-4 meals per day for consistent nutrition.")
        
        return insights

    def _calculate_age_months(self, date_of_birth) -> int:
        """Calculate child's age in months"""
        today = datetime.now().date()
        age_months = (today.year - date_of_birth.year) * 12 + (today.month - date_of_birth.month)
        if today.day < date_of_birth.day:
            age_months -= 1
        return max(0, age_months) 
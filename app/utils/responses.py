"""Standardized API response utilities"""

from typing import Dict, Any, Optional


def placeholder_response(feature: str) -> Dict[str, Any]:
    """Generate a standardized placeholder response for unimplemented features"""
    return {
        "message": f"{feature} endpoint",
        "status": "not_implemented",
        "feature": feature
    }


def success_response(message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a standardized success response"""
    response = {"message": message, "status": "success"}
    if data:
        response.update(data)
    return response


def error_response(message: str, status: str = "error") -> Dict[str, Any]:
    """Generate a standardized error response"""
    return {"message": message, "status": status}


def sync_response(synced_count: int, total_count: int) -> Dict[str, Any]:
    """Generate a standardized sync response"""
    return {
        "message": "Sync completed",
        "status": "success",
        "synced_count": synced_count,
        "total_count": total_count,
        "success_rate": synced_count / total_count if total_count > 0 else 0
    } 
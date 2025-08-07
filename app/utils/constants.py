"""Centralized constants and error messages"""

# Error Messages
PREMIUM_FEATURE_ERROR = "Premium feature. Upgrade to access {feature}."
CHILD_NOT_FOUND_ERROR = "Child not found"
USER_NOT_FOUND_ERROR = "User not found"
MEAL_NOT_FOUND_ERROR = "Meal not found"
INVALID_CREDENTIALS_ERROR = "Incorrect email or password"
EMAIL_ALREADY_REGISTERED_ERROR = "Email already registered"

# Subscription Limits
FREE_TIER_CHILD_LIMIT = 1
PREMIUM_TIER_CHILD_LIMIT = 10

# Default Values
DEFAULT_MEAL_LIMIT = 100
DEFAULT_TREND_DAYS = 30
DEFAULT_CONFIDENCE_SCORE = 0.0
DEFAULT_OPENAI_TEMPERATURE = 0.3
DEFAULT_OPENAI_MAX_TOKENS = 1000

# API Response Messages
SUCCESS_DELETE_MESSAGE = "Deleted successfully"
SUCCESS_SYNC_MESSAGE = "Sync completed successfully"

# Feature Names for Error Messages
FEATURE_MEAL_PLANS = "meal plan generation"
FEATURE_REPORTS = "report generation"
FEATURE_CHAT = "AI chat assistant"
FEATURE_CAREGIVER = "caregiver sharing"
FEATURE_MULTIPLE_CHILDREN = "multiple children" 
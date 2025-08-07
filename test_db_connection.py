#!/usr/bin/env python3
"""
Test database connection
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing Database Connection...")
    
    try:
        from app.database import get_db
        from app.models.user import User
        
        # Get database session
        db = next(get_db())
        
        # Test simple query
        print("📊 Testing database query...")
        user_count = db.query(User).count()
        print(f"✅ Database connection successful! Found {user_count} users")
        
        # Test specific user query
        test_user_id = "68251b05-9143-4c59-80d1-6d1a55885f67"
        user = db.query(User).filter(User.id == test_user_id).first()
        
        if user:
            print(f"✅ Test user found: {user.email}")
            print(f"   Subscription: {user.subscription_tier}")
        else:
            print(f"⚠️ Test user {test_user_id} not found")
            print("   This is expected if the user doesn't exist in the database")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test environment variables"""
    print("\n🔧 Testing Environment Variables...")
    
    required_vars = [
        'DATABASE_URL',
        'SUPABASE_URL', 
        'SUPABASE_KEY',
        'JWT_SECRET_KEY',
        'OPENAI_API_KEY',
        'QDRANT_URL',
        'QDRANT_API_KEY'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}..." if len(value) > 20 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not found")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("🚀 Starting Database Connection Tests...")
    
    # Test environment variables
    env_success = test_environment_variables()
    
    # Test database connection
    db_success = test_database_connection()
    
    print(f"\n📊 Test Results:")
    print(f"  Environment Variables: {'✅ PASS' if env_success else '❌ FAIL'}")
    print(f"  Database Connection: {'✅ PASS' if db_success else '❌ FAIL'}")
    
    if env_success and db_success:
        print("\n🎉 Database connection is working!")
    else:
        print("\n⚠️ Database connection issues detected.") 
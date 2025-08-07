#!/usr/bin/env python3
"""
Test server import without database
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_server_import():
    """Test if the server can import without database issues"""
    print("🧪 Testing Server Import...")
    
    try:
        # Test importing main modules
        print("📦 Testing imports...")
        
        # Test config import
        from app.config import settings
        print("✅ Config imported successfully")
        
        # Test database import (should not connect)
        from app.database import get_db
        print("✅ Database module imported successfully")
        
        # Test routes import
        from app.routes import chat_router
        print("✅ Routes imported successfully")
        
        # Test services import
        from app.services.rag_service import RAGService
        print("✅ RAG Service imported successfully")
        
        # Test models import
        from app.models.user import User
        from app.models.child import Child
        from app.models.chat import ChatSession, ChatMessage
        print("✅ Models imported successfully")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def test_main_import():
    """Test if main.py can be imported"""
    print("\n🚀 Testing Main Import...")
    
    try:
        # Test importing main
        import main
        print("✅ Main module imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Main import failed: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Import Tests...\n")
    
    # Test server imports
    server_success = test_server_import()
    
    # Test main import
    main_success = test_main_import()
    
    print("\n📊 Test Results:")
    print(f"  Server Imports: {'✅ PASS' if server_success else '❌ FAIL'}")
    print(f"  Main Import: {'✅ PASS' if main_success else '❌ FAIL'}")
    
    if server_success and main_success:
        print("\n🎉 All import tests passed! The server can be imported without issues.")
    else:
        print("\n⚠️ Some import tests failed. Please check the error messages above.") 
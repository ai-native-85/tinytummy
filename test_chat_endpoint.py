#!/usr/bin/env python3
"""
End-to-end test for chat endpoint with RAG integration using real Supabase user
"""

import requests
import json
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Real Supabase user details
REAL_USER_UUID = "68251b05-9143-4c59-80d1-6d1a55885f67"
REAL_USER_EMAIL = "test@example.com"

def generate_test_jwt_token():
    """Generate a test JWT token for the real user"""
    # Get JWT secret from environment
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret:
        print("❌ JWT_SECRET_KEY not found in environment")
        return None
    
    # Create payload for the test user
    payload = {
        "sub": REAL_USER_UUID,  # Subject (user ID)
        "email": REAL_USER_EMAIL,
        "exp": datetime.utcnow() + timedelta(hours=1),  # Expires in 1 hour
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    try:
        # Generate JWT token
        token = jwt.encode(payload, jwt_secret, algorithm="HS256")
        return token
    except Exception as e:
        print(f"❌ Error generating JWT token: {e}")
        return None

def test_chat_endpoint_with_real_user():
    """Test the chat endpoint with real Supabase user authentication"""
    print("🧪 Testing Chat Endpoint with Real Supabase User...")
    
    # Base URL (assuming local development server)
    base_url = "http://localhost:8000"
    
    # Test query
    test_query = "What should my 6-month-old eat?"
    
    # Prepare request data
    request_data = {
        "user_input": test_query,
        "child_id": None  # No specific child for this test
    }
    
    # Generate valid JWT token
    auth_token = generate_test_jwt_token()
    
    if not auth_token:
        print("❌ Could not generate valid JWT token")
        return False
    
    # Prepare headers with real user authentication
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    print(f"\n📝 Test Query: {test_query}")
    print(f"👤 Real User UUID: {REAL_USER_UUID}")
    print(f"📧 User Email: {REAL_USER_EMAIL}")
    print(f"🌐 Endpoint: {base_url}/chat/query")
    print(f"🔐 Auth Token: {auth_token[:20]}..." if auth_token else "❌ No auth token")
    
    try:
        # Make request to chat endpoint
        response = requests.post(
            f"{base_url}/chat/query",
            json=request_data,
            headers=headers
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat endpoint test successful!")
            print(f"\n🤖 AI Response: {result['response'][:300]}...")
            print(f"📋 Session ID: {result['session_id']}")
            
            # Check RAG metadata
            metadata = result.get('metadata', {})
            print(f"\n🔍 RAG Metadata:")
            print(f"  Confidence: {metadata.get('rag_confidence', 'unknown')}")
            print(f"  Sources: {metadata.get('rag_sources', [])}")
            print(f"  Context Count: {metadata.get('context_count', 0)}")
            
            return True
        elif response.status_code == 403:
            print("❌ Authentication failed - 403 Forbidden")
            print("This might be due to premium subscription check")
            print("Response:", response.text)
            return False
        elif response.status_code == 401:
            print("❌ Unauthorized - 401 Unauthorized")
            print("Response:", response.text)
            return False
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the FastAPI server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_rag_service_directly():
    """Test RAG service directly without HTTP"""
    print("\n🔍 Testing RAG Service Directly...")
    
    try:
        import sys
        sys.path.append('.')
        from app.services.rag_service import RAGService
        
        rag = RAGService()
        
        # Test query
        test_query = "What should my 6-month-old eat?"
        result = rag.generate_rag_response(test_query)
        
        print(f"✅ RAG Service Test Successful!")
        print(f"🤖 Response: {result['response'][:300]}...")
        print(f"📊 Confidence: {result['confidence']}")
        print(f"📚 Sources: {result['sources']}")
        print(f"🔢 Context Count: {len(result['context_used'])}")
        
        # Show context details
        if result['context_used']:
            print(f"\n📖 Context Used:")
            for i, context in enumerate(result['context_used'][:3], 1):
                print(f"  {i}. {context['title']} ({context['source']}) - Score: {context['score']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG Service Error: {e}")
        return False

def test_authentication_flow():
    """Test the authentication flow"""
    print("\n🔐 Testing Authentication Flow...")
    
    try:
        # Test without auth token
        response = requests.post(
            "http://localhost:8000/chat/query",
            json={"user_input": "test", "child_id": None},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 No Auth Response: {response.status_code}")
        if response.status_code == 401 or response.status_code == 403:
            print("✅ Authentication is properly enforced")
            return True
        else:
            print("❌ Authentication not properly enforced")
            return False
            
    except Exception as e:
        print(f"❌ Auth Test Error: {e}")
        return False

def test_jwt_token_generation():
    """Test JWT token generation"""
    print("\n🔑 Testing JWT Token Generation...")
    
    token = generate_test_jwt_token()
    if token:
        print("✅ JWT token generated successfully")
        print(f"Token preview: {token[:50]}...")
        
        # Decode token to verify
        try:
            jwt_secret = os.getenv('JWT_SECRET_KEY')
            decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            print(f"✅ Token decoded successfully")
            print(f"User ID: {decoded.get('sub')}")
            print(f"Email: {decoded.get('email')}")
            return True
        except Exception as e:
            print(f"❌ Token decode error: {e}")
            return False
    else:
        print("❌ JWT token generation failed")
        return False

if __name__ == "__main__":
    print("🚀 Starting Chat Endpoint Tests with Real Supabase User...")
    
    # Test JWT token generation first
    jwt_success = test_jwt_token_generation()
    
    # Test authentication flow
    auth_success = test_authentication_flow()
    
    # Test RAG service directly
    rag_success = test_rag_service_directly()
    
    # Test chat endpoint with real user
    chat_success = test_chat_endpoint_with_real_user()
    
    print(f"\n📊 Test Results:")
    print(f"  JWT Token Generation: {'✅ PASS' if jwt_success else '❌ FAIL'}")
    print(f"  Authentication Flow: {'✅ PASS' if auth_success else '❌ FAIL'}")
    print(f"  RAG Service: {'✅ PASS' if rag_success else '❌ FAIL'}")
    print(f"  Chat Endpoint: {'✅ PASS' if chat_success else '❌ FAIL'}")
    
    if jwt_success and auth_success and rag_success and chat_success:
        print("\n🎉 All tests passed! RAG integration is working with real authentication.")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
        
    print(f"\n📋 Summary:")
    print(f"  - Real User UUID: {REAL_USER_UUID}")
    print(f"  - User Email: {REAL_USER_EMAIL}")
    print(f"  - RAG Database: 26 vectors in Qdrant")
    print(f"  - Sources: US, WHO, UK, Canada, Singapore, India, Australia") 
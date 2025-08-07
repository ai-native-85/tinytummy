#!/usr/bin/env python3
"""
Test Chat Endpoint with Full RAG Integration
"""

import requests
import json
import os
import jwt
import time
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def generate_test_jwt_token():
    """Generate a test JWT token"""
    secret_key = os.getenv('JWT_SECRET_KEY')
    if not secret_key:
        print("❌ JWT_SECRET_KEY not found in environment")
        return None
    
    # Create a test payload
    payload = {
        'user_id': '68251b05-9143-4c59-80d1-6d1a55885f67',
        'email': 'test@example.com',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

def test_rag_service_directly():
    """Test RAG service directly without database"""
    print("🧠 Testing RAG Service Directly...")
    
    try:
        from app.services.rag_service import RAGService
        
        # Initialize RAG service
        rag_service = RAGService()
        print("✅ RAG Service initialized successfully")
        
        # Test service status
        status = rag_service.get_service_status()
        print(f"📊 Service Status: {status}")
        
        # Test RAG functionality
        test_query = "What should I feed my 9-month-old baby?"
        print(f"🔍 Testing query: {test_query}")
        
        result = rag_service.generate_rag_response(test_query)
        
        print("✅ RAG Response Generated Successfully!")
        print(f"📝 Response: {result.get('response', 'No response')}")
        print(f"🎯 Confidence: {result.get('confidence', 'Unknown')}")
        print(f"📚 Sources: {result.get('sources', [])}")
        print(f"🔗 Context Count: {len(result.get('context_used', []))}")
        
        return True, result
        
    except Exception as e:
        print(f"❌ RAG Service Test Failed: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False, None

def start_server_in_background():
    """Start the server in background"""
    print("🚀 Starting server in background...")
    
    try:
        # Start server process
        process = subprocess.Popen(
            ["python3", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        time.sleep(10)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start")
            print(f"📋 Stdout: {stdout}")
            print(f"📋 Stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        return None

def test_chat_endpoint_with_rag():
    """Test chat endpoint with RAG integration"""
    print("\n🧪 Testing Chat Endpoint with RAG...")
    
    # Generate JWT token
    token = generate_test_jwt_token()
    if not token:
        return False
    
    # Test data
    test_data = {
        "user_input": "What should I feed my 9-month-old baby?",
        "child_id": None
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Make request to chat endpoint
        response = requests.post(
            "http://localhost:8000/chat/query",
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ Chat endpoint responded successfully!")
            print(f"📝 AI Response: {response_data.get('response', 'No response')}")
            print(f"🎯 RAG Confidence: {response_data.get('metadata', {}).get('rag_confidence', 'Unknown')}")
            print(f"📚 RAG Sources: {response_data.get('metadata', {}).get('rag_sources', [])}")
            print(f"🔗 Context Count: {response_data.get('metadata', {}).get('context_count', 0)}")
            return True
        else:
            print(f"❌ Chat endpoint failed with status {response.status_code}")
            print(f"📋 Error Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to chat endpoint. Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error testing chat endpoint: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Chat Endpoint Test...\n")
    
    # Test RAG service directly first
    rag_success, rag_result = test_rag_service_directly()
    
    if not rag_success:
        print("❌ RAG service test failed. Cannot proceed with endpoint test.")
        return
    
    # Start server
    server_process = start_server_in_background()
    
    if server_process is None:
        print("❌ Server failed to start. Cannot test endpoint.")
        return
    
    try:
        # Test chat endpoint
        chat_success = test_chat_endpoint_with_rag()
        
        print("\n📊 Test Results:")
        print(f"  RAG Service: {'✅ PASS' if rag_success else '❌ FAIL'}")
        print(f"  Server Startup: {'✅ PASS' if server_process else '❌ FAIL'}")
        print(f"  Chat Endpoint: {'✅ PASS' if chat_success else '❌ FAIL'}")
        
        if rag_success and chat_success:
            print("\n🎉 All tests passed! The chat functionality is working correctly.")
            print("📋 Summary:")
            print(f"  - RAG Response: {rag_result.get('response', 'No response')[:100]}...")
            print(f"  - Confidence: {rag_result.get('confidence', 'Unknown')}")
            print(f"  - Sources: {rag_result.get('sources', [])}")
            print(f"  - Context Count: {len(rag_result.get('context_used', []))}")
        else:
            print("\n⚠️ Some tests failed. Please check the error messages above.")
            
    finally:
        # Clean up server process
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("👋 Server stopped.")

if __name__ == "__main__":
    main() 
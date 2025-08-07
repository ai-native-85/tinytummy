#!/usr/bin/env python3
"""
Test RAG functionality without database dependencies
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_rag_service():
    """Test RAG service directly"""
    print("🧠 Testing RAG Service...")
    
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
        
        return True
        
    except Exception as e:
        print(f"❌ RAG Service Test Failed: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def test_vector_service():
    """Test Vector service directly"""
    print("\n🔍 Testing Vector Service...")
    
    try:
        from app.services.vector_service import VectorService
        
        # Initialize vector service
        vector_service = VectorService()
        print("✅ Vector Service initialized successfully")
        
        # Test connection
        if vector_service.test_connection():
            print("✅ Vector database connection successful")
        else:
            print("❌ Vector database connection failed")
            return False
        
        # Test collection info
        info = vector_service.get_collection_info()
        print(f"📊 Collection Info: {info}")
        
        # Test search
        test_query = "baby feeding guidelines"
        results = vector_service.search_similar(test_query, limit=3)
        print(f"🔍 Search Results for '{test_query}':")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result.get('score', 'N/A')}")
            print(f"     Title: {result.get('payload', {}).get('title', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector Service Test Failed: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Starting RAG-Only Tests...\n")
    
    # Test vector service first
    vector_success = test_vector_service()
    
    # Test RAG service
    rag_success = test_rag_service()
    
    print("\n📊 Test Results:")
    print(f"  Vector Service: {'✅ PASS' if vector_success else '❌ FAIL'}")
    print(f"  RAG Service: {'✅ PASS' if rag_success else '❌ FAIL'}")
    
    if vector_success and rag_success:
        print("\n🎉 All RAG tests passed! The RAG functionality is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.") 
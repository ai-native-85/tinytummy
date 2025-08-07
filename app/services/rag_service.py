"""
RAG Service for TinyTummy
Retrieval-Augmented Generation service using Qdrant and OpenAI
"""

import os
import logging
from typing import List, Dict, Any, Optional
from .vector_service import VectorService
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class RAGService:
    """Service for Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.vector_service = VectorService()
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        
    def get_relevant_context(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get relevant context from vector database"""
        try:
            results = self.vector_service.search_similar(query, limit=limit)
            return results
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return []
    
    def format_context_for_prompt(self, context_results: List[Dict[str, Any]]) -> str:
        """Format context results into a prompt-friendly string"""
        if not context_results:
            return "No relevant nutrition guidelines found."
        
        formatted_context = "Based on authoritative nutrition guidelines:\n\n"
        
        for i, result in enumerate(context_results, 1):
            formatted_context += f"{i}. **{result['title']}** ({result['source']}, {result['region']})\n"
            formatted_context += f"   Age Group: {result['age_group']}\n"
            formatted_context += f"   Topic: {result['topic']}\n"
            formatted_context += f"   Content: {result['content'][:300]}...\n\n"
        
        return formatted_context
    
    def generate_rag_response(self, query: str, user_context: str = "") -> Dict[str, Any]:
        """Generate RAG response using retrieved context"""
        try:
            # Get relevant context
            context_results = self.get_relevant_context(query)
            
            if not context_results:
                return {
                    "response": "I don't have specific information about that topic in my nutrition guidelines database. Please consult with a healthcare provider for personalized advice.",
                    "context_used": [],
                    "confidence": "low"
                }
            
            # Format context for prompt
            context_text = self.format_context_for_prompt(context_results)
            
            # Create system prompt
            system_prompt = f"""You are TinyTummy, an AI nutrition assistant for parents and caregivers. You provide evidence-based advice from authoritative sources like WHO, CDC, NHS, and other health organizations.

When responding:
1. Base your answers on the provided nutrition guidelines
2. Be clear, supportive, and age-appropriate
3. Always recommend consulting healthcare providers for specific medical advice
4. Use simple language that parents can understand
5. Include relevant age groups and developmental stages

{context_text}

User Context: {user_context if user_context else "No additional context provided"}

Please respond to the user's question based on the authoritative guidelines provided above."""

            # Generate response
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Calculate confidence based on similarity scores
            avg_score = sum(result['score'] for result in context_results) / len(context_results)
            confidence = "high" if avg_score > 0.8 else "medium" if avg_score > 0.6 else "low"
            
            return {
                "response": response.choices[0].message.content,
                "context_used": context_results,
                "confidence": confidence,
                "sources": [result['source'] for result in context_results]
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return {
                "response": "I'm having trouble accessing the nutrition guidelines right now. Please try again later or consult with a healthcare provider.",
                "context_used": [],
                "confidence": "error"
            }
    
    def test_rag_functionality(self) -> Dict[str, Any]:
        """Test RAG functionality with a sample query"""
        test_query = "What are the feeding guidelines for 6-month-old babies?"
        
        try:
            result = self.generate_rag_response(test_query)
            return {
                "test_query": test_query,
                "response": result["response"],
                "confidence": result["confidence"],
                "sources": result["sources"],
                "context_count": len(result["context_used"])
            }
        except Exception as e:
            logger.error(f"Error testing RAG functionality: {e}")
            return {"error": str(e)}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of RAG service components"""
        try:
            vector_status = self.vector_service.test_connection()
            collection_info = self.vector_service.get_collection_info()
            
            return {
                "vector_service": "connected" if vector_status else "disconnected",
                "collection_info": collection_info,
                "openai_model": self.model,
                "status": "operational" if vector_status else "degraded"
            }
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"status": "error", "error": str(e)} 
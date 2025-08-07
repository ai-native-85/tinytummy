"""
Vector Service for TinyTummy RAG functionality
Handles vector operations using Qdrant
"""

import os
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector database operations using Qdrant"""
    
    def __init__(self):
        self.qdrant_client = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        self.collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'nutrition-guidelines')
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for given text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            raise
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors in Qdrant"""
        try:
            # Create embedding for query
            query_embedding = self.create_embedding(query)
            
            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "payload": result.payload,
                    "content": result.payload.get("content", ""),
                    "title": result.payload.get("title", ""),
                    "source": result.payload.get("source", ""),
                    "region": result.payload.get("region", ""),
                    "age_group": result.payload.get("age_group", ""),
                    "topic": result.payload.get("topic", "")
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []
    
    def upload_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """Upload vectors to Qdrant"""
        try:
            points = []
            for vector_data in vectors:
                point_id = hash(vector_data["id"]) % (2**63)  # Convert to positive integer
                points.append(PointStruct(
                    id=point_id,
                    vector=vector_data["values"],
                    payload=vector_data["metadata"]
                ))
            
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Uploaded {len(points)} vectors to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading vectors: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            return {
                "name": collection_info.name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test connection to Qdrant"""
        try:
            collections = self.qdrant_client.get_collections()
            logger.info(f"Successfully connected to Qdrant. Found {len(collections.collections)} collections")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {e}")
            return False 
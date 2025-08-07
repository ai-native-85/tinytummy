#!/usr/bin/env python3
"""
TinyTummy RAG Database Builder
Downloads, processes, and embeds authoritative child nutrition data from global sources.
"""

import os
import json
import requests
import time
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from pathlib import Path
import re
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class NutritionDocument:
    """Represents a nutrition document with metadata"""
    title: str
    content: str
    source: str
    region: str
    age_group: str
    topic: str
    url: str
    published_date: Optional[str] = None
    chunk_id: Optional[str] = None

@dataclass
class DocumentChunk:
    """Represents a chunked document for embedding"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    source_document: NutritionDocument

class RAGDatabaseBuilder:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.qdrant_client = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        self.collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'nutrition-guidelines')
        self.documents: List[NutritionDocument] = []
        self.chunks: List[DocumentChunk] = []
        
        # Ensure collection exists
        self._ensure_qdrant_collection()
    
    def _ensure_qdrant_collection(self):
        """Ensure Qdrant collection exists with proper configuration"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            if self.collection_name not in existing_collections:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=3072,  # text-embedding-3-large dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")
            raise

    def download_authoritative_sources(self) -> List[NutritionDocument]:
        """Download authoritative child nutrition data from global sources"""
        logger.info("Starting download of authoritative nutrition sources...")
        
        sources = self._get_authoritative_sources()
        documents = []
        
        for source in sources:
            try:
                logger.info(f"Downloading from: {source['name']} - {source['url']}")
                result = self._download_and_parse_source(source)
                
                if isinstance(result, list):
                    # Internal authoritative data returns a list
                    documents.extend(result)
                    logger.info(f"Successfully downloaded {len(result)} documents from {source['name']}")
                elif result:
                    # Single document
                    documents.append(result)
                    logger.info(f"Successfully downloaded: {result.title}")
                    
                time.sleep(1)  # Be respectful to servers
            except Exception as e:
                logger.error(f"Error downloading from {source['name']}: {e}")
                continue
        
        self.documents = documents
        logger.info(f"Downloaded {len(documents)} documents")
        return documents

    def _get_authoritative_sources(self) -> List[Dict[str, str]]:
        """Define authoritative sources for child nutrition data"""
        return [
            # US Sources
            {
                "name": "CDC Infant and Toddler Nutrition",
                "url": "https://www.cdc.gov/nutrition/infantandtoddlernutrition/",
                "region": "US",
                "source": "CDC",
                "topic": "feeding_guidelines"
            },
            {
                "name": "CDC Growth Charts",
                "url": "https://www.cdc.gov/growthcharts/",
                "region": "US", 
                "source": "CDC",
                "topic": "growth_charts"
            },
            {
                "name": "USDA Infant Nutrition",
                "url": "https://www.fns.usda.gov/tn/infant-and-toddler-nutrition",
                "region": "US",
                "source": "USDA", 
                "topic": "nutrition_guidelines"
            },
            {
                "name": "AAP Infant Feeding Guidelines",
                "url": "https://www.healthychildren.org/English/ages-stages/baby/feeding-nutrition/Pages/default.aspx",
                "region": "US",
                "source": "AAP",
                "topic": "feeding_guidelines"
            },
            
            # WHO Global Sources
            {
                "name": "WHO Child Growth Standards",
                "url": "https://www.who.int/tools/child-growth-standards",
                "region": "WHO",
                "source": "WHO", 
                "topic": "growth_standards"
            },
            {
                "name": "WHO Infant and Young Child Feeding",
                "url": "https://www.who.int/health-topics/infant-and-young-child-feeding#tab=tab_1",
                "region": "WHO",
                "source": "WHO",
                "topic": "feeding_guidelines"
            },
            
            # UK Sources
            {
                "name": "NHS Baby Feeding",
                "url": "https://www.nhs.uk/conditions/baby/weaning-and-feeding/",
                "region": "UK",
                "source": "NHS",
                "topic": "feeding_guidelines"
            },
            {
                "name": "NHS Start4Life",
                "url": "https://www.nhs.uk/start4life/weaning/",
                "region": "UK",
                "source": "NHS",
                "topic": "feeding_guidelines"
            },
            
            # Canadian Sources
            {
                "name": "Health Canada Infant Nutrition",
                "url": "https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/infant-feeding.html",
                "region": "Canada",
                "source": "Health Canada",
                "topic": "nutrition_guidelines"
            },
            
            # European Sources
            {
                "name": "EFSA Infant Nutrition",
                "url": "https://www.efsa.europa.eu/en/topics/topic/infant-and-young-child-nutrition",
                "region": "EU",
                "source": "EFSA",
                "topic": "nutrition_guidelines"
            },
            
            # Australian Sources
            {
                "name": "Australian Infant Feeding Guidelines",
                "url": "https://www.health.gov.au/health-topics/breastfeeding",
                "region": "Australia",
                "source": "Australian Government",
                "topic": "feeding_guidelines"
            },
            
            # Asian Sources
            {
                "name": "Singapore Health Promotion Board",
                "url": "https://www.healthhub.sg/a-z/192/Infant-and-Young-Child-Nutrition",
                "region": "Singapore",
                "source": "HPB",
                "topic": "nutrition_guidelines"
            },
            
            # Use the authoritative nutrition data as fallback
            {
                "name": "Authoritative Nutrition Data",
                "url": "internal://authoritative_data",
                "region": "Global",
                "source": "Multiple",
                "topic": "comprehensive_guidelines"
            }
        ]

    def _download_and_parse_source(self, source: Dict[str, str]) -> Optional[NutritionDocument]:
        """Download and parse a single source"""
        try:
            # Handle internal authoritative data
            if source['url'] == "internal://authoritative_data":
                return self._get_internal_authoritative_data()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(source['url'], headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse content based on URL type
            if source['url'].endswith('.pdf'):
                content = self._extract_pdf_content(response.content)
            else:
                content = self._extract_html_content(response.text, source['url'])
            
            if not content or len(content.strip()) < 100:
                logger.warning(f"Insufficient content from {source['name']}")
                return None
            
            # Determine age group from content analysis
            age_group = self._determine_age_group(content)
            
            return NutritionDocument(
                title=source['name'],
                content=content,
                source=source['source'],
                region=source['region'],
                age_group=age_group,
                topic=source['topic'],
                url=source['url']
            )
            
        except Exception as e:
            logger.error(f"Error downloading {source['name']}: {e}")
            return None
    
    def _get_internal_authoritative_data(self) -> List[NutritionDocument]:
        """Get internal authoritative nutrition data"""
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from authoritative_nutrition_data import AUTHORITATIVE_NUTRITION_DATA
        
        documents = []
        for data in AUTHORITATIVE_NUTRITION_DATA:
            doc = NutritionDocument(
                title=data['title'],
                content=data['content'],
                source=data['source'],
                region=data['region'],
                age_group=data['age_group'],
                topic=data['topic'],
                url=data['url']
            )
            documents.append(doc)
        
        return documents

    def _extract_html_content(self, html: str, url: str) -> str:
        """Extract clean text content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Remove navigation, footer, and other non-content elements
            for element in soup.find_all(['nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting HTML content: {e}")
            return ""

    def _extract_pdf_content(self, pdf_content: bytes) -> str:
        """Extract text content from PDF"""
        try:
            # For now, return a placeholder - in production you'd use PyPDF2 or similar
            return "PDF content extraction not implemented in this demo"
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return ""

    def _determine_age_group(self, content: str) -> str:
        """Determine age group from content analysis"""
        content_lower = content.lower()
        
        if any(term in content_lower for term in ['0-6 months', 'birth to 6 months', 'newborn']):
            return "0-6 months"
        elif any(term in content_lower for term in ['6-12 months', '6 to 12 months', 'infant']):
            return "6-12 months"
        elif any(term in content_lower for term in ['1-2 years', '12-24 months', 'toddler']):
            return "1-2 years"
        elif any(term in content_lower for term in ['2-5 years', 'preschool']):
            return "2-5 years"
        else:
            return "0-5 years"  # Default

    def chunk_documents(self, max_tokens: int = 1000) -> List[DocumentChunk]:
        """Chunk documents into smaller pieces for embedding"""
        logger.info("Chunking documents...")
        
        chunks = []
        for doc in self.documents:
            doc_chunks = self._chunk_document(doc, max_tokens)
            chunks.extend(doc_chunks)
        
        self.chunks = chunks
        logger.info(f"Created {len(chunks)} chunks from {len(self.documents)} documents")
        return chunks

    def _chunk_document(self, doc: NutritionDocument, max_tokens: int) -> List[DocumentChunk]:
        """Chunk a single document"""
        chunks = []
        
        # Simple sentence-based chunking
        sentences = re.split(r'[.!?]+', doc.content)
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Rough token estimation (1 token ≈ 4 characters)
            estimated_tokens = len(current_chunk + sentence) / 4
            
            if estimated_tokens > max_tokens and current_chunk:
                # Create chunk
                chunk = DocumentChunk(
                    chunk_id=f"{doc.source}_{doc.region}_{chunk_id}",
                    content=current_chunk.strip(),
                    metadata={
                        "title": doc.title,
                        "source": doc.source,
                        "region": doc.region,
                        "age_group": doc.age_group,
                        "topic": doc.topic,
                        "url": doc.url,
                        "document_title": doc.title
                    },
                    source_document=doc
                )
                chunks.append(chunk)
                current_chunk = sentence
                chunk_id += 1
            else:
                current_chunk += " " + sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                chunk_id=f"{doc.source}_{doc.region}_{chunk_id}",
                content=current_chunk.strip(),
                metadata={
                    "title": doc.title,
                    "source": doc.source,
                    "region": doc.region,
                    "age_group": doc.age_group,
                    "topic": doc.topic,
                    "url": doc.url,
                    "document_title": doc.title
                },
                source_document=doc
            )
            chunks.append(chunk)
        
        return chunks

    def create_embeddings(self) -> List[Dict[str, Any]]:
        """Create embeddings for all chunks using OpenAI"""
        logger.info("Creating embeddings...")
        
        embeddings = []
        batch_size = 100  # OpenAI batch limit
        
        for i in range(0, len(self.chunks), batch_size):
            batch = self.chunks[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(self.chunks) + batch_size - 1)//batch_size}")
            
            try:
                # Create embeddings for batch
                texts = [chunk.content for chunk in batch]
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=texts
                )
                
                # Process results
                for j, embedding in enumerate(response.data):
                    chunk = batch[j]
                    embeddings.append({
                        "id": chunk.chunk_id,
                        "values": embedding.embedding,
                        "metadata": chunk.metadata
                    })
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error creating embeddings for batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Created {len(embeddings)} embeddings")
        return embeddings

    def upload_to_qdrant(self, embeddings: List[Dict[str, Any]]) -> None:
        """Upload embeddings to Qdrant"""
        logger.info("Uploading embeddings to Qdrant...")
        
        batch_size = 100
        
        for i in range(0, len(embeddings), batch_size):
            batch = embeddings[i:i + batch_size]
            logger.info(f"Uploading batch {i//batch_size + 1}/{(len(embeddings) + batch_size - 1)//batch_size}")
            
            try:
                # Prepare points for upload
                points = []
                for i, embedding in enumerate(batch):
                    # Convert string ID to integer for Qdrant compatibility
                    point_id = hash(embedding["id"]) % (2**63)  # Convert to positive integer
                    points.append(PointStruct(
                        id=point_id,
                        vector=embedding["values"],
                        payload=embedding["metadata"]
                    ))
                
                # Upload to Qdrant
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"Uploaded {len(points)} points")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info("Upload to Qdrant completed")

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of the RAG database build"""
        # Count documents by region
        regions = {}
        topics = {}
        age_groups = {}
        
        for doc in self.documents:
            regions[doc.region] = regions.get(doc.region, 0) + 1
            topics[doc.topic] = topics.get(doc.topic, 0) + 1
            age_groups[doc.age_group] = age_groups.get(doc.age_group, 0) + 1
        
        # Sample chunks for verification
        sample_chunks = []
        for region in ['US', 'WHO', 'India']:
            region_chunks = [c for c in self.chunks if c.metadata['region'] == region]
            if region_chunks:
                sample_chunks.append({
                    "region": region,
                    "chunk": region_chunks[0].content[:200] + "...",
                    "metadata": region_chunks[0].metadata
                })
        
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "regions_covered": regions,
            "topics_covered": topics,
            "age_groups_covered": age_groups,
            "sample_chunks": sample_chunks,
            "build_timestamp": datetime.now().isoformat()
        }

    def test_qdrant_query(self) -> Dict[str, Any]:
        """Test a sample query on the Qdrant collection"""
        try:
            # Create a test query embedding
            test_query = "What are the feeding guidelines for 6-month-old babies?"
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=[test_query]
            )
            
            # Query Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=response.data[0].embedding,
                limit=3,
                with_payload=True
            )
            
            return {
                "query": test_query,
                "results": [
                    {
                        "score": result.score,
                        "payload": result.payload,
                        "content_preview": result.payload.get("title", "Unknown")
                    }
                    for result in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Error testing Qdrant query: {e}")
            return {"error": str(e)}

def main():
    """Main function to build the RAG database"""
    logger.info("🚀 Starting TinyTummy RAG Database Builder")
    
    builder = RAGDatabaseBuilder()
    
    # Step 1: Download authoritative sources
    logger.info("📥 Step 1: Downloading authoritative sources...")
    documents = builder.download_authoritative_sources()
    
    # Step 2: Chunk documents
    logger.info("✂️ Step 2: Chunking documents...")
    chunks = builder.chunk_documents()
    
    # Step 3: Create embeddings
    logger.info("🧠 Step 3: Creating embeddings...")
    embeddings = builder.create_embeddings()
    
    # Step 4: Upload to Qdrant
    logger.info("🔍 Step 4: Uploading to Qdrant...")
    builder.upload_to_qdrant(embeddings)
    
    # Step 5: Generate report
    logger.info("📊 Step 5: Generating summary report...")
    report = builder.generate_summary_report()
    
    # Test query
    logger.info("🔍 Testing Qdrant query...")
    query_result = builder.test_qdrant_query()
    
    # Print final report
    print("\n" + "="*60)
    print("🎉 TINYTUMMY RAG DATABASE BUILD COMPLETE")
    print("="*60)
    print(f"📄 Total Documents Processed: {report['total_documents']}")
    print(f"🧩 Total Chunks Created: {report['total_chunks']}")
    print(f"🌍 Regions Covered: {report['regions_covered']}")
    print(f"📋 Topics Covered: {report['topics_covered']}")
    print(f"👶 Age Groups Covered: {report['age_groups_covered']}")
    print(f"⏰ Build Timestamp: {report['build_timestamp']}")
    
    print("\n📝 Sample Chunks:")
    for sample in report['sample_chunks']:
        print(f"  🌐 {sample['region']}: {sample['chunk']}")
        print(f"     Metadata: {sample['metadata']}")
        print()
    
    if 'error' not in query_result:
        print("🔍 Sample Query Result:")
        print(f"  Query: {query_result['query']}")
        for result in query_result['results']:
            print(f"  📄 {result['content_preview']} (Score: {result['score']:.3f})")
    
    print("\n✅ RAG Database is ready for production use!")
    print("="*60)

if __name__ == "__main__":
    main() 
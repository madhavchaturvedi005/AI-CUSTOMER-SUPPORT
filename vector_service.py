"""Vector database service using Qdrant for RAG."""

import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from openai import AsyncOpenAI
import hashlib
import asyncio


class VectorService:
    """
    Manages vector embeddings and semantic search using Qdrant.
    
    Features:
    - Store document chunks with embeddings
    - Semantic search for relevant content
    - Automatic chunking and embedding generation
    - Support for multiple collections (businesses)
    """
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        collection_name: str = "knowledge_base"
    ):
        """
        Initialize Vector Service.
        
        Args:
            qdrant_url: Qdrant server URL (default: localhost:6333)
            qdrant_api_key: Qdrant API key (for cloud)
            openai_api_key: OpenAI API key for embeddings
            collection_name: Name of the Qdrant collection
        """
        # Qdrant client
        if qdrant_url:
            # Cloud or remote Qdrant
            self.client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
        else:
            # Local Qdrant (in-memory for development)
            self.client = QdrantClient(":memory:")
        
        self.collection_name = collection_name
        
        # OpenAI client for embeddings
        self.openai_client = AsyncOpenAI(
            api_key=openai_api_key or os.getenv('OPENAI_API_KEY')
        )
        
        # Embedding model
        self.embedding_model = "text-embedding-3-small"  # Cheaper and faster
        self.embedding_dimension = 1536
        
        # Chunking parameters
        self.chunk_size = 500  # characters per chunk
        self.chunk_overlap = 50  # overlap between chunks
        
        print(f"✅ Vector service initialized with collection: {collection_name}")
    
    async def initialize(self):
        """Initialize Qdrant collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Created Qdrant collection: {self.collection_name}")
            else:
                print(f"✅ Using existing collection: {self.collection_name}")
        except Exception as e:
            print(f"⚠️  Error initializing Qdrant: {e}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > self.chunk_size * 0.5:  # At least 50% of chunk
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        
        return [c for c in chunks if c]  # Remove empty chunks
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise
    
    async def add_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add document to vector database.
        
        Args:
            document_id: Unique document identifier
            text: Document text
            metadata: Optional metadata (filename, type, etc.)
            
        Returns:
            Number of chunks created
        """
        # Chunk the text
        chunks = self.chunk_text(text)
        print(f"📄 Split document into {len(chunks)} chunks")
        
        # Generate embeddings for all chunks
        points = []
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await self.generate_embedding(chunk)
            
            # Create point ID (hash of document_id + chunk_index)
            point_id = hashlib.md5(f"{document_id}_{i}".encode()).hexdigest()
            point_id_int = int(point_id[:8], 16)  # Convert to int for Qdrant
            
            # Create point
            point = PointStruct(
                id=point_id_int,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk,
                    "metadata": metadata or {}
                }
            )
            points.append(point)
        
        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        print(f"✅ Added {len(chunks)} chunks to vector database")
        return len(chunks)
    
    async def search(
        self,
        query: str,
        limit: int = 3,
        score_threshold: float = 0.3  # Lowered from 0.7 for better recall
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using semantic similarity.
        
        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of relevant chunks with scores
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)
        
        # Search Qdrant using query_points (correct API for v1.17+)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Format results
        chunks = []
        for result in response.points:
            chunks.append({
                "text": result.payload["text"],
                "score": result.score,
                "document_id": result.payload["document_id"],
                "chunk_index": result.payload["chunk_index"],
                "metadata": result.payload.get("metadata", {})
            })
        
        print(f"🔍 Found {len(chunks)} relevant chunks (scores: {[f'{c['score']:.2f}' for c in chunks]})")
        return chunks
    
    async def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Number of chunks deleted
        """
        # Search for all points with this document_id
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            ),
            limit=1000
        )
        
        point_ids = [point.id for point in results[0]]
        
        if point_ids:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )
            print(f"🗑️  Deleted {len(point_ids)} chunks for document {document_id}")
        
        return len(point_ids)
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all unique documents in the collection.
        
        Returns:
            List of documents with metadata including chunk counts
        """
        try:
            # Scroll through all points to get unique documents
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True
            )
            
            # Group by document_id to get unique documents and count chunks
            documents_map = {}
            chunk_counts = {}
            
            for point in results[0]:
                doc_id = point.payload.get("document_id")
                if doc_id:
                    # Count chunks per document
                    chunk_counts[doc_id] = chunk_counts.get(doc_id, 0) + 1
                    
                    # Store document info (only once per document)
                    if doc_id not in documents_map:
                        metadata = point.payload.get("metadata", {})
                        documents_map[doc_id] = {
                            "id": doc_id,
                            "filename": metadata.get("filename", doc_id),
                            "file_type": metadata.get("file_type", "unknown"),
                            "uploaded_at": metadata.get("uploaded_at"),
                            "size": metadata.get("size", 0)
                        }
            
            # Add chunk counts to documents
            for doc_id, doc_info in documents_map.items():
                doc_info["chunk_count"] = chunk_counts.get(doc_id, 0)
                doc_info["vector_count"] = chunk_counts.get(doc_id, 0)
            
            documents = list(documents_map.values())
            total_chunks = sum(chunk_counts.values())
            print(f"📚 Found {len(documents)} unique documents with {total_chunks} total chunks in Qdrant")
            return documents
            
        except Exception as e:
            print(f"⚠️  Error listing documents: {e}")
            return []
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            print(f"⚠️  Error getting collection info: {e}")
            return {}
    
    async def clear_collection(self):
        """Clear all vectors from collection."""
        try:
            self.client.delete_collection(self.collection_name)
            await self.initialize()
            print(f"🗑️  Cleared collection: {self.collection_name}")
        except Exception as e:
            print(f"⚠️  Error clearing collection: {e}")


# Global instance
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get or create global vector service instance."""
    global _vector_service
    
    if _vector_service is None:
        # Get configuration from environment
        qdrant_url = os.getenv('QDRANT_URL')  # e.g., "http://localhost:6333" or cloud URL
        qdrant_api_key = os.getenv('QDRANT_API_KEY')  # For Qdrant Cloud
        
        _vector_service = VectorService(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key
        )
    
    return _vector_service


async def initialize_vector_service():
    """Initialize the global vector service."""
    service = get_vector_service()
    await service.initialize()
    return service

from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_core.embeddings import Embeddings
from typing import List, Optional, Dict, Any
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.logger import create_scoped_logger

logger = create_scoped_logger("AsyncPineconeManager")

class AsyncPineconeManager:
    def __init__(self,
                 api_key: str,
                 index_name: str,
                 embeddings: Embeddings,
                 environment: str = "us-east-1-aws",
                 dimension: int = 1536,
                 metric: str = "cosine",
                 max_workers: int = 4):
        """
        Initialize Async Pinecone Manager

        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            embeddings: Embedding model (e.g., OpenAI embeddings)
            environment: Pinecone environment
            dimension: Vector dimension (depends on your embedding model)
            metric: Distance metric for similarity search
            max_workers: Maximum number of threads for async operations
        """
        self.api_key = api_key
        self.index_name = index_name
        self.embeddings = embeddings
        self.environment = environment
        self.dimension = dimension
        self.metric = metric

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        self.vector_store = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def create_index(self) -> bool:
        """Create Pinecone index if it doesn't exist"""
        def _create_index():
            try:
                # Check if index already exists
                existing_indexes = [index.name for index in self.pc.list_indexes()]

                if self.index_name not in existing_indexes:
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric=self.metric,
                        spec=ServerlessSpec(
                            cloud="aws",
                            region=self.environment
                        )
                    )
                    logger.info(f"Created Pinecone index: {self.index_name}")
                else:
                    logger.info(f"Index {self.index_name} already exists")

                return True
            except Exception as e:
                logger.error(f"Error creating index: {e}")
                return False

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _create_index)

    async def connect(self) -> bool:
        """Connect to Pinecone index and initialize vector store"""
        def _connect():
            try:
                # Get the index
                self.index = self.pc.Index(self.index_name)

                # Initialize the vector store
                self.vector_store = PineconeVectorStore(
                    index=self.index,
                    embedding=self.embeddings,
                    text_key="text"  # Key for storing text content
                )

                logger.info(f"Connected to Pinecone index: {self.index_name}")
                return True
            except Exception as e:
                logger.error(f"Error connecting to Pinecone: {e}")
                return False

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _connect)

    async def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None) -> List[str]:
        """
        Add documents to the vector store

        Args:
            texts: List of text documents to add
            metadatas: Optional metadata for each document
            ids: Optional custom IDs for documents

        Returns:
            List of document IDs
        """
        if not self.vector_store:
            raise Exception("Vector store not initialized. Call connect() first.")

        def _add_documents():
            try:
                document_ids = self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Added {len(texts)} documents to vector store")
                return document_ids
            except Exception as e:
                logger.error(f"Error adding documents: {e}")
                raise

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _add_documents)

    async def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict] = None) -> List[Dict]:
        """
        Perform similarity search

        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of similar documents with metadata
        """
        if not self.vector_store:
            raise Exception("Vector store not initialized. Call connect() first.")

        def _similarity_search():
            try:
                results = self.vector_store.similarity_search(
                    query=query,
                    k=k,
                    filter=filter
                )

                logger.info(f"Found {len(results)} similar documents")
                return [{"text": doc.page_content, "metadata": doc.metadata} for doc in results]
            except Exception as e:
                logger.error(f"Error performing similarity search: {e}")
                raise

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _similarity_search)

    async def similarity_search_with_score(self, query: str, k: int = 5, filter: Optional[Dict] = None) -> List[tuple]:
        """
        Perform similarity search with scores

        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of tuples (document, score)
        """
        if not self.vector_store:
            raise Exception("Vector store not initialized. Call connect() first.")

        def _similarity_search_with_score():
            try:
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k,
                    filter=filter
                )

                logger.info(f"Found {len(results)} similar documents with scores")
                return [
                    ({"text": doc.page_content, "metadata": doc.metadata}, score)
                    for doc, score in results
                ]
            except Exception as e:
                logger.error(f"Error performing similarity search with score: {e}")
                raise

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _similarity_search_with_score)

    async def delete_documents(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs

        Args:
            ids: List of document IDs to delete

        Returns:
            True if successful
        """
        if not self.index:
            raise Exception("Index not initialized. Call connect() first.")

        def _delete_documents():
            try:
                self.index.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents")
                return True
            except Exception as e:
                logger.error(f"Error deleting documents: {e}")
                return False

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _delete_documents)

    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.index:
            raise Exception("Index not initialized. Call connect() first.")

        def _get_index_stats():
            try:
                stats = self.index.describe_index_stats()
                logger.info("Retrieved index statistics")
                return stats
            except Exception as e:
                logger.error(f"Error getting index stats: {e}")
                raise

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _get_index_stats)

    async def delete_index(self) -> bool:
        """Delete the entire index"""
        def _delete_index():
            try:
                self.pc.delete_index(self.index_name)
                logger.info(f"Deleted index: {self.index_name}")
                return True
            except Exception as e:
                logger.error(f"Error deleting index: {e}")
                return False

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _delete_index)

    async def close(self):
        """Clean up resources"""
        self.index = None
        self.vector_store = None
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Async Pinecone manager closed")



class AsyncPineconeManagerFactory:
    @staticmethod
    def create_manager(
        embeddings: Embeddings,
        index_name: str,
        api_key: Optional[str] = None,
        max_workers: int = 4
        ) -> AsyncPineconeManager:
        """
        Factory method to create AsyncPineconeManager with environment variables
        """

        if not api_key:
            api_key = os.getenv("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("PINECONE_API_KEY environment variable not set")

        return AsyncPineconeManager(
            api_key=api_key,
            index_name=index_name,
            embeddings=embeddings,
            max_workers=max_workers
        )



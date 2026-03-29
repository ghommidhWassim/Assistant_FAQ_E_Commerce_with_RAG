"""
Vector Store implementation using ChromaDB.

Manages document storage, chunking, embedding, and semantic search.
"""

import logging
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain.schema import Document
from langchain_community.document_loaders import WebBaseLoader
import bs4

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
model = "llama3"
llm = ChatOllama(model=model)
embeddings_model = OllamaEmbeddings(model=model)
CHROMA_DB_PATH = Path("./chroma_db")


class VectorStore:
    """
    Vector store implementation using ChromaDB.
    
    Provides document storage, chunking, embedding, and semantic search functionality.
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        llm_model: str = "llama3",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize the ChromaDB vector store.

        Args:
            persist_directory: Path where ChromaDB will store data
            llm_model: Name of the LLM model for embeddings
            chunk_size: Size of document chunks in tokens
            chunk_overlap: Overlap between chunks
        """
        self.persist_directory = persist_directory
        self.llm_model = llm_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embeddings
        self.embeddings_model = OllamaEmbeddings(model=llm_model)
        
        # Initialize ChromaDB vector store
        self._setup_vector_store()
        
        logger.info(f"VectorStore initialized with model: {llm_model}")

    def _setup_vector_store(self) -> None:
        """
        Set up the ChromaDB vector store.
        
        Creates a persistent ChromaDB instance that auto-loads existing data
        if available or creates new collection.
        """
        try:
            # Create persist directory if needed
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize Chroma vector store
            self.vector_store = Chroma(
                collection_name="rag_documents",
                embedding_function=self.embeddings_model,
                persist_directory=self.persist_directory,
            )
            
            logger.info(f"ChromaDB initialized at {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Error setting up ChromaDB: {str(e)}")
            raise

    def load_documents(self, data_path: str) -> List[Document]:
        """
        Load documents from a directory.
        
        Supports PDF, JSON, and TXT files.

        Args:
            data_path: Path to directory containing documents

        Returns:
            List of loaded documents
        """
        documents = []
        data_path = Path(data_path)
        
        if not data_path.exists():
            logger.warning(f"Data path does not exist: {data_path}")
            return documents
        
        # Load PDF files
        for pdf_path in data_path.glob("*.pdf"):
            try:
                docs = self.load_document(pdf_path)
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} pages from {pdf_path.name}")
            except Exception as e:
                logger.error(f"Error loading {pdf_path}: {str(e)}")
        
        # Load JSON files (treat as text)
        for json_path in data_path.glob("*.json"):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    doc = Document(
                        page_content=content,
                        metadata={"source": json_path.name, "type": "json"}
                    )
                    documents.append(doc)
                    logger.info(f"Loaded JSON: {json_path.name}")
            except Exception as e:
                logger.error(f"Error loading {json_path}: {str(e)}")
        
        # Load TXT files
        for txt_path in data_path.glob("*.txt"):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    doc = Document(
                        page_content=content,
                        metadata={"source": txt_path.name, "type": "text"}
                    )
                    documents.append(doc)
                    logger.info(f"Loaded text: {txt_path.name}")
            except Exception as e:
                logger.error(f"Error loading {txt_path}: {str(e)}")
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents

    def add_documents(self, documents: List[Document]) -> List[Document]:
        """
        Add documents to the vector store with chunking.

        Args:
            documents: List of documents to add

        Returns:
            List of chunked documents that were added
        """
        if not documents:
            logger.warning("No documents to add")
            return []
        
        try:
            # Chunk documents
            chunked_docs = self.chunk_documents(documents)
            logger.info(f"Chunking created {len(chunked_docs)} chunks")
            
            # Add to ChromaDB with progress logging
            logger.info(f"⏳ Adding {len(chunked_docs)} chunks to vector store (this may take a few seconds)...")
            batch_size = 100
            total_batches = (len(chunked_docs) + batch_size - 1) // batch_size
            
            for i in range(0, len(chunked_docs), batch_size):
                batch = chunked_docs[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                logger.info(f"  📤 Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
                self.vector_store.add_documents(batch)
            
            logger.info(f"✅ Successfully added {len(chunked_docs)} chunks to vector store")
            
            return chunked_docs
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks using RecursiveCharacterTextSplitter.

        Args:
            documents: List of documents to chunk

        Returns:
            List of chunked documents
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunked = splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunked)} chunks")
        return chunked

    def load_document(self, file_path: Path) -> List[Document]:
        """
        Load a single PDF document.

        Args:
            file_path: Path to PDF file

        Returns:
            List of documents from the PDF
        """
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()
        
        # Add metadata
        for doc in docs:
            doc.metadata["source"] = file_path.name
        
        return docs if isinstance(docs, list) else [docs]

    def add_document(self, file_path: Path) -> List[Document]:
        """
        Load and add a single document to the vector store.

        Args:
            file_path: Path to document file

        Returns:
            List of documents that were added
        """
        docs = self.load_document(file_path)
        return self.add_documents(docs)

    def similarity_search(self, question: str, k: int = 5) -> List[Document]:
        """
        Search for documents similar to the question.

        Args:
            question: Query string
            k: Number of results to return

        Returns:
            List of most similar documents
        """
        try:
            results = self.vector_store.similarity_search(question, k=k)
            logger.info(f"Found {len(results)} similar documents for query")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []

    def as_retriever(self):
        """
        Get a retriever interface for the vector store.

        Returns:
            Retriever object compatible with LangChain
        """
        return self.vector_store.as_retriever(search_kwargs={"k": 5})

    def index_websites(self, urls: List[str]) -> List[Document]:
        """
        Index documents from websites.

        Args:
            urls: List of website URLs

        Returns:
            List of documents indexed from websites
        """
        docs = self.website_to_documents(urls)
        return self.add_documents(docs)

    def website_to_documents(self, urls: List[str]) -> List[Document]:
        """
        Load and parse web pages into documents.

        Args:
            urls: List of website URLs

        Returns:
            List of documents from websites
        """
        try:
            loader = WebBaseLoader(
                web_paths=urls,
                bs_kwargs=dict(
                    parse_only=bs4.SoupStrainer(
                        class_=("post-content", "post-title", "post-header")
                    )
                ),
            )
            docs = loader.load()
            logger.info(f"Loaded {len(docs)} documents from {len(urls)} URLs")
            return docs
        except Exception as e:
            logger.error(f"Error loading websites: {str(e)}")
            return []

    def delete_all(self) -> None:
        """
        Delete all documents from the vector store.
        """
        try:
            # Delete the collection by deleting all documents
            if hasattr(self.vector_store, 'delete_collection'):
                self.vector_store.delete_collection()
                logger.info("All documents deleted from vector store")
            else:
                logger.warning("Delete collection not supported")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the current collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self.vector_store._collection
            count = collection.count()
            return {
                "collection_name": collection.name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
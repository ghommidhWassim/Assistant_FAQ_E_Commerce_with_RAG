from pathlib import Path
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from typing import List, Dict, Tuple
from langchain.schema import Document
from vector_store import VectorStore
from langchain_core.output_parsers import StrOutputParser


class LLMRAGHandler:
    """
    A class to handle LLM-based RAG (Retrieval-Augmented Generation) tasks with enhanced prompting.
    
    Features:
    - Chain-of-thought reasoning for better accuracy
    - Source tracking and citation
    - Confidence scoring
    - French language support with professional tone
    
    Attributes:
        llm (ChatOllama): The language model used for generating responses.
        vector_store (VectorStore): The vector store used for document retrieval.
        system_prompt (str): The system prompt with careful instructions.
        history (List[BaseMessage]): The conversation history.
        rag_prompt (ChatPromptTemplate): The prompt template for q&a with RAG.
    
    Methods:
        __init__(self, model="llama3"): Initializes the LLMRAGHandler.
        generate_response(self, human_message) -> Dict: Generates response with sources and confidence.
        retrieve(self, question: str, k:int = 4) -> List[Document]: Retrieves relevant documents.
        add_pdf_to_context(self, filePath: Path): Adds a PDF file to the context.
    """
    
    def __init__(self, model="llama3"):
        """
        Initializes the LLMRAGHandler with the specified model.

        Args:
            model (str): The model to use. Default is "llama3".
        """
        self.llm = ChatOllama(model=model)
        self.vector_store = VectorStore(llm_model=model)
        
        # Advanced system prompt with chain-of-thought and guardrails
        self.system_prompt = """Tu es un assistant spécialisé en support client pour e-commerce. Tu dois répondre UNIQUEMENT en français.

IDENTITÉ ET RESPONSABILITÉS:
- Professionnel, concis et courtois
- Répondre STRICTEMENT à partir du contexte fourni
- Citer TOUJOURS les sources exactes de tes réponses
- Refuser poliment les questions en dehors du contexte des documents

INSTRUCTIONS STRICTES:
1. Si les documents contiennent une réponse complète: fournis cette réponse avec la source précise
2. Si les documents contiennent une réponse partielle: indique clairement ce qui est et n'est pas couvert
3. Si la question n'est pas couverte par les documents: refuse poliment et suggère une alternative ou du contexte en 1-2 lignes
4. Maximum 3-4 phrases par réponse (sauf si détail nécessaire)

TECHNIQUE DE RAISONNEMENT EXPLICITE:
- Énonce brièvement ce que tu cherches dans les documents (1 ligne max)
- Fournir la réponse avec sources

FORMAT DE RÉPONSE ATTENDU (respecte exactement ce format):
Réponse: [ta réponse ici]
Source(s): [docname.extension, section/ligne ou description précise]
Couverture: [complete/partial/not available]"""
        
        # Keep track of the conversation history
        self.history = []
        self.history.append(SystemMessage(content=self.system_prompt))

        # ChatPromptTemplate injects the system prompt on every chain call
        # This ensures the French instruction and guardrails are always enforced
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human",
             "Question utilisateur: {input}\n"
             "Contexte pertinent des documents:\n{context}\n"
             "Utilise le raisonnement en chaîne (chain-of-thought) et cite TOUJOURS tes sources.\n"
             "Réponse:")
        ])

        # Chain for querying the LLM and getting the answer
        self.llm_chain = self.rag_prompt | self.llm | StrOutputParser()

    
    def generate_response(self, human_message: str) -> Dict:
        """
        Generates a response from the LLM with source tracking and confidence.

        Args:
            human_message (str): The user's question.

        Returns:
            Dict: {
                'answer': str - the AI's response,
                'sources': List[str] - source documents cited,
                'confidence': str - 'high'/'medium'/'low',
                'coverage': str - 'complete'/'partial'/'not_available'
            }
        """
        try:
            print(f"[DEBUG] Processing question: {human_message}")
            
            # Retrieve relevant documents
            context_docs = self.retrieve(human_message, k=5)
            
            if not context_docs:
                return {
                    'answer': "Je n'ai pas trouvé d'informations pertinentes dans les documents. Pouvez-vous reformuler votre question ou consulter le support direct ?",
                    'sources': [],
                    'confidence': 'low',
                    'coverage': 'not_available'
                }
            
            # Format context with source metadata
            formatted_context = self._format_context_with_sources(context_docs)
            
            # Generate response via LLM
            response_text = self.llm_chain.invoke({
                "input": human_message,
                "context": formatted_context
            })
            
            # Parse response and extract sources
            answer, sources, coverage = self._parse_response(response_text, context_docs)
            
            # Calculate confidence based on coverage and document relevance
            confidence = self._calculate_confidence(coverage, context_docs)
            
            # Store in history
            self.history.append(HumanMessage(content=human_message))
            self.history.append(AIMessage(content=answer))
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'coverage': coverage
            }
            
        except Exception as e:
            print(f"[ERROR] in generate_response: {str(e)}")
            return {
                'answer': f"Erreur lors du traitement: {str(e)}",
                'sources': [],
                'confidence': 'low',
                'coverage': 'error'
            }

    def _format_context_with_sources(self, docs: List[Document]) -> str:
        """
        Formats retrieved documents with source information.
        
        Args:
            docs: List of retrieved documents
            
        Returns:
            Formatted string with sources
        """
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', '')
            page_info = f" (page {page})" if page else ""
            formatted.append(f"[Source {i}: {source}{page_info}]\n{doc.page_content}")
        return "\n\n".join(formatted)

    def _parse_response(self, response: str, retrieved_docs: List[Document]) -> Tuple[str, List[str], str]:
        """
        Parses LLM response to extract answer and determine coverage.

        Reads the structured 'Couverture:' line the LLM is instructed to write,
        with a keyword fallback for refusal phrases.

        Returns:
            Tuple of (answer, sources_list, coverage_level)
        """
        # Extract sources from retrieved documents
        sources = []
        for doc in retrieved_docs:
            source = doc.metadata.get('source', 'Unknown')
            if source not in sources:
                sources.append(source)

        # Parse the "Couverture:" line written by the LLM
        coverage = 'partial'
        lower = response.lower()

        if 'couverture: complete' in lower or 'couverture: complète' in lower:
            coverage = 'complete'
        elif 'couverture: not available' in lower or 'couverture: non disponible' in lower:
            coverage = 'not_available'
        elif 'couverture: partial' in lower or 'couverture: partielle' in lower:
            coverage = 'partial'
        # Fallback: detect refusal keywords in the answer body
        elif any(k in lower for k in [
            "je ne trouve pas", "pas d'information", "non disponible",
            "hors sujet", "ne concerne pas", "n'est pas couverte",
            "je ne peux pas répondre", "en dehors du contexte",
            "pas dans les documents", "aucune information"
        ]):
            coverage = 'not_available'

        return response, sources, coverage

    def _calculate_confidence(self, coverage: str, docs: List[Document]) -> str:
        """
        Calculates confidence level based on coverage and document count.
        
        Args:
            coverage: Coverage level from response parsing
            docs: Retrieved documents
            
        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        if coverage == 'not_available':
            return 'low'
        elif coverage == 'complete' and len(docs) >= 3:
            return 'high'
        elif coverage == 'partial' and len(docs) >= 2:
            return 'medium'
        else:
            return 'low'

    def reset(self) -> None:
        """
        Resets the conversation history.
        """
        self.history = []
        self.history.append(SystemMessage(content=self.system_prompt))

    def get_history(self) -> List[BaseMessage]:
        """
        Returns the conversation history.

        Returns:
            List[BaseMessage]: The conversation history.
        """       
        return self.history
    
    def retrieve(self, question: str, k: int = 5) -> List[Document]:
        """
        Retrieves the most relevant documents for a given question.

        Args:
            question (str): The question to retrieve documents for.
            k (int): The number of documents to retrieve. Default is 5.

        Returns:
            List[Document]: The retrieved documents.
        """
        try:
            retrieved_docs = self.vector_store.similarity_search(question, k=k)
            print(f"[DEBUG] Retrieved {len(retrieved_docs)} documents for question")
            return retrieved_docs
        except Exception as e:
            print(f"[ERROR] in retrieve: {str(e)}")
            return []

    def add_pdf_to_context(self, filePath: Path) -> List[Document]:
        """
        Adds a PDF file to the context for retrieval.

        Args:
            filePath (Path): The path to the PDF file.
        Returns:
            List[Document]: The documents added to the vector store.
        """
        self.vector_store.add_document(filePath)
    
if __name__ == '__main__':
    print(ChatOllama.list_models())
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from backend.service.agent import conv_chain, select_and_format_prompt
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env. Please set it.")

# Initialize embeddings and vector store
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    logger.info("Embeddings initialized successfully.")

    client = QdrantClient(url="http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "testing-huggingface")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )
    logger.info("Vector store initialized successfully.")

    # Test query
    query = "What documents can you help me with?"
    logger.info(f"Testing query: {query}")

    # Retrieve context
    context = vector_store.as_retriever().invoke(query)
    logger.info(f"Retrieved context: {context[:100]}...")

    # Prepare input for the chain
    input_dict = {
        "question": query,
        "chat_history": [],
        "use_rag": True,
        "context": (context, []),
    }
    formatted_input = select_and_format_prompt(input_dict)
    logger.info(f"Formatted prompt: {formatted_input['prompt'][:100]}...")

    # Invoke the chain to get the answer
    logger.info("Invoking the conversation chain...")
    result = conv_chain.invoke(query)

    logger.info(f"Chain result: {result}")
    print(f"Answer: {result}")

except Exception as e:
    logger.error(f"Error: {str(e)}")
    print(f"Error: {str(e)}")

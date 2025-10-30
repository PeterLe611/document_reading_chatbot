# Libraries imports
import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= Qdrant localhost client =================

# Create a Qdrant client to store vectors
client = QdrantClient(url="http://localhost:6333")

QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION")

# Create a vector store for embeddings
# client.recreate_collection(
#     collection_name=QDRANT_COLLECTION,
#     vectors_config={
#         "size": 3072,  # 1536 for OpenAI embeddings, 3072 for Google GenAI
#         "distance": "Cosine",
#     },
# )

# Check if collection exists, create only if it doesn't
# Recreate collection to ensure size matches embedding
if not client.collection_exists(collection_name=QDRANT_COLLECTION):
    logger.info(f"Creating collection {QDRANT_COLLECTION} with size 3072")
    client.recreate_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config={
            "size": 3072,  # Matches gemini-embedding-001
            "distance": "Cosine",
        },
    )
else:
    logger.info(f"Collection {QDRANT_COLLECTION} exists, verifying size")
    collection_info = client.get_collection(QDRANT_COLLECTION)
    if collection_info.config.params.vectors.size != 3072:
        logger.warning(
            f"Collection size {collection_info.config.params.vectors.size} does not match 3072. Recreating..."
        )
        client.recreate_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config={
                "size": 3072,
                "distance": "Cosine",
            },
        )
    else:
        logger.info(f"Collection {QDRANT_COLLECTION} size matches 3072")

google_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = QdrantVectorStore(
    client=client,
    collection_name=QDRANT_COLLECTION,
    # embedding=hf_embeddings,
    embedding=google_embeddings,
)

# # Test: Check number of points in collection
# points = client.scroll(collection_name=QDRANT_COLLECTION)
# print(f"Number of points in collection: {len(points[0])}")

# ================= Qdrant cloud client =================

# QDRANT_HOST = os.environ["QDRANT_HOST"]
# QDRANT_API = os.environ["QDRANT_API"]


# client = QdrantClient(
#     url=os.environ.get("QDRANT_HOST"),  # Use os.environ.get for safety
#     api_key=os.environ.get("QDRANT_API"),
# )


# # Create a collection
# QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION")

# client.recreate_collection(
#     collection_name=QDRANT_COLLECTION,
#     vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
# )  # Vectors mapping at size 384 for HuggingFace all-MiniLM-L6-v2 model, 1536 for OpenAI embeddings, 3072 for Google GenAI


# hf_embeddings = HuggingFaceEmbeddings(
#     model_name="all-MiniLM-L6-v2"
# )  # 384 dims, fast & good for MVP

# google_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# vector_store = QdrantVectorStore(
#     client=client,
#     collection_name=QDRANT_COLLECTION,
#     # embedding=hf_embeddings,
#     embedding=google_embeddings,
# )


# # Test: Check number of points in collection
# points = client.scroll(collection_name=QDRANT_COLLECTION)
# print(f"Number of points in collection: {len(points[0])}")

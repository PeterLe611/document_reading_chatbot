# from langchain import text_splitter
# from langchain.vectorstores import qdrant
# from langchain.embeddings import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from langchain_huggingface import HuggingFaceEmbeddings
import os

# https://8bbf5100-21d0-4beb-85e8-e100c56dbadc.eu-west-1-0.aws.cloud.qdrant.io # Cluster endpoints
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.caaq-EykmYTiwew-uRA0KUCgLFX9jlzVEAnxUBoH0Ws

os.environ["QDRANT_HOST"] = (
    "https://8bbf5100-21d0-4beb-85e8-e100c56dbadc.eu-west-1-0.aws.cloud.qdrant.io"
)
os.environ["QDRANT_API"] = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.caaq-EykmYTiwew-uRA0KUCgLFX9jlzVEAnxUBoH0Ws"
)

client = QdrantClient(os.getenv("QDRANT_HOST"), api_key=os.getenv("QDRANT_API"))

# Create a collection
os.environ["QDRANT_COLLECTION"] = "testing-huggingface"

client.recreate_collection(
    collection_name=os.getenv("QDRANT_COLLECTION"),
    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
)

# Open AI API Key: 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

# Google AI API Key: AIzaSyAjExKFiYnKzf5ZTwxuHZOG51Jm1tClUAA
# os.environ["OPENAI_API_KEY"] = (
#     "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"
# )

# embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)  # 384 dims, fast & good for MVP

vector_store = QdrantVectorStore(
    client=client,
    collection_name=os.environ["QDRANT_COLLECTION"],
    embedding=embeddings,
)

from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document  # Import Document class

texts = [
    "Sample doc 1 text: This document discusses the basics of AI chatbots. Your goal is to help the IT people find Docs",
    "Sample doc 2 text: This document covers vector databases like Qdrant.",
]
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

text_chunks = splitter.split_text("\n".join(texts))

# Convert text chunks to Document objects
documents = [Document(page_content=chunk) for chunk in text_chunks]

# Add the documents to vector store for context
vector_store.add_documents(documents)

points = client.scroll(collection_name=os.environ["QDRANT_COLLECTION"])
print(f"Number of points in collection: {len(points[0])}")

# # Debug: Check if documents are in the collection
# from qdrant_client import QdrantClient

# client = QdrantClient(
#     url="https://your-cluster-endpoint.qdrant.io", api_key="your_qdrant_api_key"
# )
# points = client.scroll(collection_name=os.environ["QDRANT_COLLECTION"])
# print(f"Number of points in collection: {len(points[0])}")

# ================= Local test llama3.2 model =================


def ollama_test():
    from langchain_ollama import OllamaLLM
    from langchain.chains import RetrievalQA

    # Set up the retrieval chain with Ollama LLM
    llm = OllamaLLM(model="llama3.2")  # Local LLM
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # Simple concatenation of retrieved docs
        retriever=vector_store.as_retriever(),
    )

    # Test the chain
    # query = "What is in sample doc 2?"
    query = "What does this system do?"  # For broader context
    response = qa_chain.invoke({"query": query})
    print(f"Query: {query}")
    print(f"Response: {response['result']}")

    from langchain.chains import ConversationalRetrievalChain
    from langchain.memory import ConversationBufferMemory

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, retriever=vector_store.as_retriever(), memory=memory
    )


# ================= OpenAIAPI LLM test =================

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# CALL IN GOOGLE GEMINI API KEY HERE:
# os.environ["GOOGLE_API_KEY"] = "your_api_key"

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # Simple concatenation of retrieved docs
    retriever=vector_store.as_retriever(),
)

messages = [
    SystemMessage(
        content="You are a helpful IT assistant. You can hold basic conversations such as greetings, or anything of sort. Always keep a professional attitude"
    ),  # System prompt
]

query = "What does this system do?"  # For broader context
response = qa_chain.invoke({"query": query})
print(f"Query: {query}")
print(f"Response: {response['result']}")

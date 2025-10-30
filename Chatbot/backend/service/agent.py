# Libraries imports
from functools import cache
import os
import langchain
from dotenv import load_dotenv
from operator import itemgetter
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from typing import Dict, List


# Repository imports
from backend.config.vectorstores import vector_store


# Get goole API key from environment variable
load_dotenv()

# Config setup for langchain verbosity
langchain.verbose = False
langchain.debug = False
langchain.llm_cache = False

# ================= Prompt Templates and condensed question prompts for Chatbot =================
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(
    """
Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}

Follow Up Input: {question}

Standalone question:"""
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an internal assistant for IMT Solutions.

Your task:
1. Based on the provided context, answer the user's question clearly and concisely.
2. If the question requires a guide, respond with a numbered step-by-step answer relevant to IMT's internal workflows.
3. If the question is simple, provide a short, direct response.

Language:
- Answer in Vietnamese if the question is in Vietnamese.
- Answer in English if the question is in English.

Answer the question based only on the following context:
<context>
{context}
</context>""",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{question}"),
    ]
)

FALLBACK_PROMPT = PromptTemplate.from_template(
    """
You are an internal assistant for IMT Solutions. Answer the following question as best you can:

Question: {question}

Please provide a helpful response based on general knowledge about workplace procedures and best practices.
"""
)

DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")


# ================= Chatbot  =================


# Retrieve the Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# def testing_sample_text():
# For testing purposes:
from langchain_text_splitters import CharacterTextSplitter  # Updated import

texts = [
    "Sample doc 1 text: This document discusses the basics of AI chatbots. Your goal is to help the IT people find Docs",
    "Sample doc 2 text: This document covers vector databases like Qdrant.",
]
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
text_chunks = splitter.split_text("\n".join(texts))
documents = [
    Document(page_content=chunk) for chunk in text_chunks
]  # Convert text chunks to Document objects

# Add the documents to vector store for context
vector_store.add_documents(documents)

# Initialize the Google Generative AI LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Testing RunnableSequence
from langchain_core.runnables import RunnablePassthrough, RunnableLambda


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


conv_chain = (
    {
        # Pluck "question", send to retriever, format, and assign to "context"
        "context": itemgetter("question") | vector_store.as_retriever() | format_docs,
        # Pluck "question" and pass it through to the "question" variable
        "question": itemgetter("question"),
        # Pluck "chat_history" and pass it through to the "chat_history" variable
        "chat_history": itemgetter("chat_history"),
    }
    | ANSWER_PROMPT  # <-- The prompt now receives all 3 required variables
    | llm
    | RunnableLambda(lambda x: x.content)
)


# Prompt selecting and formatting in the application
def select_and_format_prompt(input_dict: Dict) -> Dict:
    """Select appropriate prompt based on context relevance."""
    if input_dict.get("use_rag", False):
        context, references = input_dict["context"]
        prompt = ANSWER_PROMPT.format(
            context=context,
            chat_history=input_dict["chat_history"],
            question=input_dict["question"],
        )
    else:
        prompt = FALLBACK_PROMPT.format(question=input_dict["question"])
        references = ""

    return {
        "prompt": prompt,
        "reference": references,
        "question": input_dict["question"],
    }

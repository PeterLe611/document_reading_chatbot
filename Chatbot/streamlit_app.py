import asyncio
import streamlit as st
import datetime
import textwrap
import time
import logging
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from htbuilder import div, styles
import pandas as pd
from io import StringIO

# Repository imports
# from backend.config.test_prompts import vector_store, client, conv_chain
from backend.service.agent import conv_chain, select_and_format_prompt
from backend.config.vectorstores import vector_store
from backend.helpers.document_loader import DocLoader, UnstructuredDocLoader


# ================= Page Configuration and UI setup =================

# Set page title and icon
st.set_page_config(page_title="Help Desk Assistant")

# Initialize chat history, processsing files and first prompt in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_file" not in st.session_state:
    st.session_state.processed_files = set()
if "first_prompt" not in st.session_state:
    st.session_state.first_prompt = True

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

title_row = st.container(
    horizontal=True,
    vertical_alignment="bottom",
)

# chat_box = st.container(horizontal=True, vertical_alignment="bottom")

with title_row:
    st.title(
        # ":material/cognition_2: Streamlit AI assistant", anchor=False, width="stretch"
        "Streamlit AI assistant",
        anchor=False,
        width="stretch",
    )

# with chat_box:
#     if st.session_state.first_prompt:
#         prompt = st.chat_input("Ask me anything about documents")

# ================= File Uploading (TO database) and Attaching (For added context)=================


# File uploading function
file_upload = st.file_uploader(
    "Upload a file and save to the database", type=["pdf", "csv"]
)
if file_upload is not None:
    try:
        logger.info(f"Processing file: {file_upload.name}")
        loader = UnstructuredDocLoader()
        docs = asyncio.run(loader.convert_document(file_upload))
        logger.info(f"Generated {len(docs)} documents")
        vector_store.add_documents(docs)
        st.success(f"File {file_upload.name} ingested successfully!")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        st.error(f"Error processing file: {str(e)}")


# File attaching function


# ================= UI building, chat messages building =================

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything about documents"):
    # # Set the first_prompt variable as false
    # st.session_state.first_prompt = False

    # Save the chat messages into the history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Implement AI model
    with st.spinner("Thinking ..."):
        try:
            logger.info(f"Invoking chain with prompt: {prompt}")

            # 1. Format chat history for the chain's MessagesPlaceholder
            chat_history_messages = []
            for msg in st.session_state.messages[
                :-1
            ]:  # Get all messages *before* the new one
                if msg["role"] == "user":
                    chat_history_messages.append(HumanMessage(content=msg["content"]))
                else:
                    chat_history_messages.append(AIMessage(content=msg["content"]))

            # 2. Create the simple input dictionary
            chain_input = {"question": prompt, "chat_history": chat_history_messages}

            # 3. Invoke the chain. It will handle retrieval and prompting.
            response = conv_chain.invoke(chain_input)
        except Exception as e:
            logger.error(f"Error invoking chain: {str(e)}")
            response = f"Error: '{str(e)}'"
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Display assistant's messages
    with st.chat_message("assistant"):
        st.markdown(response)

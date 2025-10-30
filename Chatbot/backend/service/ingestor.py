# Libraries imports
from __future__ import annotations
import os
import asyncio  # For running sync code in async context
import base64
import uuid, time
from qdrant_client.http import models as rest
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import models
from fastapi import FastAPI, UploadFile, File, Body
from qdrant_client import models  # Ensure this is imported for PointStruct
from qdrant_client import AsyncQdrantClient

# from pypdf import PdfReader


# Repository imports
from backend.helpers.errors.raise_errors import raise_http_error
from backend.constants.http import *
from backend.config.vectorstores import vector_store, client
from backend.helpers.document_loader import DocLoader, UnstructuredDocLoader
import backend.schema.schema as schema


class Payload(models.BaseModel):
    content: dict


# Constants
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION")


# ================= Ingestor Service Class - Only use for ingesting new from the FE, and any files updating actions =================
class Ingestor:
    def __init__(self):
        self.EMBEDDING = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        # self.EMBEDDING = OpenAIEmbeddings()
        self._doc_loader = UnstructuredDocLoader()
        self._max_timstamp_value = 9_999_999_999_999_999

    def __custom_uuid(self):
        base_uuid = str(uuid.uuid4().hex)
        custom_id = str(self._max_timstamp_value - int(time.time() * 1_000_000))
        result_id = "0" + custom_id + base_uuid[(len(custom_id) + 1) :]
        return result_id

    async def add_chunks(self, chunks):
        try:
            ids = [self.__custom_uuid() for _ in range(len(chunks))]
            await vector_store.aadd_documents(
                [
                    Document(
                        page_content=chunk.text,
                        metadata={
                            "reference": chunk.reference,
                            "section": chunk.section,
                            "related_images": chunk.related_images,
                        },
                    )
                    for chunk in chunks
                ],
                ids=ids,
            )
            return ids
        except Exception as e:
            print(e)
            return None

    # Create point data (ID, vector, payload)
    async def ingest_file(self, file: UploadFile = File(...)):
        if not file.filename:
            raise_http_error(status_code=400, detail="No filename provided.")

        original_file_name = file.filename

        try:
            # 1. Use UnstructuredDocLoader to get LangChain Documents
            # Pass the UploadFile object directly (as your loader handles it)
            file_contents = await file.read()

            documents = await self._doc_loader.convert_document(
                file_contents
            )  # Pass the file-like object

            # 2. Chunk the documeunts and prepare for vector store
            points_to_upsert = []
            chunk_texts = [doc.page_content for doc in documents]

            # Embed all chunks at once (more efficient)
            chunk_vectors = await self.EMBEDDING.aembed_documents(chunk_texts)

            for i, doc in enumerate(documents):
                chunk_text = doc.page_content
                chunk_index = i

                # Create a consistent and unique ID for the Qdrant point
                # Using filename + chunk index is recommended for file management
                point_id = f"{original_file_name}_chunk_{chunk_index}"
                # Alternatively use your custom UUID if needed:
                # point_id = self.__custom_uuid()

                # Prepare the payload using the QdrantChunkPayload schema
                payload = schema.QdrantChunkPayload(
                    file_name=original_file_name,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    source_metadata=doc.metadata,  # Pass along metadata from the loader
                    # Add other fields like page_number if extracted by UnstructuredDocLoader
                )

                # Get the corresponding vector
                vector = chunk_vectors[i]  # Already a list from aembed_documents

                # Create the PointStruct
                points_to_upsert.append(
                    models.PointStruct(
                        id=point_id, vector=vector, payload=payload.model_dump()
                    )
                )

            # 3. Upsert points to Qdrant (use async version)
            if points_to_upsert:
                print(f"Upserting {len(points_to_upsert)} points to Qdrant...")

                # Use await client.a_upsert(...) if using AsyncQdrantClient
                await client.upsert(
                    collection_name=QDRANT_COLLECTION,  # Use your constant
                    points=points_to_upsert,
                    wait=True,  # Wait for operation to complete
                )

                print("Upsert finished.")
                # Return the generated point IDs
                return [p.id for p in points_to_upsert]
            else:
                print(f"No points generated for {original_file_name}.")
                return []

        except Exception as e:
            print(e)
            raise_http_error(
                status_code=500, detail="An error occurred during file ingestion."
            )

    async def ingest_links(
        self, file_links_request: schema.AddFilesRequest = Body(...)
    ):
        if not file_links_request.files:
            return []

        try:
            links_to_process = []
            for link_info in file_links_request.files:  # Process each link
                # 1. Prepare the payload data for each link
                link_payload = schema.FileMetadataPayload(
                    file_name=link_info.file_name,
                    link=link_info.link,
                )

                links_to_process.append(self._doc_loader.convert_link(link_payload))

            # 2. Process all links via UnstructuredDocLoader and add chunks (run sync convert in thread)
            print(f"Processing {len(links_to_process)} links concurrently...")
            conversion_result = await asyncio.gather(*links_to_process)

            # 3. Collect all documents from the conversion results
            all_documents = []
            for doc_list in conversion_result:
                for docs in doc_list.values():
                    all_documents.extend(docs)

            if not all_documents:
                print("No documents were generated from links.")
                raise_http_error(
                    status_code=500,
                    detail="No documents generated from provided links.",
                )

            # 4. Add all documents to the vector store
            print(f"Adding {len(all_documents)} documents to vector store...")
            await vector_store.aadd_documents(all_documents)

            print("Link ingestion finished.")
            return {"status": "success", "documents_added": len(all_documents)}

        except Exception as e:
            print(f"Error ingesting links: {e}")
            raise_http_error(
                status_code=500, detail="An error occurred during link ingestion."
            )

    async def update_chunk(self, doc_id: str, new_content: str):
        pass

    async def update_reference(self, id: str, text: str):
        pass

    async def update_related_images(self, id: str, images: list[str]):
        pass

    async def upload_image(self, image_b64: str, name: str):
        pass

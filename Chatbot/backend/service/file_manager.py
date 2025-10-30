# Libraries imports
from __future__ import annotations
import os
import os.path as osp
import base64
import uuid, time
import asyncio  # For running sync code in async context
from qdrant_client.http import models as rest
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import models


# Repository imports
from backend.constants.http import *
from backend.constants.env import QDRANT_COLLECTION
from backend.helpers.errors.raise_errors import raise_http_error
from backend.config.vectorstores import vector_store, client


# ================= File Manager Service Class - Only use for gettings files and deleting files from the vectorstore =================
class FileManager:

    async def get_document_ids(
        self, limit: int, offset: int, section: str | None = None
    ):
        pass

    async def get_image_ids(self, limit: int, offset: int):
        pass

    async def get_document(self, id: str):
        try:
            return dict(
                (
                    await client.retrieve(
                        collection_name=os.environ["QDRANT_COLLECTION"], ids=[id]
                    )
                )[0]
            )
        except Exception as e:
            print(e)
            return None

    async def get_documents_by_keyword(self, key: str, k: int = 5):
        try:
            result = await vector_store.asimilarity_search(query=key, k=k)
            serialized_documents = [
                {
                    "id": doc.metadata.get("_id", ""),
                    "payload": {
                        "page_content": doc.page_content,
                        "metadata": {
                            "reference": doc.metadata.get("reference", ""),
                            "related_images": doc.metadata.get("related_images", []),
                        },
                    },
                }
                for doc in result
            ]
            return serialized_documents
        except Exception as e:
            print(e)
            return None

    async def get_image(self, id: str):
        pass

    async def get_number_ingested_documents(self, section: str | None = None) -> int:
        pass

    async def get_number_ingested_images(self):
        return (
            await client.count(collection_name=os.environ["QDRANT_IMAGE_COLLECTION"])
        ).count

    async def delete_file_chunks(self, file_name: str):
        """Deletes all chunks associated with a specific file name."""
        print(f"Deleting chunks for file: {file_name}...")
        try:
            # Use await client.a_delete(...) if using AsyncQdrantClient
            delete_result = await asyncio.to_thread(
                client.delete,
                collection_name=QDRANT_COLLECTION,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_name",
                                match=models.MatchValue(value=file_name),
                            )
                        ]
                    )
                ),
                wait=True,
            )
            print(f"Deletion result for {file_name}: {delete_result.status}")
            return delete_result
        except Exception as e:
            print(f"Error deleting chunks for {file_name}: {e}")
            raise_http_error(
                status_code=500, detail=f"Failed to delete file chunks: {str(e)}"
            )

    async def delete_image(self, id: str):
        pass

    async def delete_related_images(self, id: str, images_to_remove: list[str]):
        pass

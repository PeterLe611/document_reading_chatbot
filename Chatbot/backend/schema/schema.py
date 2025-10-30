# Libraries imports
from __future__ import annotations
import enum
from typing import Annotated, Optional, List, Dict, Any
from fastapi import Body, File, Form, UploadFile
from pydantic import BaseModel, Field, HttpUrl


# Enums
class SectionEnum(str, enum.Enum):
    IT = "IT"
    HR = "HR"


# # BaseModel schemas
# class Chunk(BaseModel):
#     """Chunk of text"""

#     text: str = Body(..., description="Text of the chunk", example="Hello world")
#     reference: Optional[str] = Body(
#         None, description="Reference of the chunk", example="https://example.com"
#     )
#     section: Optional[SectionEnum] = Body(
#         None,
#         description="Team/department the chunk belongs to",
#         example="IT",
#     )
#     related_images: List[str] = Body(
#         [],
#         description="List of related images",
#         example=["https://example.com/image.jpg"],
#     )


class QdrantChunkPayload(BaseModel):
    """
    Pydantic model for the payload stored in Qdrant for each file chunk.
    This structure facilitates filtering and management based on the source file.
    """

    file_name: str = Field(..., description="The original name of the uploaded file.")
    chunk_index: int = Field(
        ...,
        ge=0,
        description="The sequential index (0, 1, 2...) of this chunk within the file.",
    )
    chunk_text: str = Field(..., description="The actual text content of this chunk.")
    page_number: Optional[int] = Field(
        None, description="Page number in the original PDF, if applicable."
    )
    source_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Any other metadata extracted by the loader."
    )


class FileMetadataPayload(BaseModel):
    """Payload for storing file metadata in Qdrant (without vectors)."""

    file_name: str = Field(..., description="The intended name of the file.")
    link: HttpUrl = Field(
        ..., description="URL pointing to the file content (PDF, Excel, etc.)."
    )


class AddFileRequest(BaseModel):
    """Request body for adding a single file metadata entry."""

    file_name: str
    link: HttpUrl
    link_name: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class AddFilesRequest(BaseModel):
    """Request body for adding multiple file metadata entries."""

    files: List[FileMetadataPayload]


class AddChunksResponse(BaseModel):
    """Add chunks to the index response"""

    status: str = Body(..., description="Status of the request", example="ok")

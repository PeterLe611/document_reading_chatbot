# Libraries imports
from fastapi import APIRouter
from typing import List


# Repository imports
from ..service.file_manager import FileManager
from ..helpers.errors.raise_errors import raise_http_error
from ..constants.http import *


router = APIRouter()


@router.get("/list-all-document-ids")
async def get_all_documents_ids():
    ids = FileManager.get_document_ids(limit=10, offset=10, section=None)
    return ids


@router.get("/{id}")
async def get_document_by_id(request: str):
    document = FileManager.get_document(request)
    if document is None:
        raise_http_error(
            status_code=HTTP_400_BAD_REQUEST,
            detail="No document found for your provided ID",
        )

    return document

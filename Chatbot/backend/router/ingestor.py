# Libraries imports
from fastapi import APIRouter, UploadFile, File, Body
from typing import List


# Repository imports
from ..service.ingestor import Ingestor
from ..helpers.errors.raise_errors import raise_http_error
from ..constants.http import *


router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/ingest-file")
async def ingest_file(file: UploadFile):
    ingestor_service = Ingestor()
    ids = await ingestor_service.ingest_file(file)
    if ids is None:
        raise_http_error(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest the provided file.",
        )
    return {"ingested_ids": ids}


@router.post("/ingest-links")
async def ingest_links(links: List[str] = Body(...)):
    ingestor_service = Ingestor()
    ids = await ingestor_service.ingest_links(links)
    if ids is None:
        raise_http_error(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest the provided links.",
        )
    return {"ingested_ids": ids}

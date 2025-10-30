# Libraries imports
from fastapi import APIRouter
from urllib import response
from typing import List


# Repository imports
from ..service.crawl_data import CrawlDataService


router = APIRouter()


MAX_LINKS = 10000


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/crawl-web-data")
async def crawl_web_data(request) -> List[str]:
    service = CrawlDataService()
    return service.crawl_all_file_links(
        request.username, request.password, max_links=MAX_LINKS
    )

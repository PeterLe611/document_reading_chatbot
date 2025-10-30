from fastapi import APIRouter
from .ingestor import router as ingestor_router

from .file_manager import router as file_manager_router
from .crawl_data import router as crawl_data_router

# Create the main router
main_router = APIRouter()

# Include all sub-routers with their prefixes
main_router.include_router(ingestor_router, prefix="/ingestor", tags=["ingestor"])

main_router.include_router(
    file_manager_router, prefix="/file-manager", tags=["file-manager"]
)

main_router.include_router(crawl_data_router, prefix="/crawl-data", tags=["crawl-data"])

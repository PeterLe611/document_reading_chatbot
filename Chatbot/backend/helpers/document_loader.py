# Libraries imports
import os
import re
import logging
import tempfile
import asyncio
from typing import List, Any
from unittest import result
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PipelineOptions,
    TesseractCliOcrOptions,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# Repository imports
from backend.constants.http import HTTP_500_INTERNAL_SERVER_ERROR
from backend.helpers.errors.raise_errors import raise_http_error


# Basic Docling usage
# source = "https://arxiv.org/pdf/2408.09869"  # file path or URL
# converter = DocumentConverter()
# doc = converter.convert(source).document

# print(doc.export_to_markdown())  # output: "### Docling Technical Report[...]"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ================ DOCLING DOCUMENT LOADER ================
class DocLoader:
    def __init__(self):
        self.converter = DocumentConverter()
        self._initialize_converter()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,  # Initialize text splitter, each chunk with 1000 characters and 200 overlap
        )

    def _initialize_converter(self):
        # PYTESSERACT OCR OPTIONS
        # ocr_options = TesseractCliOcrOptions(
        #     lang=["auto"]
        # )  # Uses PyTesseract for OCR with language auto-detection

        # pipeline_options = PdfPipelineOptions(
        #     do_ocr=True, force_full_page_ocr=True, ocr_options=ocr_options
        # )

        # DEFAULT RAPIDOCR FOR DOCLING
        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 1.0
        pipeline_options.do_ocr = True  # Enable OCR (uses RapidOCR by default)

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    # Convert general document to markdown format
    async def convert_document(self, file_input: Any) -> List[Document]:
        temp_file_path = None
        try:
            # Initialize Docling OCR processing before adding to vector database
            # Handle different input types

            # 1. Handle different I/O in a thread to avoid blocking
            def _write_temp_file():
                # Use a more robust suffix detection or pass filename
                suffix = ".pdf"  # Assuming PDF for now
                if hasattr(file_input, "name") and "." in file_input.name:
                    suffix = "." + file_input.name.split(".")[-1]

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix
                ) as temp_file:
                    temp_file.write(
                        file_input.read()
                    )  # Use .read() for file-like objects
                    logger.info(f"Temporary file created at: {temp_file.name}")
                    return temp_file.name

            temp_file_path = await asyncio.to_thread(_write_temp_file)

            # 2. Convert the document using Docling
            result = await asyncio.to_thread(
                self.converter.convert,
                temp_file_path,
            )
            doc = (
                result.document.export_to_markdown()
            )  # Extract the document from the result

            # TEST TO SEE IF THE TEXT IS BEING EXTRACTED PROPERLY
            logger.info(f"Extracted full_text length: {len(doc)} characters")
            if not doc:
                logger.warning("No text extracted from document pages.")

            clearned_text = self.process_text(
                doc
            )  # Clean and process the text if needed

            chunks = self.text_splitter.split_text(
                clearned_text
            )  # Split the text into chunks

            # Add metadata such as source and page count for added context
            source_name = getattr(file_input, "name", str(file_input))
            metadata = {"source": source_name}

            # Return the list of chunks as Document objects with metadata
            return [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

        except Exception as e:
            print(f"Error loading document: {e}")
            if temp_file_path:
                os.unlink(temp_file_path)  # Ensure cleanup on error
            raise_http_error(
                status=HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load document."
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                await asyncio.to_thread(
                    os.unlink, temp_file_path
                )  # Ensure cleanup in finally block
                logger.info(f"Temporary file {temp_file_path} deleted.")

    # Convert link (URL) to Document chunks
    async def convert_link(self, link: dict[str, str]) -> dict[str, Document]:
        try:
            # Initialize Docling OCR processing before adding to vector database
            # 1. Process the link to get the document and extract text
            source = link["link"]  # URL source to convert
            result = await asyncio.to_thread(self.converter.convert, source)
            doc = (
                result.document.export_to_markdown()
            )  # Extract the document from the result
            clearned_text = self.process_text(doc)
            chunks = self.text_splitter.split_text(
                clearned_text
            )  # Split the text into chunks
            # Add metadata such as source and page count for added context
            metadata = {"source": link["file_name"]}

            # 2. Return the list of chunks as Document objects with metadata
            return {
                link["link"]: [
                    Document(page_content=chunk, metadata=metadata) for chunk in chunks
                ]
            }

        except Exception as e:
            print(f"Error converting link: {e}")
            raise_http_error(
                status=HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to convert link."
            )

    # Process and clean text for better readability
    def process_text(self, text: str) -> str:
        lines = text.splitlines()
        non_empty_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if re.fullmatch(r"\d+", stripped):
                continue
            if re.fullmatch(r"(?i)page\s*\d+(\s*of\s*\d+)?", stripped):
                continue
            if i > 0 and lines[i - 1].strip() == stripped:  # Skip duplicates
                continue
            non_empty_lines.append(stripped)

        cleaned_text = "\n".join(non_empty_lines)
        cleaned_text = re.sub(r"\n+", "\n", cleaned_text).strip()
        return cleaned_text

    # Load and read files into QDRANT vector store
    def load_file(self, file_path: str):
        pass


# ================ UNSTRUCTURED DOCUMENT LOADER ================
# New imports needed for Unstructured
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element


class UnstructuredDocLoader:
    """
    A document loader class that uses the 'unstructured' library
    to load, process, and chunk documents from files and URLs.

    This class is designed as a drop-in replacement for the 'DocLoader'
    that used 'docling'.
    """

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,  # Initialize text splitter
        )
        logger.info("Initialized UnstructuredDocLoader")

    async def convert_document(self, file_input: Any) -> List[Document]:
        """
        Loads, partitions (with OCR), cleans, and chunks a document
        from a file-like object using 'unstructured'.
        """
        source_name = getattr(file_input, "name", "unknown_file")
        try:
            # 1. Partition the document using Unstructured
            # We run this in a thread as partition is a blocking I/O and CPU-bound (OCR) operation
            def _partition_file():
                # Ensure the file pointer is at the beginning
                file_input.seek(0)
                return partition(
                    file=file_input,
                    file_filename=source_name,
                    strategy="hi_res",  # Best strategy for PDFs, auto-handles OCR
                    # Docling used "auto". For Tesseract, you may need to be explicit, e.g., "eng+fra"
                    # Leaving it blank often defaults to "eng" or Tesseract's auto-detection.
                    ocr_languages="eng",
                )

            elements = await asyncio.to_thread(_partition_file)

            # 2. Convert unstructured elements to a single string
            # This replaces docling's `export_to_markdown()`
            full_text = "\n\n".join([str(el) for el in elements])

            logger.info(f"Extracted full_text length: {len(full_text)} characters")
            if not full_text:
                logger.warning("No text extracted from document pages.")

            # 3. Clean and process the text (using your existing method)
            cleaned_text = self.process_text(full_text)

            # 4. Split the text into chunks
            chunks = self.text_splitter.split_text(cleaned_text)

            # 5. Return the list of chunks as Document objects
            metadata = {"source": source_name}
            return [Document(page_content=chunk, metadata=metadata) for chunk in chunks]

        except Exception as e:
            print(f"Error loading document with Unstructured: {e}")
            # Re-raise your custom HTTP error
            raise_http_error(
                HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load document: {source_name}",
            )
        # No 'finally' block needed as we read the file object directly

    async def convert_link(self, link: dict[str, str]) -> dict[str, Document]:
        source_url = link["link"]
        file_name = link["file_name"]
        try:
            # 1. Process the link to get the document and extract text
            def _partition_url():
                return partition(
                    url=source_url,
                    strategy="hi_res",  # Use "hi_res" for web-hosted PDFs
                    ocr_languages="eng",
                )

            elements = await asyncio.to_thread(_partition_url)

            # 2. Convert elements to a single string
            full_text = "\n\n".join([str(el) for el in elements])

            # 3. Clean and process the text
            cleaned_text = self.process_text(full_text)

            # 4. Split the text into chunks
            chunks = self.text_splitter.split_text(cleaned_text)

            # 5. Return the dict of chunks as Document objects
            metadata = {"source": file_name}
            documents = [
                Document(page_content=chunk, metadata=metadata) for chunk in chunks
            ]

            return {source_url: documents}

        except Exception as e:
            print(f"Error converting link with Unstructured: {e}")
            raise_http_error(
                HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to convert link."
            )

    def process_text(self, text: str) -> str:
        lines = text.splitlines()
        non_empty_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if re.fullmatch(r"\d+", stripped):
                continue
            if re.fullmatch(r"(?i)page\s*\d+(\s*of\s*\d+)?", stripped):
                continue
            if i > 0 and lines[i - 1].strip() == stripped:  # Skip duplicates
                continue
            non_empty_lines.append(stripped)

        cleaned_text = "\n".join(non_empty_lines)
        cleaned_text = re.sub(r"\n+", "\n", cleaned_text).strip()
        return cleaned_text

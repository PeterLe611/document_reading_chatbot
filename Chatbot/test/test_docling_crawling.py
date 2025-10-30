# https://arxiv.org/pdf/2510.19788
from docling.document_converter import DocumentConverter, PdfFormatOption

# Basic Docling usage
source = "https://arxiv.org/pdf/2510.19788"  # file path or URL
converter = DocumentConverter()
doc = converter.convert(source).document

print(doc.export_to_markdown())

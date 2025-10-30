import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]
QDRANT_API = os.environ["QDRANT_API"]

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

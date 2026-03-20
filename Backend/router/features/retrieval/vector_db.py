import os
from dotenv import load_dotenv
import weaviate
from weaviate.auth import AuthApiKey
from fastapi import APIRouter
from db.database import db

load_dotenv()

upload = db["files"]
retrieval_router = APIRouter(tags=["retrieval"], prefix="/retrieval")

_client = None
COLLECTION_NAME = "DocumentChunk"


def get_client():
    global _client
    if _client is not None:
        return _client

    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    weaviate_url = os.getenv("WEAVIATE_URL")

    if not weaviate_api_key:
        raise RuntimeError("WEAVIATE_API_KEY not found")

    if not weaviate_url:
        raise RuntimeError("WEAVIATE_URL not found")

    if not weaviate_url.startswith("http"):
        weaviate_url = f"https://{weaviate_url}"

    _client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=AuthApiKey(weaviate_api_key),
    )
    return _client
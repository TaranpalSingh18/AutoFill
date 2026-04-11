import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import weaviate
from weaviate.auth import AuthApiKey
from fastapi import APIRouter
from db.database import db
from typing import Optional
from uuid import uuid5, NAMESPACE_DNS
from bson import ObjectId

from fastapi import HTTPException, Query
from pydantic import BaseModel
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter

from models.vectorised_file import SearchFileResponse


load_dotenv()

upload = db["files"]
retrieval_router = APIRouter(tags=["retrieval"])

_client = None
_embeddings = None
COLLECTION_NAME = "DocumentChunk"


def get_client():
    global _client
    if _client is not None:
        return _client

    weaviate_api_key = (os.getenv("WEAVIATE_API_KEY") or "").strip().strip('"').strip("'")
    weaviate_url = (os.getenv("WEAVIATE_URL") or "").strip().strip('"').strip("'")

    if not weaviate_api_key:
        raise RuntimeError("WEAVIATE_API_KEY not found")

    if not weaviate_url:
        raise RuntimeError("WEAVIATE_URL not found")

    if not weaviate_url.startswith("http"):
        weaviate_url = f"https://{weaviate_url}"

    cloud_error = None
    try:
        _client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=AuthApiKey(weaviate_api_key),
            skip_init_checks=True,
        )
    except Exception as e:
        cloud_error = e

    if _client is None:
        parsed = urlparse(weaviate_url)
        http_host = parsed.hostname or ""
        http_secure = parsed.scheme == "https"
        http_port = parsed.port or (443 if http_secure else 80)

        grpc_host = (os.getenv("WEAVIATE_GRPC_HOST") or "").strip().strip('"').strip("'") or http_host
        grpc_port_raw = (os.getenv("WEAVIATE_GRPC_PORT") or "").strip().strip('"').strip("'")
        grpc_port = int(grpc_port_raw) if grpc_port_raw.isdigit() else (443 if http_secure else 50051)

        try:
            _client = weaviate.connect_to_custom(
                http_host=http_host,
                http_port=http_port,
                http_secure=http_secure,
                grpc_host=grpc_host,
                grpc_port=grpc_port,
                grpc_secure=http_secure,
                auth_credentials=AuthApiKey(weaviate_api_key),
                skip_init_checks=True,
            )
        except Exception as custom_error:
            raise RuntimeError(
                "Failed to connect to Weaviate. Verify WEAVIATE_URL/WEAVIATE_API_KEY and gRPC reachability "
                f"(grpc host: {grpc_host}, port: {grpc_port}). Cloud error: {cloud_error}; Custom error: {custom_error}"
            ) from custom_error

    ensure_collection(_client)
    return _client


class IngestTextBody(BaseModel):
    file_id: str
    file_name: str
    text: str
    chunk_size: int = 900
    overlap: int = 120


class SearchBody(BaseModel):
    query: str
    file_id: Optional[str] = None
    limit: int = 5


def ensure_collection(client):
    if client.collections.exists(COLLECTION_NAME):
        return

    client.collections.create(
        name=COLLECTION_NAME,
        vectorizer_config=Configure.Vectorizer.none(),
        properties=[
            Property(name="file_id", data_type=DataType.TEXT),
            Property(name="file_name", data_type=DataType.TEXT),
            Property(name="chunk_id", data_type=DataType.INT),
            Property(name="text", data_type=DataType.TEXT),
            Property(name="category", data_type=DataType.TEXT),
            Property(name="sub_category", data_type=DataType.TEXT),
            Property(name="section_heading", data_type=DataType.TEXT),
        ],
    )


def _update_ingest_status(file_id: str, status: str, ingest_error: Optional[str] = None, chunk_count: Optional[int] = None):
    """Best-effort status update in Mongo for both legacy and current file identifiers."""
    update_fields = {
        "ingest_status": status,
        "ingest_error": ingest_error,
    }
    if chunk_count is not None:
        update_fields["chunk_count"] = chunk_count

    filters = [{"file_id": file_id}]
    if ObjectId.is_valid(file_id):
        filters.append({"_id": ObjectId(file_id)})

    upload.update_one({"$or": filters}, {"$set": update_fields})


def get_embeddings_model():
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError as e:
        raise RuntimeError(
            "langchain-community is missing. Install it with: pip install langchain-community"
        ) from e

    _embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        encode_kwargs={"normalize_embeddings": True},
    )
    return _embeddings


def embed_query(text: str) -> list[float]:
    model = get_embeddings_model()
    return model.embed_query(text)


def embed_documents(texts: list[str]) -> list[list[float]]:
    model = get_embeddings_model()
    return model.embed_documents(texts)


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120):
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError as e:
        raise RuntimeError("langchain is missing. Install it with: pip install langchain") from e

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    return splitter.split_text(text)


def ingest_semantic_chunks(file_id: str, file_name: str, chunks: list[dict]) -> dict:
    """Store semantic chunks in Weaviate with embeddings and metadata."""
    if not chunks:
        raise HTTPException(status_code=400, detail="No semantic chunks to ingest")

    texts = [str(item.get("text", "")).strip() for item in chunks]
    texts = [t for t in texts if t]
    if not texts:
        raise HTTPException(status_code=400, detail="Semantic chunks are empty")

    client = get_client()
    collection = client.collections.get(COLLECTION_NAME)

    collection.data.delete_many(where=Filter.by_property("file_id").equal(file_id))

    vectors = embed_documents(texts)

    text_index = 0
    for idx, chunk in enumerate(chunks):
        chunk_text_value = str(chunk.get("text", "")).strip()
        if not chunk_text_value:
            continue

        metadata = chunk.get("metadata") or {}
        doc_uuid = str(uuid5(NAMESPACE_DNS, f"{file_id}:{idx}"))
        collection.data.insert(
            uuid=doc_uuid,
            vector=vectors[text_index],
            properties={
                "file_id": file_id,
                "file_name": file_name,
                "chunk_id": int(chunk.get("chunk_id", idx)),
                "text": chunk_text_value,
                "category": str(metadata.get("category", "other")),
                "sub_category": str(metadata.get("sub_category", "general")),
                "section_heading": str(metadata.get("section_heading") or ""),
            },
        )
        text_index += 1

    _update_ingest_status(file_id=file_id, status="done", ingest_error=None, chunk_count=text_index)
    return {"file_id": file_id, "chunk_count": text_index}


def _search_chunks(q: str, file_id: Optional[str], limit: int) -> list[SearchFileResponse]:
    client = get_client()
    collection = client.collections.get(COLLECTION_NAME)

    where_filter = None
    if file_id:
        where_filter = Filter.by_property("file_id").equal(file_id)

    query_vector = embed_query(q)
    result = collection.query.near_vector(
        near_vector=query_vector,
        filters=where_filter,
        limit=limit,
        return_metadata=["distance"],
    )

    response_items = []
    for obj in result.objects:
        props = obj.properties
        score = None
        if obj.metadata is not None:
            distance = getattr(obj.metadata, "distance", None)
            if distance is not None:
                score = max(0.0, 1 - float(distance))

        response_items.append(
            SearchFileResponse(
                file_id=props.get("file_id", ""),
                file_name=props.get("file_name", ""),
                chunk_id=props.get("chunk_id", 0),
                text=props.get("text", ""),
                score=score,
            )
        )

    return response_items


@retrieval_router.post("/internal/embeddings/store")
@retrieval_router.post("/retrieval/ingest-text")
def ingest_text(body: IngestTextBody):
    try:
        _update_ingest_status(file_id=body.file_id, status="processing", ingest_error=None)

        chunks = chunk_text(
            body.text,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
        )
        if not chunks:
            raise HTTPException(status_code=400, detail="No text to ingest")

        semantic_chunks = [
            {
                "chunk_id": idx,
                "text": chunk,
                "metadata": {
                    "category": "other",
                    "sub_category": "general",
                    "section_heading": "",
                },
            }
            for idx, chunk in enumerate(chunks)
        ]

        return ingest_semantic_chunks(
            file_id=body.file_id,
            file_name=body.file_name,
            chunks=semantic_chunks,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _update_ingest_status(file_id=body.file_id, status="failed", ingest_error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@retrieval_router.get("/retrieval/search", response_model=list[SearchFileResponse])
def search(
    q: str = Query(..., min_length=2),
    file_id: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
):
    try:
        return _search_chunks(q=q, file_id=file_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@retrieval_router.post("/api/search")
def search_pipeline(body: SearchBody):
    if len(body.query.strip()) < 2:
        raise HTTPException(status_code=400, detail="query must be at least 2 characters")
    if body.limit < 1 or body.limit > 20:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 20")

    try:
        items = _search_chunks(q=body.query, file_id=body.file_id, limit=body.limit)
        return {"results": [item.model_dump() for item in items]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
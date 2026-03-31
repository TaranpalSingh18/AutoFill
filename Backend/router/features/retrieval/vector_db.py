import os
from dotenv import load_dotenv
import weaviate
from weaviate.auth import AuthApiKey
from fastapi import APIRouter
from db.database import db
from typing import Optional
from uuid import uuid5, NAMESPACE_DNS

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

    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    weaviate_url = os.getenv("WEAVIATE_URL")

    if not weaviate_api_key:
        raise RuntimeError("WEAVIATE_API_KEY not found")

    if not weaviate_url:
        raise RuntimeError("WEAVIATE_URL not found")

    if not weaviate_url.startswith("http"):
        weaviate_url = f"https://{weaviate_url}"

    try:
        _client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=AuthApiKey(weaviate_api_key),
            skip_init_checks=True,
        )
    except Exception as e:
        raise RuntimeError(
            "Failed to connect to Weaviate. Check WEAVIATE_URL format and ensure your cluster has gRPC enabled/reachable."
        ) from e

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
        ],
    )


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
        client = get_client()
        collection = client.collections.get(COLLECTION_NAME)

        upload.update_one(
            {"file_id": body.file_id},
            {"$set": {"ingest_status": "processing", "ingest_error": None}},
        )

        chunks = chunk_text(
            body.text,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
        )
        if not chunks:
            raise HTTPException(status_code=400, detail="No text to ingest")

        collection.data.delete_many(
            where=Filter.by_property("file_id").equal(body.file_id)
        )

        chunk_vectors = embed_documents(chunks)

        for idx, chunk in enumerate(chunks):
            doc_uuid = str(uuid5(NAMESPACE_DNS, f"{body.file_id}:{idx}"))
            collection.data.insert(
                uuid=doc_uuid,
                vector=chunk_vectors[idx],
                properties={
                    "file_id": body.file_id,
                    "file_name": body.file_name,
                    "chunk_id": idx,
                    "text": chunk,
                },
            )

        upload.update_one(
            {"file_id": body.file_id},
            {
                "$set": {
                    "ingest_status": "done",
                    "chunk_count": len(chunks),
                    "ingest_error": None,
                }
            },
        )

        return {"file_id": body.file_id, "chunk_count": len(chunks)}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        upload.update_one(
            {"file_id": body.file_id},
            {"$set": {"ingest_status": "failed", "ingest_error": str(e)}},
        )
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
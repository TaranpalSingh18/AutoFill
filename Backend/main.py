from fastapi import FastAPI, UploadFile, File
from router.auth.main import auth_router
from db.database import ping_mongo, close_mongo
from router.features.upload.main import upload_router
from router.features.retrieval.vector_db import retrieval_router

app = FastAPI()


app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(retrieval_router)


@app.on_event("startup")
async def start_mongo():
    print("starting mongo")
    ping_mongo()

@app.on_event("shutdown")
async def shut_mongo():
    close_mongo()

@app.get('/health')
def get_health():
    return {"message":"hello"}






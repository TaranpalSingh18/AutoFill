from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from router.auth.main import auth_router
from router.features.upload.main import upload_router
from db.database import ping_mongo, close_mongo

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(upload_router)


@app.on_event("startup")
async def start_mongo():
    print("starting mongo")
    try:
        ping_mongo()
    except Exception as e:
        print(f"Mongo startup failed: {type(e).__name__}: {e}")
        print("Check MONGO_URI credentials, Atlas IP allowlist, and local network/VPN/firewall.")
        raise

@app.on_event("shutdown")
async def shut_mongo():
    close_mongo()

@app.get('/health')
def get_health():
    return {"message":"hello"}






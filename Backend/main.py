from fastapi import FastAPI, UploadFile, File
from router.auth.main import auth_router
from db.database import ping_mongo, close_mongo

app = FastAPI()


app.include_router(auth_router)


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

@app.post("/upload")
async def upload_the_file(file: UploadFile = File(...)):
    ## here ... means that the file is required

    file_op = await file.read()

    return {
        "filename": file.filename,
        "content_type" : file.content_type,
        "length": len(file_op)
    }







from fastapi import FastAPI, UploadFile, File

app = FastAPI()

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







from fastapi import APIRouter, HTTPException
import json
from models.auth import Signup, Login
from db.database import db
from passlib.context import CryptContext



auth_router = APIRouter(prefix="/auth")
users = db["users"]
hashed_password_context = CryptContext(schemes=['bcrypt'], deprecated="auto")


def get_hash_password(password: str)->str:
    return hashed_password_context.hash(password)

def verify_password(password: str, hashed_passwordd: str)->bool:
    return hashed_password_context.verify(password, hashed_passwordd)

@auth_router.get('/')
async def get_auth_health():
    return {"message": "hello from auth"}

@auth_router.post('/signup')
async def signup(payload: Signup):
    existing_user = users.find_one({"email":payload.email})
    hashed_password=get_hash_password(payload.password)

    if existing_user:
        raise HTTPException(status_code=400, detail="User Email Already exists")
    
    users.insert_one(
        {
            "name": payload.name,
            "email": payload.email,
            "password": hashed_password
        }
    )

    return {"messsage": f"User Created with email: {payload.email}"}


@auth_router.post('/login')
async def login(payload: Login):

    existing_user = users.find_one({'email': payload.email})
    
    if not existing_user:
        raise HTTPException(status_code=400, detail=f"The email: {payload.email} does not match. Sign up kro")
    
    original_pass = existing_user["password"]
    payload_password = payload.password

    if not verify_password(payload_password, original_pass):
        raise HTTPException(status_code=400, detail="Invalid password")

    return {"message": "Login Successful"}




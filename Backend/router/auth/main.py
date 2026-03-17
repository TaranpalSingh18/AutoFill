from fastapi import APIRouter, HTTPException
import json
from models.auth import Signup, Login
from db.database import db


auth_router = APIRouter(prefix="/auth")
users = db["users"]

@auth_router.get('/')
async def get_auth_health():
    return {"message": "hello from auth"}

@auth_router.post('/signup')
async def signup(payload: Signup):
    existing_user = users.find_one({"email":payload.email})

    if existing_user:
        raise HTTPException(status_code=400, detail="User Email Already exists")
    
    users.insert_one(
        {
            "name": payload.name,
            "email": payload.email,
            "password": payload.password
        }
    )

    return {"messsage": f"User Created with email: {payload.email}"}


@auth_router.post('/login')
async def login(payload: Login):

    existing_user = users.find_one({'email': payload.email})
    
    if not existing_user:
        raise HTTPException(status_code=400, detail=f"The email: {payload.email} does not match. Sign up kro")
    
    return {"message": "Login Succesful"}



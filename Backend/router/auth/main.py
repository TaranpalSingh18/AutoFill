from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import json
from models.auth import Signup, Login
from db.database import db
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from datetime import datetime, timedelta, timezone
import os



auth_router = APIRouter(prefix="/auth")
users = db["users"]
hashed_password_context = CryptContext(schemes=['bcrypt_sha256'], deprecated="auto")
oath2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")

secret_key = os.getenv("JWT_SECRET_KEY")
algorithm = os.getenv("JWT_ALGO")
access_token_time = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

if not secret_key:
    raise ValueError("jwt_secret key is missing")

if not algorithm:
    raise ValueError( "No algorithm defined")

if not access_token_time:
    raise ValueError("No access time defined")


def create_access_tokens(data:dict, expires_delta: timedelta| None = None)->str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)

async def get_current_user(token: str = Depends(oath2_schema)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate the credentials",
    )

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = users.find_one({"email": email})
    if not user:
        raise credentials_exception

    return user

def get_hash_password(password: str)->str:
    return hashed_password_context.hash(password)

def verify_password(password: str, hashed_passwordd: str)->bool:
    try:
        return hashed_password_context.verify(password, hashed_passwordd)
    except UnknownHashError:
        # Backward compatibility for old plaintext records.
        return password == hashed_passwordd

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

    # Upgrade old plaintext passwords to hashed format after successful login.
    if hashed_password_context.identify(original_pass) is None:
        users.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"password": get_hash_password(payload_password)}},
        )
    

    token_expiry = timedelta(minutes=int(access_token_time))
    access_token = create_access_tokens(
        data={"sub": existing_user["email"]},
        expires_delta=token_expiry,
    )

    return {
        "message": "Login Successful",
        "access_token": access_token,
        "token_type": "bearer", 
    }




from passlib.context import CryptContext
import os 
from dotenv import load_dotenv
from datetime import datetime
import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
# password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_hash_password(password):
    return pwd_context.hash(password)

def verify_hashing(password, hashed_password):
    pwd_context.verify(password, hashed_password)
    
# token creation 
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_token(user:dict, delta_minutes: int = 10):
    #delta_minutes - when the token is invalid anymore, after x minutes
    data_to_encode = user.copy()
    expire_time = datetime.now() + datetime.timedelta(minutes=delta_minutes)
    data_to_encode.update({'exp': expire_time})
    return jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token:str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("token is invalid")
    
#create custom middleware for the "/update" route    
class TokenAuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        #checking only for the "/update" or "/profile" routes
        if request.url.path in ["/update", "/profile"]:
            header = request.headers.get("Authorization")
            if not header.lower().startswith("bearer") or not header:
                return JSONResponse({"detail": "Token missing or invalid"}, status_code=401)
            #split the string to get the token from header - like bearer <token>
            token = header.split(" ", 1)[1]
            try:
                payload = decode_token(token)
                request.state.user_id = payload.get("user_id")
            except ValueError as e:
                return JSONResponse({"detail": str(e)}, status_code=401)
        #get the data we want to update    
        response = await call_next(request)
        return response
        
    
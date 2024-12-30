from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, get_db
from .models import User
from .schemas import UserCreate, UserLogin, UserUpdate, UserProfile
from sqlalchemy.orm import Session
from .authentication import create_hash_password, verify_hashing, create_token, TokenAuthorizationMiddleware
from .caching import check_cache, update_cache
import redis as rd
import uvicorn

app = FastAPI()

#on startup of the application - run the database
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

#create CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #because we dont have fronend app, we use postman so we allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#create token middleware - made at authentication.py
app.add_middleware(TokenAuthorizationMiddleware)


app.post("/register", response_model=str, status_code=status.HTTP_201_CREATED)
async def register_user(req:UserCreate, db: Session = Depends(get_db)):
    
    #if password or username won't enter, fastapi will raise exception 422
    user = db.query(User).filter_by(email=req.email).first()
    if user:
        raise HTTPException(status_code=400, detail=f"user's email already exists")
    
    hashed_password = await create_hash_password(req.password)
    
    new_user = User(
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
        
    return f"user with email: {new_user.email} - created successfully"
    

app.post("/login", response_model=dict, status_code=status.HTTP_200_OK)
async def login_user(req:UserLogin, db: Session = Depends(get_db)):
    #check email
    user = db.query(User).filter_by(email=req.email).first()
    if not user:
        raise HTTPException(status_code=400, detail=f"Invalid email")
    
    #check password
    if not await verify_hashing(req.password, user.password):
        raise HTTPException(status_code=400, detail=f"Invalid password")
    
    # the default for delta_minutes is 10 - change value here if you want to 
    token = await create_token({"sub":user.email, "user_id":user.id}, delta_minutes=30)
    return {"access_token":token, "token_type":"bearer"}


app.put("/update", response_model=dict, status_code=status.HTTP_200_OK)
async def update_user(req:UserUpdate, request:Request, db: Session = Depends(get_db)):
    #req - the body - means here getting the data to update
    #request - the headers - means here checking the authorization of the middleware
    
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # If somehow no user_id is set, raise 401
        raise HTTPException(status_code=401, detail=f"no user_id in token")
    
    user = db.query(User).filter(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found")
    
    #for every variable - checking if exists in the request
    if req.first_name is not None:
        user.first_name = req.first_name
    if req.last_name is not None:
        user.last_name = req.last_name
    if req.email is not None:
        user.email = req.email
    if req.password is not None:
        # You might want to hash the new password before storing
        user.hashed_password = await create_hash_password(req.password)

    db.commit()
    db.refresh(user)
    
    try:
        update_cache(user)
    except rd.exceptions.RedisError as e:
        pass
    
    return {"message": "User updated successfully", "username": f"{user.first_name} {user.last_name}"}

@app.get("/profile", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def get_user_profile(request: Request, db: Session = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # If somehow no user_id is set, raise 401
        raise HTTPException(status_code=401, detail=f"no user_id in token") 
    
    try:
        user = await check_cache(user_id=user_id)
    except rd.exceptions.RedisError as e:
        pass
       
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # fastapi automatically gets from user just the relevant fields for UserProfile pydantic schema
    return user

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

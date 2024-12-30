import os 
from dotenv import load_dotenv
import redis as rd
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = 0  # default
PASSWORD = os.getenv("REDIS_PASSWORD", None)
# Create a global Redis client
redis_client = rd.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=PASSWORD,
)

def check_cache(user_id: int):
    cache_key = f"user:{user_id}"
    cache_user = redis_client.get(cache_key)
    if cache_user:
        user = json.loads(cache_user.encode("utf-8"))
    return user

def update_cache(user): 
    cache_key = f"user:{user.id}"
    user_dict = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    }
    redis_client.set(cache_key, json.dumps(user_dict))
    
    
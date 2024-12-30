from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os 

#load enviroment variables from .env file 
load_dotenv()
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")

#create url for mysql database
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{DATABASE_NAME}"


# Create an engine instance
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

Base = declarative_base()

def get_db():
    db = Session(engine)
    try: 
        yield db
    finally:
        db.close() 




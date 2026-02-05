from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
DEBUG = os.getenv("DEBUG") == "True"

engine = create_engine(DATABASE_URL, echo=DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

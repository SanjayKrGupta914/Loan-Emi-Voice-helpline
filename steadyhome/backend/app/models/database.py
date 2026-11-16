import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Import schema models from database package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from database.schema import Base, Borrower, Loan, EMI, Payment, Escalation, InteractionLog

def get_engine():
    return create_engine(f"sqlite:///{settings.DATABASE_PATH}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


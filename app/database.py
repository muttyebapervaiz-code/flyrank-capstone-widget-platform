from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Abhi ke liye SQLite use karenge (chota, file-based database, testing ke liye asaan)
DATABASE_URL = "sqlite:///./widget_platform.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
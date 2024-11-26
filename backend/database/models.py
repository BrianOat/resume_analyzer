from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    email = Column(String, primary_key=True, index=True)
    username = Column(String, index=True)
    hashed_password = Column(String, index=True)

    def __init__(self, email, username, hashed_password):
        self.email = email
        self.username = username
        self.hashed_password = hashed_password
        
DATABASE_URL = "sqlite:///./database/database.db"
engine = create_engine(DATABASE_URL)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

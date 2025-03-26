from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# SQLite database for simplicity
ENGINE = create_engine('sqlite:///immune_atlas.db')

def get_session():
    Session = sessionmaker(bind=ENGINE)
    return Session()

def init_db():
    Base.metadata.create_all(ENGINE)
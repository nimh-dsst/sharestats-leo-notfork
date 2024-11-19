import os

from dsst_etl import get_db_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base



def get_db_session():
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    engine = get_db_engine()
    Base.metadata.create_all(engine)

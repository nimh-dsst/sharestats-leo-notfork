from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from dsst_etl import get_db_engine

from .models import Base


def get_db_session():
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    engine = get_db_engine()
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)

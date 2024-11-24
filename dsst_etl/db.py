from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from dsst_etl import get_db_engine

from .models import Base


def get_db_session(is_test=False):
    engine = get_db_engine(is_test)
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(is_test=False):
    engine = get_db_engine(is_test)
    url = make_url(engine.url)
    database = url.database
    dialect_name = url.get_dialect().name

    print("url: ", url)
    print("database: ", database)
    print("dialect_name: ", dialect_name)

    print("engine.urlengine.urlengine.url: ", engine.url)
    print("database_exists(engine.url): ", database_exists(engine.url))
    if not database_exists(engine.url):
        print("Creating database")
        create_database(engine.url)
    Base.metadata.create_all(engine)

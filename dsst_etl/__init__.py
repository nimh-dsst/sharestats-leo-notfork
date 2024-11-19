"""
DSST ETL Package
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

def get_db_url():
    database_url = (
        "postgresql://"
        f"{os.environ['POSTGRES_USER']}"
        f":{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return database_url

def get_db_engine():
    return create_engine(get_db_url())

engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_version():
    try:
        from . import _version

        return _version.version
    except ImportError:
        generate_version_file()
        from . import _version

        return _version.version


def generate_version_file():
    import pkg_resources

    version = pkg_resources.get_distribution("dsst_etl").version
    version_file_content = f"version = '{version}'\n"

    version_file_path = os.path.join(os.path.dirname(__file__), "_version.py")
    with open(version_file_path, "w") as version_file:
        version_file.write(version_file_content)


__version__ = get_version()

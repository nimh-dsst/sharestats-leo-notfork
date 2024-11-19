import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# .env variables
load_dotenv()

# Database parameters from .env
db_params = {
    "dbname": os.getenv("POSTGRES_NAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
}
DATA_PATH = Path("delme_data")
OPEN_ACCESS_PATH = Path(DATA_PATH) / "oa_urls.csv"
NOT_OA_PATH = Path(DATA_PATH) / "not_oa_pmids.csv"


def get_oa_urls():
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Get pmid|oa_url for open access works
        cursor.execute(
            """
            SELECT o.work_id, o.oa_url
            FROM openalex_works_open_access o
            WHERE o.is_oa = TRUE
        """
        )
        result = cursor.fetchall()

        work_ids = [work_id for work_id, _ in result]
        oa_urls = [oa_url for _, oa_url in result]

        # Get pmids for these works
        cursor.execute(
            """
            SELECT i.pmid
            FROM openalex_works_ids i
            WHERE i.work_id IN %s
        """,
            (tuple(work_ids),),
        )
        pmid_values = cursor.fetchall()

        pmid_url_dict = {
            pmid[0].replace("https://pubmed.ncbi.nlm.nih.gov/", ""): oa_url
            for pmid, oa_url in zip(pmid_values, oa_urls)
        }

        pmid_url_df = pd.DataFrame(
            pmid_url_dict.items(), columns=["PMID", "oa_url"]
        )
        pmid_url_df.to_csv(OPEN_ACCESS_PATH, index=False)

    except psycopg2.Error as e:
        print("Error:", e)
    finally:
        cursor.close()
        conn.close()


def get_not_oa_pmids():
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()

        # Get pmids for closed access works
        cursor.execute(
            """
            SELECT o.work_id
            FROM openalex_works_open_access o
            WHERE o.is_oa = FALSE
        """
        )
        work_ids = cursor.fetchall()

        # Get pmids and dois for these works
        cursor.execute(
            """
            SELECT i.pmid, i.doi
            FROM openalex_works_ids i
            WHERE i.work_id IN %s
        """,
            (tuple(work_ids),),
        )
        id_values = cursor.fetchall()

        id_url_df = pd.DataFrame(id_values, columns=["PMID", "DOI"])
        id_url_df.to_csv(NOT_OA_PATH, index=False)

    except psycopg2.Error as e:
        print("Error:", e)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    get_oa_urls()
    get_not_oa_pmids()

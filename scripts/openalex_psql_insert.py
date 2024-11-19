import gzip
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

"""
Loads all csv files into database
"""


def main():
    load_dotenv()
    data_path = Path(r"./delme_data/csv-files/")
    # Database parameters from .env
    db_params = {
        "dbname": os.getenv("POSTGRES_NAME"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
    }

    # Table names and corresponding CSV file paths
    table_mapping = {
        "openalex_works": "works.csv.gz",
        "openalex_works_primary_locations": "works_primary_locations.csv.gz",
        "openalex_works_locations": "works_locations.csv.gz",
        "openalex_works_best_oa_locations": "works_best_oa_locations.csv.gz",
        "openalex_works_authorships": "works_authorships.csv.gz",
        "openalex_works_biblio": "works_biblio.csv.gz",
        "openalex_works_concepts": "works_concepts.csv.gz",
        "openalex_works_ids": "works_ids.csv.gz",
        "openalex_works_mesh": "works_mesh.csv.gz",
        "openalex_works_open_access": "works_open_access.csv.gz",
        "openalex_works_referenced_works": "works_referenced_works.csv.gz",
        "openalex_works_related_works": "works_related_works.csv.gz",
    }
    # Table names and corresponding column names.
    # column names must match csv headers
    table_columns = {
        "openalex_works": [
            "id",
            "doi",
            "title",
            "display_name",
            "publication_year",
            "publication_date",
            "type",
            "cited_by_count",
            "is_retracted",
            "is_paratext",
            "cited_by_api_url",
            "abstract_inverted_index",
        ],
        "openalex_works_primary_locations": [
            "work_id",
            "source_id",
            "landing_page_url",
            "pdf_url",
            "is_oa",
            "version",
            "license",
        ],
        "openalex_works_locations": [
            "work_id",
            "source_id",
            "landing_page_url",
            "pdf_url",
            "is_oa",
            "version",
            "license",
        ],
        "openalex_works_best_oa_locations": [
            "work_id",
            "source_id",
            "landing_page_url",
            "pdf_url",
            "is_oa",
            "version",
            "license",
        ],
        "openalex_works_authorships": [
            "work_id",
            "author_position",
            "author_id",
            "institution_id",
            "raw_affiliation_string",
        ],
        "openalex_works_biblio": [
            "work_id",
            "volume",
            "issue",
            "first_page",
            "last_page",
        ],
        "openalex_works_concepts": ["work_id", "concept_id", "score"],
        "openalex_works_ids": [
            "work_id",
            "openalex",
            "doi",
            "mag",
            "pmid",
            "pmcid",
        ],
        "openalex_works_mesh": [
            "work_id",
            "descriptor_ui",
            "descriptor_name",
            "qualifier_ui",
            "qualifier_name",
            "is_major_topic",
        ],
        "openalex_works_open_access": [
            "work_id",
            "is_oa",
            "oa_status",
            "oa_url",
            "any_repository_has_fulltext",
        ],
        "openalex_works_referenced_works": ["work_id", "referenced_work_id"],
        "openalex_works_related_works": ["work_id", "related_work_id"],
    }

    # Connect to the database
    conn = psycopg2.connect(**db_params)
    cursor = None
    try:
        cursor = conn.cursor()

        # Execute COPY for each table
        for table_name, columns in table_columns.items():
            with gzip.open(
                data_path.joinpath(table_mapping[table_name]), "rt"
            ) as f:
                copy_sql = (
                    f"COPY {table_name} FROM STDIN WITH"
                    + " (FORMAT CSV, HEADER TRUE)"
                )
                cursor.copy_expert(copy_sql, f)

        conn.commit()
    except psycopg2.Error as e:
        print(f"Error: {e}")
    finally:
        if cursor:
            cursor.close()
        conn.close()


if __name__ == "__main__":
    main()

import argparse
import sys
from dsst_etl.extract import extract_data_from_pdf_dir
from dsst_etl.transform import transform_data
from dsst_etl.load import load_data
from dsst_etl.db import get_db_session
from logging_config import setup_logging  # Import the logging setup function

# Set up logging
logger = setup_logging()


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="ETL script for processing PDF data")
    parser.add_argument(
        "pdf_dir", type=str, help="Path to directory containing PDF files"
    )

    # Parse arguments
    args = parser.parse_args()

    try:
        # Initialize database session
        db_session = get_db_session()
        logger.info({"message": "Database session initialized."})

        # Step 1: Extract data
        data = extract_data_from_pdf_dir(args.pdf_dir)
        logger.info({"message": "Data extraction complete."})

        # Step 2: Transform data
        cleaned_data = transform_data(data)
        logger.info({"message": "Data transformation complete."})

        # Step 3: Load data
        load_data(cleaned_data, db_session)
        logger.info({"message": "Data loading complete."})

        db_session.commit()
        logger.info({"message": "Database commit successful."})
    except Exception as e:
        logger.error({"Error": str(e)}, exc_info=True)
        if "db_session" in locals():
            db_session.rollback()
            logger.info({"message": "Database rollback executed."})
        sys.exit(1)
    finally:
        if "db_session" in locals():
            db_session.close()
            logger.info({"message": "Database session closed."})


if __name__ == "__main__":
    main()

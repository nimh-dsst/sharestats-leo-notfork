import logging
import argparse
from dsst_etl.db import get_db_session
from dsst_etl.upload_rtransparent_data import RTransparentDataUploader  

logger = logging.getLogger(__name__)
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Upload RTransparent data from a file.')
    parser.add_argument('input_file', type=str, help='Path to the input file (feather or parquet)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create an instance of RTransparentDataUploader
    uploader = RTransparentDataUploader(get_db_session())
    
    # Call the method to upload data with the input file
    uploader.upload_data(args.input_file)  # Assuming 'upload_data' accepts a file path

if __name__ == "__main__":
    main()


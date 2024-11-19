import logging
from dsst_etl.upload_pdfs import upload_directory

logger = logging.getLogger(__name__)
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

def main():
    """
    Main function to run the PDF upload process.
    
    Usage:
        python upload_pdfs.py /path/to/pdf/directory my-s3-bucket "Optional comment"
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload PDFs to S3 and create database records')
    parser.add_argument('pdf_directory', help='Directory containing PDF files to upload')
    parser.add_argument('--comment', help='Optional comment for provenance record')
    
    args = parser.parse_args()
    logger.info(f"Uploading PDFs from {args.pdf_directory} with comment: {args.comment}")
    try:
        upload_directory(
            pdf_directory_path=args.pdf_directory,
            comment=args.comment
        )
        logger.info("Upload process completed successfully")
    except Exception as e:
        logger.error(f"Upload process failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()

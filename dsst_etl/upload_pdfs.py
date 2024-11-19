import hashlib
import os
import logging
from typing import List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from dsst_etl._utils import get_compute_context_id, get_bucket_name
from dsst_etl.models import Documents, Provenance
from dsst_etl.db import get_db_session
from pathlib import Path
import psycopg2

from dsst_etl import __version__

# Configure logging
logger = logging.getLogger(__name__)


class PDFUploader:
    """
    Handles PDF uploads to S3 and maintains database records of uploads.
    
    This class manages:
    1. Uploading PDFs to S3
    2. Creating document records
    3. Maintaining provenance logs
    4. Linking documents to works
    """
    
    def __init__(self):
        """
        Initialize the uploader with S3 bucket and database connection.
        
        Args:
            bucket_name (str): Name of the S3 bucket for PDF storage
        """
        self.bucket_name = get_bucket_name()
        self.s3_client = boto3.client('s3')
        self.db_session = get_db_session()
        
    def upload_pdfs(self, pdf_paths: List[str]) -> Tuple[List[str], List[str]]:
        """
        Upload multiple PDFs to S3 bucket.
        
        Args:
            pdf_paths (List[str]): List of paths to PDF files
            
        Returns:
            Tuple[List[str], List[str]]: Lists of successful and failed uploads
        """
        successful_uploads = []
        failed_uploads = []
        
        for pdf_path in pdf_paths:
            try:
                logger.info(f"Uploading {pdf_path} to S3")

                # Generate S3 key (path in bucket)
                s3_key = f"pdfs/{os.path.basename(pdf_path)}"
                # Upload file to S3
                self.s3_client.upload_file(pdf_path, self.bucket_name, s3_key)
                successful_uploads.append(pdf_path)
                logger.info(f"Successfully uploaded {pdf_path} to S3")
                
            except ClientError as e:
                logger.error(f"Failed to upload {pdf_path}: {str(e)}")
                failed_uploads.append(pdf_path)
                
        return successful_uploads, failed_uploads

    def create_document_records(
        self, 
        successful_uploads: List[str]
    ) -> List[Documents]:
        """
        Create document records for successfully uploaded PDFs.
        
        Args:
            successful_uploads (List[str]): List of successfully uploaded PDF paths
            
        Returns:
            List[Document]: List of created document records
        """
        documents = []
        
        for pdf_path in successful_uploads:
            s3_key = f"pdfs/{os.path.basename(pdf_path)}"
            
            pdf_path = Path(pdf_path)
            file_content = pdf_path.read_bytes()
            
            hash_data = hashlib.md5(file_content).hexdigest()
            
            document = Documents(
                hash_data=hash_data,
                s3uri=f"s3://{self.bucket_name}/{s3_key}",
            )
            
            try:
                self.db_session.add(document)
                self.db_session.commit()
                documents.append(document)
            except psycopg2.errors.UniqueViolation:
                self.db_session.rollback()
                logger.warning(f"Document with hash {hash_data} already exists. Skipping.")
            
        logger.info(f"Created {len(documents)} document records")
        return documents

    def create_provenance_record(
        self, 
        documents: List[Documents],
        comment: str = None
    ) -> Provenance:
        """
        Create a provenance record for the upload batch and link it to documents.
        
        Args:
            documents (List[Document]): List of document records
            comment (str): Comment about the upload batch
            
        Returns:
            Provenance: Created provenance record
        """
        provenance = Provenance(
            pipeline_name="Document Upload",
            version=__version__,
            compute=get_compute_context_id(),
            personnel=os.environ.get('HOSTNAME'),
            comment=comment
        )
        
        self.db_session.add(provenance)
        self.db_session.flush()
        
        # Link provenance ID to documents
        for document in documents:
            document.provenance_id = provenance.id
            
        self.db_session.commit()
        logger.info(f"Created provenance record and linked to {len(documents)} documents")
        return provenance

    def link_documents_to_work(
        self,
        document_ids: List[int],
        work_id: int
    ) -> None:
        """
        Link existing documents to a work ID.
        
        Args:
            document_ids (List[int]): List of document IDs to update
            work_id (int): Work ID to link documents to
        """
        for doc_id in document_ids:
            document = self.db_session.query(Documents).get(doc_id)
            if document:
                document.work_id = work_id
                
        self.db_session.commit()
        logger.info(f"Linked {len(document_ids)} documents to work_id {work_id}")

def upload_directory(
    pdf_directory_path: str,
    comment: Optional[str] = None
) -> None:
    """
    Upload all PDFs from a directory to S3 and create necessary database records.
    
    Args:
        pdf_directory_path (str): Path to directory containing PDFs
        bucket_name (str): S3 bucket name
        comment (Optional[str]): Comment for provenance record
    """
    # Get list of PDF files
    pdf_files = [
        os.path.join(pdf_directory_path, f) 
        for f in os.listdir(pdf_directory_path) 
        if f.lower().endswith('.pdf')
    ]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_directory_path}")
        return
        
    
    uploader = PDFUploader()
    
    # Upload PDFs
    successful_uploads, failed_uploads = uploader.upload_pdfs(pdf_files)
    
    if failed_uploads:
        logger.warning(f"Failed to upload {len(failed_uploads)} files")
    
    if successful_uploads:
        # Create document records
        documents = uploader.create_document_records(successful_uploads)
        
        # Create provenance record
        uploader.create_provenance_record(documents, comment)







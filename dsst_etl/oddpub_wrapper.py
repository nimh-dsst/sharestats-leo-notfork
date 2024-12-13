import logging
from pathlib import Path

import requests
from sqlalchemy.orm import Session

from dsst_etl.models import OddpubMetrics

from .config import config

logger = logging.getLogger(__name__)


class OddpubWrapper:
    """
    Wrapper class for the ODDPub API.
    """

    def __init__(
        self,
        db_session: Session = None,
        work_id: int = None,
        document_id: int = None,
        oddpub_host_api: str = config.ODDPUB_HOST_API,
    ):
        """
        Initialize the OddpubWrapper.

        Args:
            db (Session, optional): SQLAlchemy database session
            work_id (int): ID of the work being processed
            document_id (int): ID of the document being processed
        """
        try:
            self.oddpub_host_api = oddpub_host_api
            self.db_session = db_session
            self.work_id = work_id
            self.document_id = document_id
            logger.info("Successfully initialized OddpubWrapper")
        except Exception as e:
            logger.error(f"Failed to initialize OddpubWrapper: {str(e)}")
            raise

    def process_pdfs(self, pdf_folder: str) -> OddpubMetrics:
        """
        Process PDFs through the complete ODDPub workflow and store results in database.

        Args:
            pdf_folder (str): Path to folder containing PDF files

        Returns:
            OddpubMetrics: Results of open data analysis
        """
        try:
            # Iterate over each PDF file in the folder
            for pdf_file in Path(pdf_folder).glob("*.pdf"):
                with open(pdf_file, "rb") as f:
                    # Use requests to call the API
                    response = requests.post(
                        f"{self.oddpub_host_api}/oddpub", files={"file": f}
                    )
                    response.raise_for_status()

                    r_result = response.json()
                    oddpub_metrics = OddpubMetrics(**r_result)
                    oddpub_metrics.work_id = self.work_id
                    oddpub_metrics.document_id = self.document_id
                    self.db_session.add(oddpub_metrics)
                    self.db_session.commit()

        except Exception as e:
            logger.error(f"Error in PDF processing workflow: {str(e)}")
            self.db_session.rollback()

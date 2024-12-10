import logging
import shutil
from pathlib import Path

import pandas as pd
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from sqlalchemy.orm import Session

from .db import get_db
from .models import OddpubMetrics, Provenance

logger = logging.getLogger(__name__)


class OddpubWrapper:
    """
    A wrapper class for calling ODDPub R functions from Python using rpy2.
    """

    def __init__(
        self, db: Session = None, work_id: int = None, document_id: int = None
    ):
        """
        Initialize the OddpubWrapper.

        Args:
            db (Session, optional): SQLAlchemy database session
            work_id (int): ID of the work being processed
            document_id (int): ID of the document being processed
        """
        try:
            self.base = importr("base")
            self.oddpub = importr("oddpub")
            pandas2ri.activate()
            self.db = db if db is not None else next(get_db())
            self.work_id = work_id
            self.document_id = document_id
            logger.info("Successfully initialized OddpubWrapper")
        except Exception as e:
            logger.error(f"Failed to initialize OddpubWrapper: {str(e)}")
            raise

    def _create_provenance(self) -> int:
        """Create provenance record for this processing run."""
        try:
            provenance = Provenance(
                pipeline_name="oddpub",
                version="1.0",  # You might want to get this from your version file
                compute="PDF text analysis using ODDPub R package",
                personnel="automated",
            )
            self.db.add(provenance)
            self.db.flush()  # Get the ID without committing
            return provenance.id
        except Exception as e:
            logger.error(f"Error creating provenance record: {str(e)}")
            raise

    def _convert_pdfs(self, pdf_folder: str, output_folder: str) -> None:
        """Convert PDFs to text using oddpub::pdf_convert."""
        try:
            r_pdf_folder = robjects.StrVector([str(Path(pdf_folder))])
            r_output_folder = robjects.StrVector([str(Path(output_folder))])

            self.oddpub.pdf_convert(r_pdf_folder, r_output_folder)
            logger.info(
                f"Successfully converted PDFs from {pdf_folder} to text in {output_folder}"
            )
        except Exception as e:
            logger.error(f"Error in PDF conversion: {str(e)}")
            raise

    def _load_pdf_text(self, pdf_text_folder: str) -> robjects.vectors.ListVector:
        """Load converted PDF text using oddpub::pdf_load."""
        try:
            r_text_folder = robjects.StrVector([str(Path(pdf_text_folder))])
            pdf_text_sentences = self.oddpub.pdf_load(r_text_folder)
            logger.info(f"Successfully loaded PDF text from {pdf_text_folder}")
            return pdf_text_sentences
        except Exception as e:
            logger.error(f"Error in loading PDF text: {str(e)}")
            raise

    def _search_open_data(
        self, pdf_text_sentences: robjects.vectors.ListVector
    ) -> OddpubMetrics:
        """Search for open data statements using oddpub::open_data_search."""
        try:
            open_data_results = self.oddpub.open_data_search(pdf_text_sentences)
            result = self._convert_r_result(open_data_results)
            logger.info("Successfully completed open data search")
            return result
        except Exception as e:
            logger.error(f"Error in open data search: {str(e)}")
            raise

    def _cleanup_output_folder(self, output_folder: str) -> None:
        """Remove the temporary output folder and its contents."""
        try:
            shutil.rmtree(output_folder)
            logger.info(f"Successfully cleaned up output folder: {output_folder}")
        except Exception as e:
            logger.error(f"Error cleaning up output folder: {str(e)}")
            raise

    def process_pdfs(self, pdf_folder: str, output_folder: str) -> OddpubMetrics:
        """
        Process PDFs through the complete ODDPub workflow and store results in database.

        Args:
            pdf_folder (str): Path to folder containing PDF files
            output_folder (str): Path to temporary output folder for converted text files

        Returns:
            OddpubMetrics: Results of open data analysis
        """
        try:
            # Create output directory if it doesn't exist
            Path(output_folder).mkdir(parents=True, exist_ok=True)

            # Execute the workflow
            self._convert_pdfs(pdf_folder, output_folder)
            pdf_text_sentences = self._load_pdf_text(output_folder)
            result = self._search_open_data(pdf_text_sentences)

            # Store result in database
            self.db.add(result)
            self.db.commit()
            logger.info("Successfully stored results in database")

            # Cleanup
            self._cleanup_output_folder(output_folder)

            return result
        except Exception as e:
            logger.error(f"Error in PDF processing workflow: {str(e)}")
            self.db.rollback()
        finally:
            # Attempt cleanup even if processing failed
            self._cleanup_output_folder(output_folder)
            if self.db:
                self.db.close()

    def _convert_r_result(self, r_result) -> OddpubMetrics:
        """Convert R results to OddpubMetrics instance."""
        try:
            df = pd.DataFrame(r_result)
            result_dict = df.to_dict("records")[0] if not df.empty else {}

            # Create provenance record
            provenance_id = self._create_provenance()

            # Create new OddpubMetrics instance with relationships
            oddpub_metrics = OddpubMetrics(
                article=result_dict.get("article"),
                is_open_data=result_dict.get("is_open_data", False),
                open_data_category=result_dict.get("open_data_category"),
                is_reuse=result_dict.get("is_reuse", False),
                is_open_code=result_dict.get("is_open_code", False),
                is_open_data_das=result_dict.get("is_open_data_das", False),
                is_open_code_cas=result_dict.get("is_open_code_cas", False),
                das=result_dict.get("das"),
                open_data_statements=result_dict.get("open_data_statements"),
                cas=result_dict.get("cas"),
                open_code_statements=result_dict.get("open_code_statements"),
                work_id=self.work_id,
                document_id=self.document_id,
                provenance_id=provenance_id,
            )
            return oddpub_metrics
        except Exception as e:
            logger.error(f"Error converting R result: {str(e)}")
            raise

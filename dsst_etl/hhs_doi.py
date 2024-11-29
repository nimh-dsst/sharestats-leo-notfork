import csv
from pathlib import Path
from typing import Generator

import pdf2doi
import pypdf
from pdf2doi import config as pdf2doi_config
from pypdf._doc_common import DocumentInformation
from pypdf.errors import EmptyFileError, PdfStreamError
from tqdm import tqdm

from dsst_etl import logger


def _extract_doi(pdf: Path) -> dict[str, str | None]:
    """
    Extract the Digital Object Identifier (DOI) from a PDF file.

    Parameters
    ----------
    pdf : Path
        Path to the PDF file from which to extract the DOI.

    Returns
    -------
    dict[str, str | None]
        A dictionary containing the DOI information with the following keys:
        - 'identifier': The extracted DOI, or None if extraction fails
        - 'identifier_type': Type of identifier (e.g., 'DOI'), or None
        - 'extraction_method': Method used to extract the DOI, or None

    Notes
    -----
    Uses the pdf2doi library to attempt DOI extraction. If multiple DOIs are found,
    the first result is returned. If extraction fails, returns a dictionary with
    None values.
    """
    # Extract DOI
    try:
        doi_results = pdf2doi.pdf2doi(str(pdf.absolute()))
    except Exception:
        logger.error(f"pdf2doi failed on {pdf}", exc_info=True)
        doi_dict: dict[str, str | None] = {
            "identifier": None,
            "identifier_type": None,
            "extraction_method": None,
        }
        return doi_dict
    # Get the first result if multiple are returned
    doi_info = doi_results[0] if isinstance(doi_results, list) else doi_results
    if isinstance(doi_info, dict):
        identifier: str | None = doi_info.get("identifier")
        identifier_type: str | None = doi_info.get("identifier_type")
        extraction_method: str | None = doi_info.get("method")
        doi_dict = {
            "identifier": identifier,
            "identifier_type": identifier_type,
            "extraction_method": extraction_method,
        }
        return doi_dict
    else:
        logger.warning(f"pdf2doi failed to extract a dictionary on {pdf}")
        doi_dict: dict[str, str | None] = {
            "identifier": None,
            "identifier_type": None,
            "extraction_method": None,
        }
        return doi_dict


def _extract_hhs_info(pdf: Path) -> dict[str, str | None]:
    """
    Extract HHS (Health and Human Services) related information from a PDF file.

    Parameters
    ----------
    pdf : Path
        Path to the PDF file from which to extract information.

    Returns
    -------
    dict[str, str | None]
        A dictionary containing HHS-related PDF metadata with the following keys:
        - 'name': Full path of the PDF file
        - 'producer': PDF producer metadata
        - 'creator': PDF creator metadata
        - 'header': PDF header information
        - 'has_hhs_text': Whether 'HHS Public Access' text is found
        - 'error': Any error encountered during extraction, or None

    Notes
    -----
    Attempts to extract PDF metadata and check for 'HHS Public Access' text.
    Handles various potential errors during PDF reading and text extraction.
    """
    try:
        with open(pdf, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            metadata = pdf_reader.metadata
            try:
                page = pdf_reader.pages[0]
                text = page.extract_text()
                has_hhs_text: bool = "HHS Public Access" in text
            except Exception as e:
                hhs_info: dict[str, str | None] = {
                    "name": str(pdf.absolute()),
                    "producer": None,
                    "creator": None,
                    "header": None,
                    "has_hhs_text": None,
                    "error": str(e),
                }
                return hhs_info

            if isinstance(metadata, DocumentInformation):
                hhs_info = {
                    "name": str(pdf.absolute()),
                    "producer": metadata.producer,
                    "creator": metadata.creator,
                    "header": pdf_reader.pdf_header,
                    "has_hhs_text": str(has_hhs_text),
                    "error": None,
                }
            else:
                hhs_info = {
                    "name": str(pdf.absolute()),
                    "producer": None,
                    "creator": None,
                    "header": None,
                    "has_hhs_text": str(has_hhs_text),
                    "error": "No metadata",
                }
            return hhs_info
    except (PdfStreamError, OSError, EmptyFileError) as e:
        hhs_info = {
            "name": str(pdf.absolute()),
            "producer": None,
            "creator": None,
            "header": None,
            "has_hhs_text": None,
            "error": str(e),
        }
        return hhs_info


def _parse_pdfs(
    pdf_dir: Path,
    output_csv: Path,
    output_exists: bool,
    new_run: bool,
    make_filelist: bool,
) -> list[Path] | Generator[Path, None, None] | None:
    """
    Parse PDF files in a directory, handling previously processed files.

    Parameters
    ----------
    pdf_dir : Path
        Directory containing PDF files to process.
    output_csv : Path
        Path to the output CSV file tracking processed PDFs.
    output_exists : bool
        Indicates whether the output CSV file already exists.
    new_run : bool
        If True, prevents reusing previously processed PDFs.
    make_filelist : bool
        If True, converts PDF generator to a list for memory-intensive progress tracking.

    Returns
    -------
    list[Path] | Generator[Path] | None
        List or generator of PDF files to process, or None if all PDFs are already processed.

    Raises
    ------
    FileExistsError
        If `new_run` is True and the output CSV file already exists.

    Notes
    -----
    This function handles three scenarios:
    1. Continuing a previous run: Skips already processed PDFs
    2. Starting a new run: Raises error if output file exists
    3. First-time run: Processes all PDFs in the directory
    """
    if output_exists and new_run is False:
        logger.info("Removing previously processed PDFs")
        filenames: list[Path] = []
        with open(output_csv, "r") as file:
            csv_dict_reader = csv.DictReader(file)
            for row in csv_dict_reader:
                if row["identifier_type"] == "DOI":
                    filenames.append(Path(row["name"]).relative_to(Path.cwd()))
                else:
                    continue
        previously_found: set[Path] = set(filenames)
        pdfs: list[Path] | Generator[Path] = list(
            set(list(pdf_dir.rglob("*.[pP][dD][fF]"))) - previously_found
        )
        logger.info(f"Found {len(previously_found)} previously processed PDFs")
        if len(pdfs) == 0:
            return None
    elif output_exists and new_run is True:
        raise FileExistsError(
            f"{output_csv} exists and new_run is True."
            + " Please remove existing file prior to a new run!"
        )
    else:
        # keep a generator for memory management
        pdfs = pdf_dir.rglob("*.[pP][dD][fF]")
        if make_filelist:
            pdfs = list(pdfs)
    return pdfs


def extract_pdf_metadata(
    pdf_dir: Path,
    output_csv: Path,
    new_run: bool = False,
    make_filelist: bool = True,
    pdf2doi_verbose: bool = False,
) -> None:
    """
    Extract metadata from PDFs in a specified directory and save to a CSV file.

    Parameters
    ----------
    pdf_dir : Path
        Directory containing PDF files to process.
    output_csv : Path
        Path to the CSV file where extracted metadata will be saved.
    new_run : bool, optional
        If True, raises an error if the output CSV file already exists.
        Defaults to False.
    make_filelist : bool, optional
        If True, generates a list of all PDFs before processing.
        This allows tqdm to show a total count but uses more memory.
        Defaults to True.
    pdf2doi_verbose : bool, optional
        If True, enables verbose output from the `pdf2doi` library.
        Defaults to False.

    Returns
    -------
    None
        Writes metadata results directly to the specified CSV file.

    Raises
    ------
    FileExistsError
        If `new_run` is True and the output CSV file already exists.

    Notes
    -----
    Extracts metadata for each PDF in the specified directory, including:
    - DOI information (if available)
    - HHS-related metadata
    - PDF file information
    Saves the results in a CSV file with detailed metadata.
    """

    pdf2doi_config.set("verbose", pdf2doi_verbose)

    output_exists: bool = output_csv.exists()

    pdfs: list[Path] | Generator[Path, None, None] | None = _parse_pdfs(
        pdf_dir, output_csv, output_exists, new_run, make_filelist
    )
    if pdfs is not None:
        with open(output_csv, "a") as f_out:
            fieldnames: list[str] = [
                "identifier",
                "identifier_type",
                "extraction_method",
                "name",
                "producer",
                "creator",
                "header",
                "has_hhs_text",
                "error",
            ]
            writer: csv.DictWriter = csv.DictWriter(
                f_out, fieldnames, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\"
            )
            if not output_exists:
                writer.writeheader()

            for pdf in tqdm(pdfs):
                doi_dict: dict[str, str | None] = _extract_doi(pdf)
                hhs_dict: dict[str, str | None] = _extract_hhs_info(pdf)
                pdf_info: dict[str, str | None] = doi_dict | hhs_dict
                writer.writerow(pdf_info)

        logger.info(f"Metadata extracted to {output_csv}")
    else:
        logger.info(f"All PDFs already accounted for in {output_csv}!")

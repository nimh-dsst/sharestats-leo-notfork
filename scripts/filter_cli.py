import argparse
from pathlib import Path

import pandas as pd
import pypdf
from pypdf._doc_common import DocumentInformation
from pypdf.errors import EmptyFileError, PdfStreamError
from tqdm import tqdm


def extract_pdf_metadata(pdf_dir: Path, output_csv: Path):
    """
    Extract metadata from PDFs in the specified directory and save to CSV.

    Args:
        pdf_dir (Path): Directory containing PDF files
        output_csv (Path): Path to save output CSV file
    """
    dicts: list[dict] = []
    pdfs: list[Path] = list(pdf_dir.rglob("*pdf"))

    for pdf in tqdm(pdfs, total=len(pdfs)):
        try:
            with open(pdf, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                metadata = pdf_reader.metadata
                try:
                    page = pdf_reader.pages[0]
                    text = page.extract_text()
                    has_hhs_text: bool = "HHS Public Access" in text
                except Exception as e:
                    pdf_info: dict = {
                        "name": pdf.absolute(),
                        "producer": None,
                        "creator": None,
                        "header": None,
                        "has_hhs_text": None,
                        "error": str(e),
                    }
                    dicts.append(pdf_info)
                    continue

                if isinstance(metadata, DocumentInformation):
                    pdf_info = {
                        "name": pdf.absolute(),
                        "producer": metadata.producer,
                        "creator": metadata.creator,
                        "header": pdf_reader.pdf_header,
                        "has_hhs_text": has_hhs_text,
                        "error": None,
                    }
                else:
                    pdf_info = {
                        "name": pdf.absolute(),
                        "producer": None,
                        "creator": None,
                        "header": None,
                        "has_hhs_text": has_hhs_text,
                        "error": "No metadata",
                    }
        except (PdfStreamError, OSError, EmptyFileError) as e:
            pdf_info = {
                "name": pdf.absolute(),
                "producer": None,
                "creator": None,
                "header": None,
                "has_hhs_text": None,
                "error": str(e),
            }

        dicts.append(pdf_info)

    df: pd.DataFrame = pd.DataFrame(dicts)
    df.to_csv(output_csv, index=False)
    print(f"Metadata extracted to {output_csv}")


def main():
    """
    CLI entry point for PDF metadata extraction.
    """
    parser = argparse.ArgumentParser(
        description="Extract metadata from PDFs in a directory."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("./2024_all_ics/pdfs"),
        help="Directory containing PDF files (default: ./2024_all_ics/pdfs)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("has_hhs.csv"),
        help="Output CSV file path (default: has_hhs.csv)",
    )

    args = parser.parse_args()

    # Validate input directory exists
    if not args.input_dir.is_dir():
        print(f"Error: Input directory {args.input_dir} does not exist.")
        return

    extract_pdf_metadata(args.input_dir, args.output)


if __name__ == "__main__":
    main()

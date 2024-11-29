import argparse
from pathlib import Path

from dsst_etl.hhs_doi import extract_pdf_metadata


def main():
    """
    CLI entry point for extracting metadata from PDFs.

    This function parses command-line arguments to specify the input directory,
    output CSV file, and other configuration options, then processes the PDFs
    accordingly.

    Parameters
    ----------
    None

    Returns
    -------
    None
        This function is designed to be run from the command line and does not
        return any value.

    Command-Line Arguments
    ----------------------
    -i, --input-dir : Path, optional
        Directory containing PDF files to process. Defaults to './2024_all_ics/pdfs'.
    -o, --output : Path, optional
        Path to the output CSV file. Defaults to './has_hhs.csv'.
    -n, --new-run : bool, optional
        If True, ignores any existing output CSV file. Defaults to False.
    -m, --make-filelist : bool, optional
        If True, generates a file list before processing for tqdm to show progress.
        Defaults to False.
    -v, --verbose : bool, optional
        If True, enables verbose output from the `pdf2doi` library. Defaults to False.

    Raises
    ------
    ValueError
        If the specified input directory does not exist.
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
        default=Path("./has_hhs.csv"),
        help="Output CSV file path (default: ./has_hhs.csv)",
    )
    parser.add_argument(
        "-n",
        "--new-run",
        action="store_true",
        help="Ignore existing output CSV file if it exists",
    )
    parser.add_argument(
        "-m",
        "--make-filelist",
        action="store_true",
        help="Make filelist prior to for loop."
        + "Allows tqdm to provide total but must keep filelist in memory.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print proccessing output from pdf2doi",
    )
    args = parser.parse_args()

    # Validate input directory exists
    if not args.input_dir.is_dir():
        print(f"Error: Input directory {args.input_dir} does not exist.")
        return

    extract_pdf_metadata(
        args.input_dir,
        args.output,
        new_run=args.new_run,
        make_filelist=args.make_filelist,
        pdf2doi_verbose=args.verbose,
    )


if __name__ == "__main__":
    main()

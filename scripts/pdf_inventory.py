from pathlib import Path
import pandas as pd
from typing import Generator

DATA_ROOT: Path = Path("2024_all_ics")
PMIDS_ARTICLES_CSV: Path = DATA_ROOT.joinpath("pmids_articles_2024.csv")
PDF_DOWNLOAD_DIRECTORY: Path = DATA_ROOT.joinpath("pdfs")

SOURCES: list[Path] = [DATA_ROOT, PMIDS_ARTICLES_CSV, PDF_DOWNLOAD_DIRECTORY]


def check_sources(sources: list[Path] = SOURCES) -> bool:
    existances: list[bool] = []
    for source in sources:
        source_exists: bool = source.exists()
        existances.append(source_exists)
    return all(existances)


def append_pdf_download_inventory(
    pmids_articles_csv: Path = PMIDS_ARTICLES_CSV,
    pdf_download_directory: Path = PDF_DOWNLOAD_DIRECTORY,
) -> pd.DataFrame:
    parsed_pmids: pd.DataFrame = pd.read_csv(pmids_articles_csv)
    downloaded_pdfs: Generator = pdf_download_directory.glob("*.pdf")
    pdf_pmids: list[str] = []
    for pdf in downloaded_pdfs:
        pdf_pmids.append(pdf.stem)
    parsed_pmids["METAPUB_DOWNLOAD"] = parsed_pmids["PMID"].apply(
        lambda x: str(int(x)) in pdf_pmids
    )
    return parsed_pmids


def summarize_pdf_inventory(
    inventory: pd.DataFrame, export_csv_filepath: str | Path | None = None
) -> pd.DataFrame:
    total_num_unique_pmids: int = len(inventory.drop_duplicates(subset="PMID"))
    num_pdf_found: int = sum(
        inventory.drop_duplicates(subset="PMID")["METAPUB_DOWNLOAD"]
    )
    num_pdf_not_found: int = total_num_unique_pmids - num_pdf_found
    percent_pdf_found: float = num_pdf_found / len(
        inventory.drop_duplicates(subset="PMID")
    )
    if export_csv_filepath is not None:
        with open(export_csv_filepath, "w") as f_out:
            f_out.write(f"Number of PMIDs found: {num_pdf_found}\n")
            f_out.write(f"Number of PMIDs not found: {num_pdf_not_found}\n")
            f_out.write(
                f"Total number of unique PMIDs: {total_num_unique_pmids}\n"
            )
            f_out.write(
                f"Percent of unique PMIDs found: {percent_pdf_found}\n"
            )
    return pd.DataFrame()


if __name__ == "__main__":
    all_sources_present: bool = check_sources()
    assert all_sources_present
    pmid_inventory: pd.DataFrame = append_pdf_download_inventory()
    pmid_inventory.to_csv(
        DATA_ROOT.joinpath("pmid_download_pdf_inventory.csv")
    )
    summarize_pdf_inventory(
        pmid_inventory,
        export_csv_filepath=DATA_ROOT.joinpath("metapub_pdf_summary.txt"),
    )

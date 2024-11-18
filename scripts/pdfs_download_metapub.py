import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from metapub import FindIt
from multiprocessing import Pool

"""
Uses pmids_articles.csv and tries to get a pdf link from PubMed
Ignores openalex database
Skips files already downloaded
"""
data = Path("2024_all_ics")
data.joinpath("pdfs").mkdir(exist_ok=True)
df = pd.read_csv(data / "pmids_articles_2024.csv")
pdf_pmids = [
    int(pdf_file.strip(".pdf"))
    for pdf_file in os.listdir(data / "pdfs")
    if pdf_file.endswith(".pdf")
]
df = df[~df["PMID"].isin(pdf_pmids)]

pmids = set(df["PMID"].astype("Int64"))


def download_pdf(pmid):
    try:
        src = FindIt(pmid, verify=False)
        pdf_url = src.url

        filename = f"{pmid}.pdf"

        response = requests.get(pdf_url)
        if response.status_code == 200:
            # Save PDF
            with open(os.path.join(data / "pdfs", filename), "wb") as pdf_file:
                pdf_file.write(response.content)
            print(f"Downloaded {filename}")
        else:
            print(f"Failed to download {filename}")
    except Exception as e:
        print(f"Error for PMID {pmid}: {e}")


if __name__ == "__main__":
    # Create a Pool of 4 worker processes
    with Pool(4) as pool:
        pool.map(download_pdf, pmids)

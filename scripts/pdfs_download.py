import os
import requests
import pandas as pd
import multiprocessing
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from dotenv import load_dotenv

# .env variables
load_dotenv()
headers = {"User-Agent": os.getenv("USER_AGENT")}

DATA_PATH = Path("delme_data")
URLS_FILE_PATH = DATA_PATH / "oa_urls.csv"
ERROR_LOG_FILE_PATH = DATA_PATH / "pdfs_download_error.csv"


def is_pdf_url(url):
    try:
        session = requests.Session()
        response = session.get(
            url, headers=headers, stream=True, allow_redirects=True
        )
        response.raise_for_status()

        # Check if content type is PDF
        if "application/pdf" in response.headers.get("content-type", ""):
            return url

        # Check if the page contains a link to a PDF
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)

        for link in links:
            link_url = urljoin(url, link["href"])
            if link_url.endswith(".pdf"):
                return link_url

        return False

    except requests.exceptions.RequestException as e:
        print(e)
        return False


def download_pdf(url, download_folder, filename):
    try:
        session = requests.Session()
        response = session.get(
            url, headers=headers, stream=True, allow_redirects=True
        )
        response.raise_for_status()

        full_path = os.path.join(download_folder, filename)
        with open(full_path, "wb") as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                pdf_file.write(chunk)

        # print(f"Downloaded: {full_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(e)
        return False


def process_urls_chunk(chunk, download_folder, error_file):
    for url, pmid in chunk:
        pdf_url = is_pdf_url(url)
        if pdf_url:
            filename = f"{pmid}.pdf"
            if download_pdf(pdf_url, download_folder, filename):
                print(f"PDF found and downloaded from: {pdf_url}")
            else:
                with open(error_file, "a") as log_file:
                    log_file.write(f"{pmid}, {url}\n")
        else:
            with open(error_file, "a") as log_file:
                log_file.write(f"{pmid}, {url}\n")


if __name__ == "__main__":
    download_folder = DATA_PATH / "pdfs"
    os.makedirs(download_folder, exist_ok=True)

    # We try downloading if pdf is not already in folder
    oa_df = pd.read_csv(URLS_FILE_PATH)
    pdf_pmids = [
        int(pdf_file.strip(".pdf"))
        for pdf_file in os.listdir(download_folder)
        if pdf_file.endswith(".pdf")
    ]
    oa_df = oa_df[~oa_df["PMID"].isin(pdf_pmids)]
    urls = oa_df["oa_url"]
    pmids = oa_df["PMID"]

    # Split URLs and PMIDs into chunks
    num_processes = 4
    chunk_size = len(urls) // num_processes
    url_chunks = [
        list(zip(urls[i : i + chunk_size], pmids[i : i + chunk_size]))
        for i in range(0, len(urls), chunk_size)
    ]

    # Create a pool of processes
    pool = multiprocessing.Pool(processes=num_processes)

    # Process the URL chunks in parallel
    results = []
    for chunk in url_chunks:
        result = pool.apply_async(
            process_urls_chunk, (chunk, download_folder, ERROR_LOG_FILE_PATH)
        )
        results.append(result)
    pool.close()
    pool.join()

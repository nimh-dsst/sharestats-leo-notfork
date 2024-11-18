import gzip
import json
import os
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Uncomment for single thread debugging
from tqdm import tqdm

# .env variables
load_dotenv()
headers = {"User-Agent": os.getenv("USER_AGENT")}

DATA_PATH = Path("./2024_all_ics")
FILTERED_PMID_FILE_PATH = DATA_PATH / "pmids_articles_2024.csv"
OUTPUT_FILE_PATH = DATA_PATH / "openalex-snapshot_2024/works"
jsonOutput_file = OUTPUT_FILE_PATH / "calls.jsonl.gz"
failed_file = DATA_PATH / "openalex_api_error.txt"

# create output folder if it doesn't exist
os.makedirs(OUTPUT_FILE_PATH, exist_ok=True)

pmid_df = pd.read_csv(FILTERED_PMID_FILE_PATH)
pmids = pmid_df["PMID"].astype("Int64").unique()

pmid_url = "https://api.openalex.org/works/pmid:{}?mailto=lawrimorejg@nih.gov"
doi_url = "https://api.openalex.org/works/https://doi.org/{}"
failed_calls: list = []
max_retries: int = 3


def process_pmid(pmid):
    retries = 0
    time.sleep(0.05)
    if pd.isna(pmid):
        return
    else:
        url = pmid_url.format(pmid)
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                json_data = response.json()
                json_line = json.dumps(json_data) + "\n"
                return json_line
            else:
                # print(f"Failed to fetch data for {url}. Retrying...")
                retries += 1
                time.sleep(1)  # Wait before retrying
        except Exception:
            continue

    if retries == max_retries:
        print(f"Failed to fetch data for {url} after {max_retries} retries.")
        with open(failed_file, "w") as failed_calls_file:
            failed_calls_file.write(url + "\n")


if __name__ == "__main__":
    # Adjust number according to cores available
    # TODO: should be a better way to indicate num cores
    # with Pool(processes=4) as pool:
    #     results = pool.map(process_pmid, pmids)

    # Uncomment for debugging on single thread
    results = []
    for pmid in tqdm(pmids):
        result = process_pmid(pmid=pmid)
        results.append(result)

    # Write successful results to the output file
    with gzip.open(jsonOutput_file, "w") as outfile:
        for result in results:
            if result:
                outfile.write(result.encode("utf-8"))

    print(f"Process completed. Check {failed_file} for pending calls.")

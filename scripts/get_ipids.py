import csv
import os
import re
from pathlib import Path
from time import sleep

import requests

from annual_parser import parse_annual_ic_pubs

"""
Scrapes ipids with post requests
Saves or appends to single csv: IC, YEAR, IPID
error_file_path only for most recent errors
"""
data_path = Path("./2024_all_ics")
csv_file_path = data_path / "ipids.csv"
error_file_path = data_path / "get_ipids_error.txt"
# create output folder if it doesn't exist
os.makedirs(data_path, exist_ok=True)

ICs = [
    "CC",
    "CIT",
    "NCATS",
    "NCCIH",
    "NCI",
    "NEI",
    "NHGRI",
    "NHLBI",
    "NIA",
    "NIAAA",
    "NIAID",
    "NIAMS",
    "NIBIB",
    "NICHD",
    "NIDA",
    "NIDCD",
    "NIDCR",
    "NIDDK",
    "NIEHS",
    "NIGMS",
    "NIMH",
    "NIMHD",
    "NINDS",
    "NINR",
    "NLM",
]

oldest_year_data = 2024
most_recent_year_data = 2024

# lines that already exist in the CSV
existing_lines = []
header = None
if csv_file_path.exists():
    with open(csv_file_path, "r") as existing_file:
        csv_reader = csv.reader(existing_file)
        header = next(csv_reader, None)
        for row in csv_reader:
            existing_lines.append(row)

with open(csv_file_path, "a", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    if not header:
        csv_writer.writerow(["IC", "YEAR", "IPID"])

    for ic in ICs:
        for searchyear in range(oldest_year_data, most_recent_year_data + 1):
            # line below can be used to only scrape
            # if data is not in csv already
            # any(row[:2] == [IC, str(searchyear)] for
            # row in existing_lines[:2])
            print(f"Getting IPID {ic} {searchyear}")
            try:
                sleep(0.5)
                response = parse_annual_ic_pubs(str(searchyear), ic)
                response.raise_for_status()

                ipid_numbers = re.findall(r"ipid=(\d+)", response.text)
                unique_ipids = list(set(ipid_numbers))

                # add IC, Year, IPID to CSV, avoiding duplicates
                for ipid in unique_ipids:
                    row = [ic, str(searchyear), ipid]
                    if row not in existing_lines:
                        csv_writer.writerow(row)
                        existing_lines.append(row)
                print(f"{ic}: {len(unique_ipids)} IPIDs")

            except requests.exceptions.RequestException as e:
                print(f"Error for {ic}: {e}")
                with open(error_file_path, "a") as error_file:
                    error_file.write(f"{ic}\n")
            except Exception as e:
                print(f"Error occurred for {ic}: {e}")
                with open(error_file_path, "a") as error_file:
                    error_file.write(f"{ic}\n")

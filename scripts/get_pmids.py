import logging
import re
import sys
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# .env variables
"""
Needs ipids.csv, run get_ipids.py to generate
Scrapes reports in search of PubMedIDs
Saves or appends to single csv: IPID, PI, PMID, DOI, PROJECT
"""
DATA_PATH = Path("./2024_all_ics")
assert DATA_PATH.exists()
IPID_FILE_PATH = DATA_PATH / "ipids_2024.csv"
PMID_FILE_PATH = DATA_PATH / "pmids_2024.csv"
ERROR_LOG_FILE_PATH = DATA_PATH / "get_pmids_error_2024.txt"
ERROR_LOG_FILE_PATH.touch(exist_ok=True)

logging.basicConfig(
    filename=ERROR_LOG_FILE_PATH,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Check if we already have a pmid file
# Otherwise, create one with the headers
if PMID_FILE_PATH.exists():
    pmid_df = pd.read_csv(PMID_FILE_PATH)
else:
    pmid_df = pd.DataFrame(columns=["IPID", "PI", "PMID", "DOI", "PROJECT"])
    pmid_df.to_csv(PMID_FILE_PATH, index=False)
# Check if we have ipids.csv, necessary in this script
if not IPID_FILE_PATH.exists():
    print(f"{IPID_FILE_PATH} does not exist, run get_ipids.py to generate")
    sys.exit(1)
ipid_df = pd.read_csv(IPID_FILE_PATH)


# TODO: will a simple get request with interpolated IPID work here? YEP!

for IC, year in (
    ipid_df[["IC", "YEAR"]].drop_duplicates().itertuples(index=False)
):
    print(f"Parsing {IC} {year}")
    ic_year_ipids = ipid_df[(ipid_df["IC"] == IC) & (ipid_df["YEAR"] == year)]
    ipids = list(ic_year_ipids["IPID"])
    # don't query ipids we already have:
    ipids = [ipid for ipid in ipids if ipid not in pmid_df["IPID"].tolist()]

    # loop over intramural project IDs
    for i, ipid in enumerate(ipids):
        print(f"IPID {i+1} of {len(ipids)}: {ipid}")
        # report url
        url = ipid_url = (
            "https://intramural.nih.gov/search/searchview.taf?"
            + f"ipid={ipid}&nidbreload=true"
        )

        try:
            # get the html for the report
            page = requests.get(url)
            page.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request Error - IPID {ipid}: {e}\n")
            continue

        # soup object
        soup = BeautifulSoup(page.text, "html.parser")

        # report code / PROJECT
        contentlabel_div = soup.find("div", class_="contentlabel")
        if contentlabel_div:
            project = contentlabel_div.text.replace("  ", " ")
        project = project.split()[1]

        # PIs
        headings = soup.findAll("div", class_="headinggrid")
        PIs = []
        valid_listings_for_pis = [
            "Lead Investigator",
            "Principal Investigator",
            "Core Lead",
            "Lead Investigators",
            "Principal Investigators",
            "Core Leads",
        ]
        # looks like the structure of the
        for head in headings:
            label = head.text.strip()
            label = re.sub(r"[^\w\s]", "", label)
            if label in valid_listings_for_pis:
                raw_name = head.find_next("div", attrs={"class": "pigrid"})
                for div in raw_name.find_all("div"):
                    div_text: str = div.text.strip()
                    if not div_text.startswith("IRP") and len(div_text) > 0:
                        if "\n" in div_text:
                            test_text: str = div_text.split("\n")[0].strip()
                        else:
                            test_text = div_text.strip()
                    PIs.append(test_text)
        # If no PIs, log and check later for cause
        if not PIs:
            logging.error(f"No PIS found for - IPID {ipid}\n")
            continue

        # PubMedIDs and DOIs
        """
        not all publications in the reports have a PubMedID
        and not all have a DOI (even if it exists)
        """
        publications = soup.findAll("div", attrs={"class": "publistgrid"})
        # looks like the structure of the HTML has changed
        # each publication has a publistgrid div followed by
        # a pubmedlinksgrid div. Inside the pubmedlinks grid
        # are a showlinkpmid div and a showlinkpmcid div. These
        # two div elements can contain &nbsp instead of an a href element
        pmid_pattern = r"pubmed/(\d+)"
        # from regex101, tested on 2019-2022 data
        doi_pattern = r'(10[.]\d{4,}[^\s"/<>]*/[^\s"<>]+)'
        pmid_lst = []
        doi_lst = []
        for publication in publications:
            doi_match = re.search(doi_pattern, publication.text)
            if doi_match:
                doi = doi_match.group()
            else:
                doi = ""
            pubmedlinksgrid = publication.find_next(
                "div", attrs={"class": "pubmedlinksgrid"}
            )
            if pubmedlinksgrid:
                pmid_tag = pubmedlinksgrid.find(
                    "div", attrs={"class": "showlinkpmid"}
                )
                anchor = pmid_tag.find("a")
                if anchor:
                    pmid_match = re.search(pmid_pattern, anchor.attrs["href"])
                    if pmid_match:
                        pmid = pmid_match.group(1)
                    else:
                        pmid = ""
                else:
                    pmid = ""
            else:
                pmid = ""
            doi_lst.append(doi)
            pmid_lst.append(pmid)

        current_ipid_rows: dict = {
            "IPID": [],
            "PI": [],
            "PMID": [],
            "DOI": [],
            "PROJECT": [],
        }

        for pi in PIs:
            for pmid, doi in zip(pmid_lst, doi_lst):
                if (pmid, doi) == ("", ""):
                    continue
                if pmid:
                    pmid = int(pmid)
                current_ipid_rows["IPID"].append(int(ipid))
                current_ipid_rows["PI"].append(pi)
                current_ipid_rows["PMID"].append(pmid)
                current_ipid_rows["DOI"].append(doi)
                current_ipid_rows["PROJECT"].append(project)

        current_ipid_df = pd.DataFrame(current_ipid_rows)
        pmid_df = pd.concat([pmid_df, current_ipid_df], ignore_index=True)
    # Save after all reports for given IC, YEAR
    pmid_df.drop_duplicates(inplace=True)
    pmid_df.to_csv(PMID_FILE_PATH, index=False)

import re
import os
import sys
import logging
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
# .env variables
load_dotenv()
headers = {'user-agent': os.getenv('USER_AGENT')}
'''
Needs ipids.csv, run get_ipids.py to generate
Scrapes reports in search of PubMedIDs
Saves or appends to single csv: IPID, PI, PMID, DOI, PROJECT
'''
DATA_PATH = Path('../2023data')
IPID_FILE_PATH = DATA_PATH / 'pmids.csv'
PMID_FILE_PATH = DATA_PATH / 'pmids2023.csv'
ERROR_LOG_FILE_PATH = DATA_PATH / 'get_pmids_error.txt'

logging.basicConfig(
    filename=ERROR_LOG_FILE_PATH,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Check if we already have a pmid file
# Otherwise, create one with the headers
if PMID_FILE_PATH.exists():
    pmid_df = pd.read_csv(PMID_FILE_PATH)
else:
    pmid_df = pd.DataFrame(columns=['PI', 'PMID', 'DOI', 'PROJECT'])
    pmid_df.to_csv(PMID_FILE_PATH, index=False)
# Check if we have ipids.csv, necessary in this script
if not IPID_FILE_PATH.exists():
    print(f"{IPID_FILE_PATH} does not exist, run get_ipids.py to generate")
    sys.exit(1)
ipid_df = pd.read_csv(IPID_FILE_PATH)

projects = ipid_df['PROJECT'].str.replace(r'-\d+', '', regex=True).unique()

URL_ROOT = "https://intramural.nih.gov/search/onereport.taf"

for num, proj in enumerate(projects):
    print(f'Parsing {proj} - {num+1}/{len(projects)}')

    d = {'code': proj[:2], 'project': proj[2:8], 'year': 2023}
    # print(d)
    try:
        # get the html for the report
        page = requests.post(URL_ROOT,
                             data=d,
                             headers=headers
                             )
        page.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request Error - {proj}: {e}\n")
        continue

    try:
        # write page.text to a text file
        with open(f'{proj}.txt', 'w') as file:
            file.write(page.text)
        # soup object
        soup = BeautifulSoup(page.text, 'html.parser')

        # report code / PROJECT
        contentlabel_div = soup.find('div', class_='contentlabel')
        project = contentlabel_div.text.replace('  ', ' ')
        project = project.split()[1]

        # PIs
        headings = soup.findAll('span', class_='headings')
        PIs = []
        valid_listings_for_pis = ['Lead Investigator', 'Principal Investigator', 'Core Lead',
                                  'Lead Investigators', 'Principal Investigators', 'Core Leads']
        for head in headings:
            label = head.text.strip()
            label = re.sub(r'[^\w\s]', '', label)
            if label in valid_listings_for_pis:
                names = head.parent.parent.findNext('tr').findChildren('td', attrs={'class': 'showname'})
                [PIs.append(nn.text.replace('  ', ' ').split('\n')[0]) for nn in names]
        # If no PIs, log and check later for cause
        if not PIs:
            logging.error(f"No PIS found for - Project {proj}\n")
            continue

        # PubMedIDs and DOIs
        '''
        not all publications in the reports have a PubMedID
        and not all have a DOI (even if it exists)
        '''
        pmids = soup.findAll('div', attrs={'class': 'publisting'})
        pmid_pattern = r'pubmed/(\d+)'
        pmid_lst = [
            re.search(pmid_pattern, str(element)).group(1)
            if re.search(pmid_pattern, str(element))
            else ''
            for element in pmids
        ]
        dois = soup.findAll('div', attrs={'class': 'publisting'})
        doi_pattern = r'(10[.]\d{4,}[^\s"/<>]*/[^\s"<>]+)'  # from regex101, tested on 2019-2022 2023data
        doi_lst = [
            re.search(doi_pattern, element.text).group(1)
            if re.search(doi_pattern, element.text)
            else ''
            for element in dois
        ]

        current_ipid_rows = {
            'PI': [],
            'PMID': [],
            'DOI': [],
            'PROJECT': []
        }

        for pi in PIs:
            for (pmid, doi) in zip(pmid_lst, doi_lst):
                if (pmid, doi) == ('', ''):
                    continue
                if pmid:
                    pmid = int(pmid)
                current_ipid_rows['PI'].append(pi)
                current_ipid_rows['PMID'].append(pmid)
                current_ipid_rows['DOI'].append(doi)
                current_ipid_rows['PROJECT'].append(project)

        current_ipid_df = pd.DataFrame(current_ipid_rows)
        pmid_df = pd.concat([pmid_df, current_ipid_df], ignore_index=True)

        # Save after all reports for given IC, YEAR
        pmid_df.drop_duplicates(inplace=True)
        pmid_df.to_csv(PMID_FILE_PATH, index=False)

    except:
        logging.error(f"No reports for: {proj}\n")
        continue

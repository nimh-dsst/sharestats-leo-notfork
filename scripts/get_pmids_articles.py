import os
from pathlib import Path
from time import sleep

import eutils  # type: ignore
import pandas as pd
from dotenv import load_dotenv
from metapub.cache_utils import get_cache_path  # type: ignore
from metapub.pubmedarticle import PubMedArticle  # type: ignore

"""
PubMed has a list of types for each publication.
This code fetches the types of each publication in pmids.csv
and generates pmids_articles.csv, removing the types:
['Review', 'Comment', 'Editorial', 'Published Erratum']

one_hot_types.csv is also produced
each column is an existing type
each row is a publication
the cells are bools indicating which type is a pub
"""

DATA_PATH: Path = Path(r"./2024_all_ics")
PMID_FILE_PATH: Path = DATA_PATH / "pmids_2024.csv"
ONE_HOT_FILE_PATH: Path = DATA_PATH / "one_hot_types_2024.csv"
FILTERED_PMID_FILE_PATH: Path = DATA_PATH / "pmids_articles_2024.csv"
ERROR_FILE_PATH: Path = DATA_PATH / "get_pmids_articles_error_2024.txt"
MAX_RETRIES: int = 10

load_dotenv()  # Import NCBI_API_KEY before loading PubMedFetcher

df = pd.read_csv(PMID_FILE_PATH)
pubtypes_lst_of_dict = []
pmids = []
qs = eutils.QueryService(
    email=os.getenv("NCBI_EMAIL"),
    api_key=os.getenv("NCBI_API_KEY"),
    cache=get_cache_path(),
)

for i, pmid in enumerate(df["PMID"].astype("Int64").unique()):
    print(f"{i+1} of {len(df['PMID'].unique())} PMIDS")
    attempts: int = 0
    retry: bool = True
    while retry:
        try:
            result = qs.efetch({"db": "pubmed", "id": pmid})
            pma = PubMedArticle(result)
            sleep(0.1)
            row = pma.publication_types
            pubtypes_lst_of_dict.append(row)
            pmids.append(pmid)
            assert len(pubtypes_lst_of_dict) == len(pmids)
            retry = False
            print("\tsuccess!")
        except eutils.EutilsNCBIError as e:
            attempts += 1
            print("\tretrying...")
            if attempts == MAX_RETRIES:
                retry = False
                with open(ERROR_FILE_PATH, "a") as f:
                    f.write(f"FINAL FAIL: {pmid}: {e}\n")
        except eutils.EutilsError as e:
            with open(ERROR_FILE_PATH, "a") as f:
                f.write(f"{pmid}: {e}\n")

all_values = set()
for d in pubtypes_lst_of_dict:
    all_values.update(d.values())

data = []
for d in pubtypes_lst_of_dict:
    row_data = {value: value in d.values() for value in all_values}
    data.append(row_data)

one_hot_df = pd.DataFrame(data)
one_hot_df = one_hot_df.fillna(False)
one_hot_df["PMID"] = pmids
one_hot_df.to_csv(ONE_HOT_FILE_PATH, index=False)

remove_cols = ["Review", "Comment", "Editorial", "Published Erratum"]

# code fails on small test cases where remove_cols values are not present
remove_cols = list(set(remove_cols).intersection(all_values))

article_pmid = one_hot_df[~one_hot_df[remove_cols].any(axis=1)]["PMID"]
opendata_articles = df[df["PMID"].isin(article_pmid)]
opendata_articles.to_csv(FILTERED_PMID_FILE_PATH, index=False)

import pandas as pd
from pathlib import Path

DATA_PATH = Path("2024_all_ics")
IPID_IC_CSV = DATA_PATH / "ipids_2024.csv"
PMID_CSV = DATA_PATH / "pmids_2024.csv"
PMID_ARTICLES_CSV = DATA_PATH / "pmids_articles_2024.csv"
RTRANSPARENT_CSV = DATA_PATH / "data_code_rtransparent.csv"

ipid_df = pd.read_csv(IPID_IC_CSV)
pmid_df = pd.read_csv(PMID_CSV)
pmid_article_df = pd.read_csv(PMID_ARTICLES_CSV)
transparent_df = pd.read_csv(RTRANSPARENT_CSV)

pmid_ic_year_df = pmid_article_df.merge(ipid_df, on="IPID", how="inner")
pivot_df = pmid_ic_year_df.merge(
    transparent_df, left_on="PMID", right_on="article", how="inner"
)
pivot_df["IPID"] = pivot_df["IPID"].astype("Int64")
pivot_df["PMID"] = pivot_df["PMID"].astype("Int64")
pivot_df.drop("article", axis=1, inplace=True)

pivot_df.to_csv(DATA_PATH / "2019-2022_all_ICs.csv", index=False)

countUnique = pivot_df.groupby("IC")["PMID"].nunique()
pmidopendata = (
    pivot_df[pivot_df["is_open_data"]].groupby("IC")["PMID"].nunique()
)
pivot = pd.concat([countUnique, pmidopendata], axis=1)
pivot.columns = ["unique", "open_data"]
pivot.reset_index(inplace=True)
pivot["%"] = round(100 * pivot["open_data"] / pivot["unique"], 2)
final_row = {
    "IC": "Grand Total",
    "unique": pivot_df["PMID"].nunique(),
    "open_data": pivot_df[pivot_df["is_open_data"]]["PMID"].nunique(),
    "%": round(pivot["%"].mean(), 2),
}
pivot = pd.concat([pivot, pd.DataFrame([final_row])], ignore_index=True)
pivot.to_csv(DATA_PATH / "2024_all_ics_parsed_via_metapub.csv", index=False)

# print(len(pmid_df['PMID'].unique()))
# print(len(pmid_article_df['PMID'].unique()))

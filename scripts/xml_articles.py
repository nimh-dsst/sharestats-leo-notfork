import pandas as pd
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import tarfile
from io import BytesIO
from dotenv import load_dotenv
import os
import shutil

load_dotenv()
headers = {"user-agent": os.getenv("USER_AGENT")}

data_path = Path("delme_data")
csv_files_path = data_path / "test/ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/"
pmids_path = data_path / "pmids_articles.csv"
download_path = data_path / "downloaded_xml"
download_path.mkdir(exist_ok=True)

pmid_df = pd.read_csv(pmids_path)

web_directory_urls = [
    "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/oa_comm/xml/",
    "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/oa_noncomm/xml/",
    "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_bulk/oa_other/xml/",
]


# Function to filter CSV files based on PMID and exclude existing files in download_path
def filter_csv_files(csv_files_path, pmid_df, download_path):
    filtered_rows = []

    # List existing files in subdirectories of download_path before the loop
    existing_files = set()
    for root, _, files in os.walk(download_path):
        relative_path = os.path.relpath(root, download_path)
        # Exclude the "." folder
        if relative_path != ".":
            existing_files.add(relative_path)
    print(existing_files)
    for csv_file in csv_files_path.rglob("*.csv"):
        csv_data = pd.read_csv(csv_file)
        relative_path = csv_file.relative_to(csv_files_path)
        relative_path_str = (
            str(relative_path)
            .split("/")[-1]
            .replace(".filelist.csv", ".tar.gz")
        )

        # Exclude rows where "Article File" matches existing files in download_path
        filtered_data = csv_data[(csv_data["PMID"].isin(pmid_df["PMID"]))]

        if not filtered_data.empty:
            filtered_data["Relative Path"] = relative_path_str
            filtered_rows.append(filtered_data)

    final_result = pd.concat(filtered_rows, ignore_index=True)
    final_result = final_result[["Article File", "PMID", "Relative Path"]]

    # Move filter_condition here to filter the concatenated DataFrame
    filter_condition = ~final_result["Article File"].apply(
        lambda x: any(existing_file in x for existing_file in existing_files)
    )
    final_result = final_result[filter_condition]

    return final_result


# download .tar.gz files from web directory and extract only needed xml
def extract_and_keep_files(web_directory_url, download_path, unique_filenames):
    response = requests.get(web_directory_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        tar_gz_links = [
            a["href"]
            for a in soup.find_all("a")
            if a["href"].endswith(".tar.gz")
        ]
        for tar_gz_link in tar_gz_links:
            tar_gz_filename = tar_gz_link
            if tar_gz_filename in unique_filenames:
                tar_gz_url = web_directory_url + tar_gz_link
                print(tar_gz_url)
                tar_gz_content = requests.get(
                    tar_gz_url, headers=headers
                ).content
                with open(
                    download_path / tar_gz_filename, "wb"
                ) as tar_gz_file:
                    tar_gz_file.write(tar_gz_content)
                    # Uncompress the downloaded .tar.gz file
                    with tarfile.open(
                        fileobj=BytesIO(tar_gz_content), mode="r:gz"
                    ) as tar:
                        # List of files in the tar.gz archive
                        files_in_tar = tar.getnames()
                        print("found, to keep")
                        print(len(files_in_tar), files_in_tar[:5])
                        # Filter files based on Article File column
                        files_to_keep_names = [
                            f
                            for f in files_in_tar
                            if f in files_to_keep["Article File"].tolist()
                        ]
                        print(
                            len(files_to_keep_names), files_to_keep_names[:5]
                        )
                        # Extract and keep files in the Article File column
                        for file in files_to_keep_names:
                            tar.extract(file, path=download_path)
                        # Remove the remaining .tar.gz file after extraction
                        os.remove(download_path / tar_gz_filename)


files_to_keep = filter_csv_files(csv_files_path, pmid_df, download_path)
print(f"{len(files_to_keep)} files needed")
print(files_to_keep["Relative Path"].unique())
# Extract and keep files in the "Article File" column and delete the rest
for web_directory_url in web_directory_urls:
    extract_and_keep_files(
        web_directory_url,
        download_path,
        files_to_keep["Relative Path"].unique(),
    )

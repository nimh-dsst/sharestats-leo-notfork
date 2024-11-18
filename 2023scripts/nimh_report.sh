#!/bin/bash

export wd="./2023data/"

csvgrep -c 4 -r '^MH' ${wd}/pmids2023.csv > ${wd}/pmids2023_nimh.csv
csvstat --count ${wd}/pmids2023_nimh.csv # 332
csvcut -C 1,4 ${wd}pmids2023_nimh.csv |csvsort | uniq |csvstat --count # 273

csvgrep -c 4 -r '^MH' ${wd}/pmids2023_articles.csv > ${wd}/pmids2023_articles_nimh.csv
csvstat --count ${wd}/pmids2023_articles_nimh.csv # 276
csvcut -C 1,4 ${wd}/pmids2023_articles_nimh.csv |csvsort | uniq |csvstat --count  # 224

sed s/"https://doi.org/"/""/g 2023data/Manually_labelled_pubs_NIMH_IRP_2023.csv |
csvcut -c 1

# Current input file for StreamLit app is all_ICs_2019-2023_fromLeo-2024-01-31.csv
# MVP for Maryland: 
- Total number of pubs scraped for each PI and whole IC 
    - pmids.csv has an entry for every pub reported regardless of whether or not it has a PMID, DOI, or
      contains dat
    - NIMH 2023 Total: 333, les
- Total number of pubs w/data for each PI and whole IC (need to update)
- Total number and percentage of pubs w/open data for each PI and whole IC

# Goal 1: 

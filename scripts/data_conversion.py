from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
load_dotenv()  # Import NCBI_API_KEY before loading PubMedFetcher
from metapub.pubmedfetcher import PubMedFetcher
paths = [
    ['2023data/pmids2023_articles.csv', '2023data/title_journal2023.csv'],
    ['data/pmids_articles.csv', 'data/title_journal19-22.csv']
]
df = pd.read_csv(paths[1][0])
pmids = df['PMID'].astype('Int64').unique()
data = {
    'pmid': [],
    'title': [],
    'journal': []
}

for i, pmid in enumerate(pmids):
    print(f'{i+1} of {len(pmids)}')
    try:
        pma = PubMedFetcher().article_by_pmid(pmid)
    except:
        print('******')
        print(pmid)
        data['pmid'].append(pmid)
        data['title'].append('')
        data['journal'].append('')
        continue
    data['pmid'].append(pmid)
    data['title'].append(pma.title)
    data['journal'].append(pma.journal)
    #print(pma.title)
    #print(pma.journal)
    #print('**************************')

df_tj = pd.DataFrame(data)
df_tj.to_csv(paths[1][1], index=False)

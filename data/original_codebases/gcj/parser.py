## this is a parser for google code jam csv 
## that extracts python files separately for each task

import pandas as pd
import os
import re

df = pd.read_csv('gcj2020.csv') ## insert here any year gcj csv from github.com/Jur1cek/gcj-dataset

mask_py = df['full_path'].str.endswith('.PYTHON') | \
          df['full_path'].str.endswith('.PYTHON3')  | \
          df['full_path'].str.endswith('.PYPY2') 

df_py = df[mask_py].copy()

df_last = df_py.drop_duplicates(subset=['task', 'username'], keep='last') # remove it for not only last sumbission of user

CODE_COL = 'flines'

BASE_DIR = 'data'

for task, grp in df_last.groupby('task'):
    task_dir = os.path.join(BASE_DIR, str(task))
    os.makedirs(task_dir, exist_ok=True)

    for idx, row in grp.iterrows():
        safe_user = re.sub(r'[^0-9A-Za-z_-]', '_', str(row['username'])).replace("_", "#")
        filename = f"{safe_user}.py"
        path = os.path.join(task_dir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(row[CODE_COL])

print("parsed")


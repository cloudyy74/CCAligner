import lexical_analysis.pretty_printing as prpr
from launching import define_args
from shutil import rmtree
import os
import pandas as pd
from clone_detection.algorithm import CCalignerAlgorithm
from numpy import sign


def regulate_records(df):
    for i in range(len(df)):
        length1 = int(df.loc[i, 'end1']) - int(df.loc[i, 'start1'])
        length2 = int(df.loc[i, 'end2']) - int(df.loc[i, 'start2'])
        if length1 < length2 or (length1 == length2 and df.loc[i, 'start1'] > df.loc[i, 'start2']):
            df.loc[i, 'start1'], df.loc[i, 'start2'] = df.loc[i, 'start2'], df.loc[i, 'start1']
            df.loc[i, 'end1'], df.loc[i, 'end2'] = df.loc[i, 'end2'], df.loc[i, 'end1']
            df.loc[i, 'dir1'], df.loc[i, 'dir2'] = df.loc[i, 'dir2'], df.loc[i, 'dir1']
            df.loc[i, 'name1'], df.loc[i, 'name2'] = df.loc[i, 'name2'], df.loc[i, 'name1']
    return df.drop_duplicates()




args = define_args()

codebase_loc = args.codebase_loc
language = args.lang
if language == 'python':
    lang_ext = '.py'
elif language == 'java':
    lang_ext = '.java'

elif language == 'c-sharp':
    lang_ext = '.cs'

pretty_loc = "./data/normalized_codebases/"
if os.path.exists(pretty_loc):
    rmtree(pretty_loc)

if language == 'python':
    pp = prpr.PrettyPrinterPy(codebase_loc, pretty_loc, language)
elif language == 'java':
    pp = prpr.PrettyPrinterJava(codebase_loc, pretty_loc, language)
elif language == 'c-sharp':
    pp = prpr.PrettyPrinterJava(codebase_loc, pretty_loc, language)

pp.pretty_print()

final_dir = pretty_loc + codebase_loc.split('/')[-1] + '/' + 'obfuscated'

cca = CCalignerAlgorithm(final_dir, lang_ext, 6, 1)
pairs = cca.run_algo()

prpr.print_with_time('Algorithm plowed')

clones = pd.DataFrame({'dir1': pd.Series(dtype='str'),
                       'name1': pd.Series(dtype='str'),
                       'start1': pd.Series(dtype='int'),
                       'end1': pd.Series(dtype='int'),
                       'dir2': pd.Series(dtype='str'),
                       'name2': pd.Series(dtype='str'),
                       'start2': pd.Series(dtype='int'),
                       'end2': pd.Series(dtype='int'),
                       })

filtered_combinations = []

for file1, file2 in pairs:  # filters nested clones
    file1_info = file1.split('/')
    file2_info = file2.split('/')
    dir1 = file1_info[-3]
    dir2 = file2_info[-3]
    file_name1 = file1_info[-2] + lang_ext
    file_name2 = file2_info[-2] + lang_ext
    start_1, end_1 = file1_info[-1][:-len(lang_ext)].split('_')
    start_2, end_2 = file2_info[-1][:-len(lang_ext)].split('_')
    if start_1 > start_2:
        start_1, start_2 = start_2, start_1
        end_1, end_2 = end_2, end_1
    if not (dir1 == dir2 and file_name1 == file_name2 and
            sign(int(start_2) - int(start_1)) * sign(int(start_2) - int(end_1)) < 0):
        filtered_combinations.append([file1, file2])

for file1, file2 in filtered_combinations:  # writes list of clones into the dataframe
    dir1 = file1.split('/')[-3]
    dir2 = file2.split('/')[-3]
    file_name1 = file1.split('/')[-2] + lang_ext
    file_name2 = file2.split('/')[-2] + lang_ext
    start_1, end_1 = file1.split('/')[-1][:-len(lang_ext)].split('_')
    start_2, end_2 = file2.split('/')[-1][:-len(lang_ext)].split('_')
    clones.loc[len(clones)] = [dir1, file_name1, start_1, end_1, dir2, file_name2, start_2, end_2]

clones = regulate_records(clones)

clones.to_csv('clones.csv', header=False, index=False)
prpr.print_with_time('Check clones.csv out')

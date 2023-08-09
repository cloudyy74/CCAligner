import lexical_analysis.pretty_printing as prpr
from launching import define_args
from shutil import rmtree
import os
import pandas as pd
from clone_detection.algorithm import CCalignerAlgorithm


args = define_args()

codebase_loc = args.codebase_loc
language = args.lang
if language == 'python':
    lang_ext = '.py'
elif language == 'java':
    lang_ext = '.java'


pretty_loc = "./data/normalized_codebases/"
if os.path.exists(pretty_loc):
    rmtree(pretty_loc)

if language == 'python':
    pp = prpr.PrettyPrinterPy(codebase_loc, pretty_loc, language)
elif language == 'java':
    pp = prpr.PrettyPrinterJava(codebase_loc, pretty_loc, language)

pp.pretty_print()


final_dir = pretty_loc + codebase_loc.split('/')[-1] + '/' + 'obfuscated'

cca = CCalignerAlgorithm(final_dir, lang_ext, 6, 1)
pairs = cca.run_algo()

clones = pd.DataFrame({'dir_1': pd.Series(dtype='str'),
                       'file_name1': pd.Series(dtype='str'),
                       'start_line1': pd.Series(dtype='int'),
                       'end_line1': pd.Series(dtype='int'),
                       'dir_2': pd.Series(dtype='str'),
                       'file_name2': pd.Series(dtype='str'),
                       'start_line2': pd.Series(dtype='int'),
                       'end_line2': pd.Series(dtype='int'),
                       })

for file1, file2 in pairs:
    dir1 = file1.split('/')[-3]
    dir2 = file2.split('/')[-3]
    file_name1 = file1.split('/')[-2] + lang_ext
    file_name2 = file2.split('/')[-2] + lang_ext
    start_1, end_1 = file1.split('/')[-1][:-len(lang_ext)].split('_')
    start_2, end_2 = file2.split('/')[-1][:-len(lang_ext)].split('_')
    clones.loc[len(clones)] = [dir1, file_name1, start_1, end_1, dir2, file_name2, start_2, end_2]

clones.to_csv('clones.csv', header=False, index=False)

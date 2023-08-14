import lexical_analysis.pretty_printing as prpr
from launching import define_args
from shutil import rmtree
import os
import pandas as pd
from clone_detection.algorithm import CCalignerAlgorithm
import output_modification as om
from numpy import sign


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

pairs = om.filter_nested_clones(pairs, lang_ext)

clones_df = om.clones_list_to_df(pairs, lang_ext)

clones_df = om.regulate_records(clones_df)

om.sort_clones(clones_df)

clones_df.to_csv('clones.csv', header=False, index=False)
prpr.print_with_time('Check clones.csv out')

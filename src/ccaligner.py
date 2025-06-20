import os
from shutil import rmtree
import pandas as pd

import lexical_analysis.pretty_printing as prpr
import output_modification as om
from clone_detection.algorithm import CCalignerAlgorithm
from launching import define_args


def run_ccaligner(codebase_loc, language, pretty_loc = "./data/normalized_codebases/", theta = 0.6):
    if os.path.exists(pretty_loc):
        rmtree(pretty_loc)

    if language == 'python':
        lang_ext = '.py'
    elif language == 'java':
        lang_ext = '.java'
    elif language == 'c-sharp':
        lang_ext = '.cs'
    elif language == 'cpp':
        lang_ext = '.cpp'

    if language == 'python':
        pp = prpr.PrettyPrinterPy(codebase_loc, pretty_loc, language)
    else:
        pp = prpr.PrettyPrinterJava(codebase_loc, pretty_loc, language)
    pp.pretty_print()
    final_dir = pretty_loc + codebase_loc.split('/')[-1] + '/' + 'obfuscated'
    cca = CCalignerAlgorithm(final_dir, lang_ext, 6, 1, theta)
    pairs = cca.run_algo()
    prpr.print_with_time('Algorithm plowed')
    # pairs = om.filter_nested_clones(pairs, lang_ext)

    # clones_df = om.clones_list_to_df(pairs, lang_ext)

    # om.sort_clones(clones_df)

    # clones_df =
    # clones_df = om.regulate_records(clones_df)
    # clones_df.to_csv('clones.csv', header=False, index=False)

    #om.write_clone_list(pairs, lang_ext, 'clones.csv')


    om.write_clone_list_correct(codebase_loc, final_dir, pairs, lang_ext, 'clones.csv')

    prpr.print_with_time('Check clones.csv out')
    prpr.print_with_time('_' * 40)
    df_py = pd.read_csv("clones.csv", names=["dir1", 'name1', 'start1', 'end1', "dir2", 'name2', 'start2', 'end2'])

    om.only_biggest(df_py).to_csv("only_biggest.csv", index=False, header=False)

    #prpr.print_with_time('Check only_biggest.csv out')

    return pairs

args = define_args()

codebase_loc = args.codebase_loc
language = args.lang
theta = int(args.theta)/100
pairs = run_ccaligner(codebase_loc=codebase_loc, language=language, theta=theta)

print(len(pairs))


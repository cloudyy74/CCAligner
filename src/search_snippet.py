import os
from shutil import rmtree
import pandas as pd

import lexical_analysis.pretty_printing as prpr
import output_modification as om
from clone_detection.algorithm import CCalignerAlgorithm
from pathlib import Path

import argparse


def define_args():
    parser = argparse.ArgumentParser(description='Finds code clones candidates')
    parser.add_argument('-from', '-codebase_loc', help='enter location of codebase', dest='codebase_loc', required=True)
    parser.add_argument('-l', help='specify language of database you want to analyse', dest='lang', required=True)
    parser.add_argument('-theta', help='specify similarity', dest='theta', required=True)
    parser.add_argument('-index_name', help='place to load indexed codebase from', dest='index_name', required=True)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = define_args()

    codebase_loc = args.codebase_loc
    language = args.lang
    theta = int(args.theta) / 100
    index_file = Path(args.index_name)

    if language == 'python':
        lang_ext = '.py'
    elif language == 'java':
        lang_ext = '.java'
    elif language == 'c-sharp':
        lang_ext = '.cs'
    elif language == 'cpp':
        lang_ext = '.cpp'

    pretty_loc = "./data/normalized_codebases/"
    if os.path.exists(pretty_loc):
        rmtree(pretty_loc)

    if language == 'python':
        pp = prpr.PrettyPrinterPy(codebase_loc, pretty_loc, language)
    else:
        pp = prpr.PrettyPrinterJava(codebase_loc, pretty_loc, language)

    pp.pretty_print()

    final_dir = pretty_loc + codebase_loc.split('/')[-1] + '/' + 'obfuscated'

    cca = CCalignerAlgorithm(final_dir, lang_ext, 6, 1, theta)
    cca.index_codebase(index_file)

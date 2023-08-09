import lexical_analysis.pretty_printing as prpr
from launching import define_args
from shutil import rmtree
import os
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
for file1, file2 in pairs:
    file_name1 = file1.split('/')[-2] + '.java'
    file_name2 = file2.split('/')[-2] + '.java'
    fragment1 = file1.split('/')[-1][:-5]
    fragment2 = file2.split('/')[-1][:-5]
    if file_name1 != file_name2:
        print(f"{file_name1} and {file_name2} contain codeclone in lines {fragment1} and {fragment2} respectively")
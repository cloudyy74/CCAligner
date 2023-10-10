import time

import output_modification as om
from algo_launch import define_args
from clone_detection.algorithm import CCalignerAlgorithm


def print_with_time(message, to='log_4'):
    with open(to, 'a') as f:
        print(message, file=f)
        print(time.ctime(time.time()), file=f)



args = define_args()
codebase1 = args.codebase1
codebase2 = args.codebase2
cipher = codebase1.split('/')[-1] + "_" + codebase2.split('/')[-1]

log_file = './logs/' + cipher + '.log'
clonesfile = './clones/' + cipher + '.csv'
language = args.lang

if language == 'python':
    lang_ext = '.py'
elif language == 'java':
    lang_ext = '.java'
elif language == 'c-sharp':
    lang_ext = '.cs'
elif language == 'cpp':
    lang_ext = '.cpp'

print_with_time("_"*40, to=log_file)
print_with_time("Execution started", to=log_file)


cca = CCalignerAlgorithm(codebase1, lang_ext, mode=2)
cca.add_files(codebase2)
pairs = cca.run_algo()
print_with_time('Algorithm plowed', to=log_file)

pairs = om.filter_nested_clones(pairs, lang_ext)

clones_df = om.clones_list_to_df(pairs, lang_ext)

om.sort_clones(clones_df)

clones_df.to_csv(clonesfile, header=False, index=False)
print_with_time('Check clones out', to=log_file)
print_with_time('_'*40, log_file)




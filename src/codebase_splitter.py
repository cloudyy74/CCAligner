import os
from shutil import copytree

dir = "../data/normalized_codebases/6/obfuscated"
dir_dest = "../data/normalized_codebases/6/parts"
number_of_parts = 8

if not os.path.exists(dir_dest):
    os.mkdir(dir_dest)

list_of_big_dirs = []
for file in os.listdir(dir):
    d = os.path.join(dir, file)
    if os.path.isdir(d):
        list_of_big_dirs.append(d)

for i in range(number_of_parts):
    if not os.path.exists(os.path.join(dir_dest, str(i))):
        os.mkdir(os.path.join(dir_dest, str(i)))


for big_dir in list_of_big_dirs:
    for small_dir in os.listdir(big_dir):
        modulo = 0
        if small_dir.isnumeric():
            modulo = int(small_dir) % number_of_parts
        else:
            modulo = ord(small_dir[-1]) % number_of_parts
        if not os.path.exists(os.path.join(*[dir_dest, str(modulo), big_dir.split('/')[-1]])):
            os.mkdir(os.path.join(*[dir_dest, str(modulo), big_dir.split('/')[-1]]))
        copytree(os.path.join(big_dir, small_dir), os.path.join(*[dir_dest, str(modulo), big_dir.split('/')[-1], small_dir]))






from itertools import combinations

for pair in combinations(range(15), 2):
    print(f"python3 algo_run.py -d1 ../data/original_codebases/parts/{pair[0]} -l java -m 2 -d2 ../data/original_codebases/2/parts/{pair[1]} &")
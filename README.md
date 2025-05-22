# modCCAligner

This repo contains an implementation of modified CCAligner algorithm on Python, with support of Python, Java, C++ and C#.


You should have python 3.12, mmh3, numpy, pandas installed.

```
$ pip install -r requirements.txt
```

Example:

```
$ python3 ./src/ccaligner.py -from ./data/original_codebases/paper_example -l java -theta 60
$ python3 ./src/ccaligner.py -from ./data/original_codebases/codebase1 -l python -theta 60
```

Or you can use docker:

```
$ docker compose run --rm ccaligner -from ./data/original_codebases/paper_example -l java -theta 60
$ docker compose run --rm ccaligner -from ./data/original_codebases/codebase1 -l python -theta 60
```

Also this repo contains google code jam dataset parser in ./data/original_codebases/gcj

## Modification

It is not exactly an implementation of CCAligner, this tool contains a number of modifications and heuristics:

1. Report granularity is code blocks, instead of methods.
2. Indexing consists expanded information compared with original implementation, for the sake of space-time trade-off.

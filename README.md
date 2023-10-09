# modCCAligner

This repo contains an implementation of modified CCAligner algorithm on Python, with support of Python, Java, C++ and C#.



It is required to run 

``git clone https://github.com/tree-sitter/tree-sitter-python``

``git clone https://github.com/tree-sitter/tree-sitter-java``

``git clone https://github.com/tree-sitter/tree-sitter-c-sharp``

``git clone https://github.com/tree-sitter/tree-sitter-cpp``

in the project root before working.

And also you should have mmh3, numpy, pandas


Example:

``python3 ./src/ccaligner.py -from ./data/original_codebases/paper_example -l java -theta 60``

## Modification

It is not exactly an implementation of CCAligner, this tool contains a number of modifications and heuristics:

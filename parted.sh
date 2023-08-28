#!/bin/bash
date


for dir_number in 5 38 11 15 21 12 8 18 20 36 26 44 17 22 32 28 45 13 25 29 33 40 19 24 31 37 6 39 34 23 42 43 9 27 41 35 10 7 30 14 3 2 4 ; do

        python3 src/ccaligner.py -from ~/benchmark/BigCloneEval/ijadataset/bcb_reduced/"$dir_number" -l java -theta 60

        if [ -f "all_clones.csv" ]; then

          cat clones.csv >> all_clones.csv
        else
          cp clones.csv all_clones.csv
        fi
        cp clones.csv "clones${dir_number}"

        echo "$dir_number" >> log_4
        date
	echo "$dir_number"
done
date


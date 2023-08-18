#!/bin/bash
date

for dir_number in {5..15} {17..45} {2..3}; do
        python3 src/ccaligner.py -from $/benchmark/ijadataset/bcb_reduced/"$dir_number" -l java -theta 60

        if [ -f "all_clones.csv" ]; then

          cat clones >> all_clones.csv
        else
          cp clones all_clones.csv
        fi
        cp clones "clones${dir_number}"

        echo "$dir_number"
        date
done
date

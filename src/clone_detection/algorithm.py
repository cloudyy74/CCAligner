import glob
import time
# from joblib import Parallel, delayed
from itertools import combinations
from typing import List, Any

import mmh3
import json


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def print_with_time(message, to='log_4'):
    with open(to, 'a') as f:
        print(message, file=f)
        print(time.ctime(time.time()), file=f)


class CCalignerAlgorithm:
    clone_pair: List[Any]

    def __init__(self, codeblocks_dir, lang_ext, window_size=6, edit_distance=1, theta=0.6, mil=10, mode=1):
        self.mode = mode  # mode = 1 means full search, mode = 2 for only inter-project clones
        self.dir = codeblocks_dir
        self.q = window_size
        self.e = edit_distance
        self.theta = theta
        self.files = []
        self.mil = mil
        self.lang_ext = lang_ext
        for file in glob.glob(self.dir + "/**/*" + lang_ext, recursive=True):
            self.files.append(file)
        self.cand_map = dict()  # for hash of q-e-grams stores dict of blocks, and for each block stores number that
        # this hash gram has occurred
        self.lines_in = dict()  # for codeblock stores number of lines
        self.hash_set = dict()  # for codeblock stores set with hash of q-e-gram and i -- number of sliding window in
        # which this gram occurred
        self.cand_pair = dict()  # we store in cand_pair pairs of fragments as keys, and values are cardinality of
        # hashes_intersection
        self.cand_pair_list = list()
        self.clone_pair = list()

    def add_files(self, new_codeblocks_dir):
        for file in glob.glob(new_codeblocks_dir + "/**/*" + self.lang_ext, recursive=True):
            self.files.append(file)

    def process_hash_gram(self, k, file):
        """
        we call this function after collecting of all q-e-grams in particular window
        :param file:
        :param k: is a given hash of q-e-gram in file.
        :return:
        """
        if k not in self.cand_map:
            self.cand_map[k] = {file: 1}
        elif file not in self.cand_map[k]:
            self.cand_map[k][file] = 1
        else:
            self.cand_map[k][file] += 1

    def index_codeblock(self, file):
        with open(file, 'r') as f:
            lines = f.readlines()
        L = len(lines)
        self.lines_in[file] = L
        num_of_wndws = L - self.q + 1
        if num_of_wndws <= 0 or L < self.mil:
            return
        hash_sub_set = set()
        for win_start in range(num_of_wndws):
            window = lines[win_start: win_start + self.q]

            hash_grams_in_window = set()

            for h in combinations(window, self.q - self.e):
                k = mmh3.hash128("".join(h))
                hash_sub_set.add(str(k) + '|' + str(win_start))
                hash_grams_in_window.add(k)

            for k in hash_grams_in_window:
                self.process_hash_gram(k, file)

        self.hash_set[file] = hash_sub_set

    def verify_pair(self, f_m_f_n, upper_est_m, upper_est_n):
        f_m, f_n = f_m_f_n.split('|')
        num_win_m = self.lines_in[f_m] - self.q + 1
        num_win_n = self.lines_in[f_n] - self.q + 1

        if upper_est_m < self.theta * num_win_m and upper_est_n < self.theta * num_win_n:
            return False

        hashes_in_f_m = set(hash_pair.split('|')[0] for hash_pair in self.hash_set[f_m])
        hashes_in_f_n = set(hash_pair.split('|')[0] for hash_pair in self.hash_set[f_n])
        hashes_intersection = hashes_in_f_n.intersection(hashes_in_f_m)
        num_match_1 = len(
            set(hash_pair.split('|')[1] for hash_pair in self.hash_set[f_m] if
                hash_pair.split('|')[0] in hashes_intersection))
        num_match_2 = len(
            set(hash_pair.split('|')[1] for hash_pair in self.hash_set[f_n] if
                hash_pair.split('|')[0] in hashes_intersection))

        if num_match_1 >= self.theta * num_win_m or num_match_2 >= self.theta * num_win_n:
            return True
        return False

    def verify_pairs(self):
        while self.cand_pair:
            another_pair = self.cand_pair.popitem()
            hashable_pair_name = another_pair[0]
            upper_est_m, upper_est_n = another_pair[1]
            if self.verify_pair(hashable_pair_name, upper_est_m, upper_est_n):
                fragment1, fragment2 = hashable_pair_name.split("|")
                self.clone_pair.append([fragment1, fragment2])


    def get_coordinates_of_fragment(self, fragment_file_loc):
        file_name = fragment_file_loc.split('/')[-1]
        start, end = file_name[:-len(self.lang_ext)].split('_')
        return int(start), int(end)

    @staticmethod
    def get_codebase_of_fragment(fragment_file_loc):
        file = fragment_file_loc.split('/')[-4]
        return file

    @staticmethod
    def get_file_of_fragment(fragment_file_loc):
        file = fragment_file_loc.split('/')[:-1]
        return "".join(file)

    def are_fragments_nested(self, fragment_1, fragment_2):
        if self.get_file_of_fragment(fragment_1) != self.get_file_of_fragment(fragment_2):
            return False
        start1, end1 = self.get_coordinates_of_fragment(fragment_1)
        start2, end2 = self.get_coordinates_of_fragment(fragment_2)
        if start1 not in range(start2, end2) and start2 not in range(start1, end1):
            return False
        return True

    def update_candidates(self, hashable_pair_name, card_first, card_second):
        if hashable_pair_name not in self.cand_pair:
            self.cand_pair[hashable_pair_name] = [card_first, card_second]
        else:
            self.cand_pair[hashable_pair_name][0] += card_first
            self.cand_pair[hashable_pair_name][1] += card_second

    def are_fragments_from_different_codebases(self, fragment_1, fragment_2):
        """

        :rtype: bool
        """
        return self.get_codebase_of_fragment(fragment_1) != self.get_codebase_of_fragment(fragment_2)

    def is_pair_interesting(self, pair):
        if self.mode == 1:
            return not self.are_fragments_nested(pair[0], pair[1])
        else:
            return ((not self.are_fragments_nested(pair[0], pair[1])) and
                    self.are_fragments_from_different_codebases(pair[0], pair[1]))

    def index_codebase(self, name_of_index_file):
        """
        index and writes codebase in indexed form in json
        :return:
        """
        for file in self.files:
            self.index_codeblock(file)

        json_index = json.dumps(self.hash_set, indent=4, cls=SetEncoder)
        with open(name_of_index_file, 'w+') as outfile:
            outfile.write(json_index)



    def run_algo(self):
        for file in self.files:
            self.index_codeblock(file)
        print_with_time("Indexing done")
        for mapp in self.cand_map.values():
            if len(mapp) >= 2:
                for pair in combinations(list(mapp.keys()), 2):
                    if self.is_pair_interesting(pair):
                        first_in_pair = min(pair[0], pair[1]); card_first = mapp[first_in_pair]
                        second_in_pair = max(pair[0], pair[1]); card_second = mapp[second_in_pair]
                        hashable_pair_name = first_in_pair + '|' + second_in_pair
                        self.update_candidates(hashable_pair_name, card_first, card_second)
        print_with_time("Form candidates")

        self.verify_pairs()
        print_with_time("Verifying done")
        return self.clone_pair

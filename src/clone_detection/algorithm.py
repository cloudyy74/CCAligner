import glob
from typing import List, Any
#from joblib import Parallel, delayed
from itertools import combinations
import mmh3


class CCalignerAlgorithm:
    clone_pair: List[Any]

    def __init__(self, codeblocks_dir, lang_ext, window_size=6, edit_distance=1, theta=0.6):
        self.dir = codeblocks_dir
        self.q = window_size
        self.e = edit_distance
        self.theta = theta
        self.files = []
        self.lang_ext = lang_ext
        for file in glob.glob(self.dir + "/**/*" + lang_ext, recursive=True):
            self.files.append(file)
        self.cand_map = dict()
        self.lines_in = dict()
        self.hash_set = dict()
        self.cand_pair = set()
        self.cand_pair_list = list()
        self.clone_pair = list()

    def add_files(self, new_codeblocks_dir):
        for file in glob.glob(new_codeblocks_dir + "/**/*" + self.lang_ext, recursive=True):
            self.files.append(file)

    def index_codeblock(self, file):
        with open(file, 'r') as f:
            lines = f.readlines()
        L = len(lines)
        self.lines_in[file] = L
        num_of_wndws = L - self.q + 1
        if num_of_wndws <= 0:
            return
        hash_sub_set = set()
        for win_start in range(num_of_wndws):
            window = lines[win_start: win_start + self.q]
            for h in combinations(window, self.q - self.e):
                k = mmh3.hash128("".join(h))
                hash_sub_set.add(str(k) + '|' + str(win_start))
                if k in self.cand_map:
                    self.cand_map[k].add(file)
                else:
                    self.cand_map[k] = {file}
        self.hash_set[file] = hash_sub_set

    def verify_pair(self, f_m_f_n):
        f_m, f_n = f_m_f_n.split('|')
        hashes_in_f_m = set(hash_pair.split('|')[0] for hash_pair in self.hash_set[f_m])
        hashes_in_f_n = set(hash_pair.split('|')[0] for hash_pair in self.hash_set[f_n])
        hashes_intersection = hashes_in_f_n.intersection(hashes_in_f_m)
        num_match_1 = len(
            set(hash_pair.split('|')[1] for hash_pair in self.hash_set[f_m] if
                hash_pair.split('|')[0] in hashes_intersection))
        num_match_2 = len(
            set(hash_pair.split('|')[1] for hash_pair in self.hash_set[f_n] if
                hash_pair.split('|')[0] in hashes_intersection))

        num_win_m = self.lines_in[f_m] - self.q + 1
        num_win_n = self.lines_in[f_n] - self.q + 1
        if num_match_1 >= self.theta * num_win_m or num_match_2 >= self.theta * num_win_n:
            return True
        return False

    def verify_pairs(self):
        self.cand_pair_list = list(self.cand_pair)
        clones_cand_indices = [self.verify_pair(f_m_f_n) for f_m_f_n in self.cand_pair_list]
        self.clone_pair = [self.cand_pair_list[i].split('|') for i in range(len(self.cand_pair_list)) if clones_cand_indices[i]]

    def get_coordinates_of_fragment(self, fragment_file_loc):
        file_name = fragment_file_loc.split('/')[-1]
        start, end = file_name[:-len(self.lang_ext)].split('_')
        return int(start), int(end)

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

    def run_algo(self):
        for file in self.files:
            self.index_codeblock(file)
        for mapp in self.cand_map.values():
            if len(mapp) >= 2:
                hashable_pairs = []
                for pair in combinations(list(mapp), 2):
                    if not self.are_fragments_nested(pair[0], pair[1]):
                        hashable_pairs.append(pair[0] + '|' + pair[1])
                self.cand_pair.update(hashable_pairs)
        self.verify_pairs()
        return self.clone_pair

import glob
import os
import time
import tokenize
from shutil import copytree
from subprocess import run

from tree_sitter import Language, Parser
import tree_sitter_java as tsjava
import tree_sitter_python as tspython

from lexical_analysis.comment_remover import CommentRemover
from lexical_analysis.obfuscation import Obfuscator
from lexical_analysis.space_inserter_between_tokens import SpaceInserter
from lexical_analysis.statements_separator import NewlineInserter
from lexical_analysis.pretty_printer_py import PrettyPrinterPython


class PrettyPrinter(object):
    def __init__(self, codebase_loc: str, pretty_loc: str, language):
        self._language = language
        self._lang_ext = None

        self._codebase_loc = codebase_loc
        self._pretty_codebase_loc = pretty_loc + self._codebase_loc.split('/')[-1]
        os.mkdir(pretty_loc)
        os.mkdir(self._pretty_codebase_loc)
        print_with_time("init from base_class")
        self._codeblocks_loc = self._pretty_codebase_loc + "/codeblocks"
        self._obfuscated_loc = self._pretty_codebase_loc + "/obfuscated"
        self._without_type1_changes_loc = self._pretty_codebase_loc + "/without_comments"
        self.tree = None  # will contain new tree-sitter tree for every file in codebase
        self._styled_loc = self._pretty_codebase_loc + '/styled_codeblocks_loc'

    @staticmethod
    def handling_file_storage(from_loc, file_name, dest_loc):
        same_dir = dest_loc + '/' + PrettyPrinter.parent_dir_relative_adress(from_loc, file_name)
        if not os.path.exists(same_dir):
            os.makedirs(same_dir)
        return same_dir
        
        
    @staticmethod
    def parent_dir_relative_adress(folder, file):
        _file = file.split('/')[:-1]
        _folder = folder.split('/')
        relative_addres = '/'.join([name for name in _file if name not in _folder])
        return relative_addres

    def copy_code_fragment(self, file_loc: str, storing_loc: str, start, end):
        start_line, start_col = start
        end_line, end_col = end
        with open(file_loc, 'r') as source_file:
            lines = source_file.readlines()
        code_fragment_lines = lines[start_line: end_line + 1]
        code_fragment_lines[end_line - start_line] = lines[end_line][:end_col]
        code_fragment_lines[0] = code_fragment_lines[0][start_col:]
        extracted_code = ''.join(code_fragment_lines)
        true_start_line = start_line + 1
        true_end_line = end_line + 1
        if code_fragment_lines[0].strip() == '':
            true_start_line += 1
        if code_fragment_lines[end_line - start_line].strip() == '':
            true_end_line -= 1
        codeblock_file_name = f'{storing_loc}/{true_start_line}_{true_end_line}{self._lang_ext}'
        with open(codeblock_file_name, 'w') as destination_file:
            destination_file.write(extracted_code)

    def finding_blocks(self, node, storing_loc, file_loc):
        if len(node.children) == 0:
            return
        if node.type.endswith('body') or node.type == 'block' or (
                node.type == 'compound_statement' and self._lang_ext == '.cpp'):
            start = node.start_point
            end = node.end_point
            self.copy_code_fragment(file_loc, storing_loc, start, end)
        if node.child_by_field_name('body') is not None:
            body_node = node.child_by_field_name('body')
            start = body_node.start_point
            end = body_node.end_point
            self.copy_code_fragment(file_loc, storing_loc, start, end)
        for child in node.children:
            self.finding_blocks(child, storing_loc, file_loc)

    def split_to_codeblocks_file(self, file_loc, new_loc):
        parser = Parser()
        if self._language == "java":
            language = Language(tsjava.language())
        else:
            language = Language(tspython.language())
        parser.set_language(language)
        with open(file_loc, "rb") as f:
            content = f.read()
        self.tree = parser.parse(content)
        storing_loc = new_loc + '/' + file_loc.split('/')[-1][:-len(self._lang_ext)]
        os.mkdir(storing_loc)
        root_node = self.tree.root_node
        self.finding_blocks(root_node, storing_loc, file_loc)


    def split_to_codeblocks_codebase(self, from_loc, to_loc):
        os.mkdir(to_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(from_loc, file, to_loc)
            if not os.path.exists(same_dir):
                os.mkdir(same_dir)
            self.split_to_codeblocks_file(file, same_dir)
        return True

    def obfuscate_codebase(self, from_loc, dest_loc):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(from_loc, file, dest_loc)
            ob = Obfuscator(file, same_dir, self._language)
            ob.obfuscate()
        return True

    @staticmethod
    def glue_gaps_file(file_loc, file_dest, line_sep_ch, tok_sep_ch=' '):
        new_file_name = file_loc.split('/')[-1]
        with open(file_loc, "r") as f:
            content = f.readlines()

        with open(file_dest + '/' + new_file_name, 'w') as f:
            for line in content:
                if line.strip() != '':
                    f.write(tok_sep_ch.join(line.split()) + line_sep_ch)

    @staticmethod
    def glue_ends_file(file_loc, file_dest, line_sep_ch):
        new_file_name = file_loc.split('/')[-1]
        with open(file_loc, "r") as f:
            content = f.readlines()

        with open(file_dest + '/' + new_file_name, 'w') as f:
            for i in range(len(content) - 1):
                line = content[i]
                next_line = content[i + 1]
                if line.strip() != '':
                    if next_line.strip() != ';':
                        f.write(' '.join(line.split()) + line_sep_ch)
                    else:
                        f.write(' '.join(line.split()) + ' ')
            line = content[-1]
            f.write(' '.join(line.split()) + line_sep_ch)


class PrettyPrinterPy(PrettyPrinter):
    def __init__(self, codebase_loc: str, pretty_loc: str, language: str):
        super().__init__(codebase_loc, pretty_loc, language)
        self._lang_ext = '.py'

    def pretty_print(self):
        if self.split_to_codeblocks_codebase(self._codebase_loc, self._codeblocks_loc):
            print("Split to codeblocks")
        PrettyPrinterPython(self._codeblocks_loc, self._obfuscated_loc).pretty_print()
        print("Pretty Printed")


def print_with_time(message, to='log_4'):
    with open(to, 'a') as f:
        print(message, file=f)
        print(time.ctime(time.time()), file=f)


class PrettyPrinterJava(PrettyPrinter):
    def __init__(self, codebase_loc: str, pretty_loc: str, language):
        super().__init__(codebase_loc, pretty_loc, language)
        self._lang_ext = ".java"
        if language == 'c-sharp':
            self._lang_ext = '.cs'
        if language == 'cpp':
            self._lang_ext = '.cpp'
        self._without_comments_loc = self._pretty_codebase_loc + '/without_comments'
        self._styled_loc = self._pretty_codebase_loc + '/styled_codeblocks_loc'
        self._one_whitespace_loc = self._pretty_codebase_loc + '/one_whitespace'
        self._separated_tokens_loc = self._pretty_codebase_loc + '/separated_tokens'
        self._sep_and_glued_loc = self._pretty_codebase_loc + '/sep_and_glued'
        self._pretttty_loc = self._pretty_codebase_loc + '/pretty'

    def remove_comments_codebase(self, from_loc, to_loc):
        os.mkdir(to_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(from_loc, file, to_loc)
            if not os.path.exists(same_dir):
                os.makedirs(same_dir)
            cr = CommentRemover(file, same_dir, self._language)
            cr.remove_comments()
        return True

    def glue_gaps_codebase(self, from_loc, dest_loc, line_sep_ch, tok_sep_ch=' '):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(from_loc, file, dest_loc)
            self.glue_gaps_file(file, same_dir, line_sep_ch, tok_sep_ch)
        return True

    def glue_ends_codebase(self, from_loc, dest_loc, line_sep_ch):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(from_loc, file, dest_loc)
            self.glue_ends_file(file, same_dir, line_sep_ch)
        return True

    def insert_whitespaces_codebase(self, from_loc, dest_loc):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(from_loc, file, dest_loc)
            si = SpaceInserter(file, same_dir, self._language)
            si.insert_spaces()
        return True

    def insert_new_lines_codebase(self, from_loc, dest_loc):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(from_loc, file, dest_loc)
            sp = NewlineInserter(file, same_dir, self._language)
            sp.insert_new_lines()
        return True

    def pretty_print(self):
        if self.remove_comments_codebase(self._codebase_loc, self._without_comments_loc):
            print_with_time("Removed comments")
        if self.split_to_codeblocks_codebase(self._without_comments_loc, self._codeblocks_loc):
            print_with_time("Splitted to codeblocks")
        if self.glue_gaps_codebase(self._codeblocks_loc, self._obfuscated_loc, ' '):
            print_with_time("Written to one line")
        if self.insert_whitespaces_codebase(self._obfuscated_loc, self._obfuscated_loc):
            print_with_time("Tokens are separated")
        if self.glue_gaps_codebase(self._obfuscated_loc, self._obfuscated_loc, ' '):
            print_with_time("Styled again")
        if self.insert_new_lines_codebase(self._obfuscated_loc, self._obfuscated_loc):
            print_with_time("Statements are separated")
        if self.obfuscate_codebase(self._obfuscated_loc, self._obfuscated_loc):
            print_with_time("Obfuscated")
        if self.glue_gaps_codebase(self._obfuscated_loc, self._obfuscated_loc, '\n', ''):
            print_with_time("Styled again")


    def codebase_to_bcb_format(self, bcb_format_loc):
        os.mkdir(bcb_format_loc)
        for file in glob.glob(self._codebase_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = bcb_format_loc + '/' + file.split('/')[-2]
            if not os.path.exists(same_dir):
                os.mkdir(same_dir)
            cr = CommentRemover(file, same_dir, self._language)
            cr.remove_comments()
        return True

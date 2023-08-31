import glob
import os
import time
import tokenize
from shutil import copytree
from subprocess import run

from tree_sitter import Language, Parser

from lexical_analysis.comment_remover import CommentRemover
from lexical_analysis.obfuscation import Obfuscator
from lexical_analysis.space_inserter_between_tokens import SpaceInserter
from lexical_analysis.statements_separator import NewlineInserter

AUTOPEP8_LOC = '/home/lokiplot/.local/bin/autopep8'

JAVA_STYLER_LOC = 'src/styling/google-java-format-1.17.0-all-deps.jar'

Language.build_library(
    # Store the library in the `build` directory
    '../build/my-languages.so',

    # Include one or more languages
    [
        'tree-sitter-python',
        'tree-sitter-java',
        'tree-sitter-c-sharp',
        'tree-sitter-cpp'
    ]
)


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
    def handling_file_storage(file_name, dest_loc):
        same_dir_par = dest_loc + '/' + file_name.split('/')[-3]
        if not os.path.exists(same_dir_par):
            os.mkdir(same_dir_par)
        same_dir = same_dir_par + '/' + file_name.split('/')[-2]
        if not os.path.exists(same_dir):
            os.mkdir(same_dir)
        return same_dir

    def copy_code_fragment(self, file_loc: str, storing_loc: str, start, end):
        """

        :param file_loc:
        :param file_dest:
        :param start_line:
        :param end_line:
        :return:
        """
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
        language = Language('../build/my-languages.so', self._language.replace('-', '_'))
        parser.set_language(language)
        with open(file_loc, "rb") as f:
            content = f.read()
        self.tree = parser.parse(content)
        storing_loc = new_loc + '/' + file_loc.split('/')[-1][:-len(self._lang_ext)]
        os.mkdir(storing_loc)
        root_node = self.tree.root_node
        self.finding_blocks(root_node, storing_loc, file_loc)

    def split_to_codeblocks_codebase(self):
        os.mkdir(self._codeblocks_loc)
        for file in glob.glob(self._without_type1_changes_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self._codeblocks_loc + '/' + file.split('/')[-2]
            if not os.path.exists(same_dir):
                os.mkdir(same_dir)
            self.split_to_codeblocks_file(file, same_dir)
        return True

    def obfuscate_codebase(self, from_loc, dest_loc):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(file, dest_loc)
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

        self._pep8_loc = self._pretty_codebase_loc + "/pep8"

    @staticmethod
    def remove_type1_changes_file_py(file_loc, new_loc):
        new_file_name = new_loc + '/' + file_loc.split('/')[-1]  # can create collision
        new_file_content = list()
        prev_token_type = tokenize.INDENT
        last_lineno = -1
        last_col = 0
        line = ""
        with open(file_loc, 'r') as f:
            tokens = tokenize.generate_tokens(f.readline)
            for token in tokens:
                token_type = token[0]
                token_string = token[1]
                start_line, start_col = token[2]
                end_line, end_col = token[3]
                if start_line > last_lineno:
                    if line.strip() != "":
                        new_file_content.append(line)
                    line = ""
                    last_col = 0
                if start_col > last_col:
                    line += (" " * (start_col - last_col))
                if token_type == tokenize.COMMENT:
                    pass
                elif token_type == tokenize.STRING or token_type == tokenize.NUMBER:
                    if prev_token_type not in [tokenize.INDENT, tokenize.NEWLINE]:
                        if start_col > 0:
                            line += token_string
                else:
                    line += token_string
                prev_token_type = token_type
                last_col = end_col
                last_lineno = end_line

        # TODO: обработать правильно переносы строки () и expressions, которые ничего не делают

        nf = open(new_file_name, 'w')
        nf.write(''.join(new_file_content))
        nf.close()

    def remove_type1_changes_in_codebase_py(self):
        os.mkdir(self._without_type1_changes_loc)
        for file in glob.glob(self._pep8_loc + "/**/*" + self._lang_ext, recursive=True):
            self.remove_type1_changes_file_py(file, self._without_type1_changes_loc)
        return True

    def to_pep8_and_copy_codebase(self) -> bool:
        """
        copies original codebase to new directory (creates new_loc dir) and transforms it to pep8
        respects codebase_dir structure
        :param self:
        :return: True if command was successful
        """
        copytree(self._codebase_loc, self._pep8_loc)
        command_to_pep8 = f'{AUTOPEP8_LOC} {self._pep8_loc} --recursive --in-place --pep8-passes 2000 --verbose'
        status = run(command_to_pep8, shell=True, capture_output=True, text=True).returncode
        return status == 0

    def pretty_print(self):
        if self.to_pep8_and_copy_codebase():
            print("Brought into proper style")
        if self.remove_type1_changes_in_codebase_py():
            print("Removed type 1 changes")
        if self.split_to_codeblocks_codebase():
            print("Split to codeblocks")
        if self.obfuscate_codebase():
            print("Obfuscated")


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

    def remove_comments_codebase(self):
        os.mkdir(self._without_comments_loc)
        for file in glob.glob(self._codebase_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self._without_comments_loc + '/' + file.split('/')[-2]
            if not os.path.exists(same_dir):
                os.mkdir(same_dir)
            cr = CommentRemover(file, same_dir, self._language)
            cr.remove_comments()
        return True

    def glue_gaps_codebase(self, from_loc, dest_loc, line_sep_ch, tok_sep_ch=' '):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(file, dest_loc)
            self.glue_gaps_file(file, same_dir, line_sep_ch, tok_sep_ch)
        return True

    def glue_ends_codebase(self, from_loc, dest_loc, line_sep_ch):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(file, dest_loc)
            self.glue_ends_file(file, same_dir, line_sep_ch)
        return True

    def insert_whitespaces_codebase(self, from_loc, dest_loc):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(file, dest_loc)
            si = SpaceInserter(file, same_dir, self._language)
            si.insert_spaces()
        return True

    def insert_new_lines_codebase(self, from_loc, dest_loc):
        if not os.path.exists(dest_loc):
            os.mkdir(dest_loc)
        for file in glob.glob(from_loc + "/**/*" + self._lang_ext, recursive=True):
            same_dir = self.handling_file_storage(file, dest_loc)
            sp = NewlineInserter(file, same_dir, self._language)
            sp.insert_new_lines()
        return True

    def pretty_print(self):
        if self.remove_comments_codebase():
            print_with_time("Removed comments")
        if self.split_to_codeblocks_codebase():
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



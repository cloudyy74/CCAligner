import glob
import os
import time
import shutil
from typing import List
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_java as tsjava
import tree_sitter_python as tspython
JAVA_LANGUAGE = Language(tsjava.language())
PY_LANGUAGE = Language(tspython.language())

from lexical_analysis.comment_remover import CommentRemover
from lexical_analysis.obfuscation import Obfuscator
from lexical_analysis.space_inserter_between_tokens import SpaceInserter
from lexical_analysis.statements_separator import NewlineInserter


class PrettyPrinter(object):
    def __init__(self, codebase_loc: str, pretty_loc: str, language):
        self._language = language
        self._lang_ext = None

        self._codebase_loc = codebase_loc
        self._pretty_codebase_loc = pretty_loc + self._codebase_loc.split('/')[-1]
        os.makedirs(pretty_loc, exist_ok=True)
        os.makedirs(self._pretty_codebase_loc, exist_ok=True)
        print_with_time("init from base_class")
        self._codeblocks_loc = self._pretty_codebase_loc + "/codeblocks"
        self._obfuscated_loc = self._pretty_codebase_loc + "/obfuscated"
        self._without_type1_changes_loc = self._pretty_codebase_loc + "/without_comments"
        self.tree = None  # will contain new tree-sitter tree for every file in codebase
        self._styled_loc = self._pretty_codebase_loc + '/styled_codeblocks_loc'

    @staticmethod
    def handling_file_storage(from_loc, file_name, dest_loc):
        same_dir = dest_loc + '/' + PrettyPrinter.parent_dir_relative_address(from_loc, file_name)
        if not os.path.exists(same_dir):
            os.makedirs(same_dir)
        return same_dir
        
        
    @staticmethod
    def parent_dir_relative_address(folder, file):
        _file = file.split('/')[:-1]
        _folder = folder.split('/')
        relative_address = '/'.join([name for name in _file if name not in _folder])
        return relative_address

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
        if self._language == "java":
            language = JAVA_LANGUAGE
        else:
            language = PY_LANGUAGE
        parser = Parser(language)
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
    INDENT = " " * 4

    _LITERAL_TYPES = {"string", "integer", "float", "true", "false", "none", "ellipsis"}

    _LINE_END_NODES = {
        "future_import_statement", "print_statement", "delete_statement", "pass_statement",
        "simple_statement", "expression_statement", "assignment", "return_statement", "decorator",
        "import_statement", "import_from_statement", "import_as_name", "break_statement",
        "assert_statement", "augmented_assignment", "raise_statement", "continue_statement",
        "global_statement", "nonlocal_statement", "exec_statement", "type_alias_statement",
    }

    def __init__(self, codebase_loc: str, pretty_loc: str, language: str):
        super().__init__(codebase_loc, pretty_loc, language)
        self._lang_ext = '.py'
        self.src_root = Path(self._codebase_loc).resolve()
        self.dst_root = Path(self._obfuscated_loc).resolve()
        self.parser = Parser(PY_LANGUAGE)
        self._skip_indent_depth: int | None = None

    @staticmethod
    def _is_block(node) -> bool:
        t = node if isinstance(node, str) else node.type
        return t.endswith("_block") or t == "block"

    @staticmethod
    def _starts_block(t: str) -> bool:
        return t in {
            "function_definition", "class_definition", "if_statement", "elif_clause",
            "else_clause", "for_statement", "while_statement", "with_statement",
            "try_statement", "except_clause", "except_group_clause",
            "finally_clause", "match_statement", "case_clause",
            "async_function_definition", "async_for_statement", "async_with_statement",
        }

    @staticmethod
    def _is_semicolon(node) -> bool:
        return (not node.is_named) and node.text.decode() == ";"

    def run(self) -> bool:
        if self.dst_root.exists():
            shutil.rmtree(self.dst_root)
        self.dst_root.mkdir(parents=True)
        for src_file in self.src_root.rglob("*.py"):
            rel = src_file.relative_to(self.src_root)
            dst_file = self.dst_root / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_text(self._process(src_file.read_text("utf‑8")), "utf‑8")
        return True

    
    def _process(self, code: str) -> str:
        tree = self.parser.parse(code.encode())
        out: List[str] = []
        self._dfs(tree.root_node, out, 0)
        final = "\n".join(line for line in "".join(out).splitlines() if line.strip())
        return final

    def _dfs(self, node, out: List[str], indent: int) -> None:
        t = node.type

        if t == "comment":
            return

        if t == "expression_statement" and len(node.children) == 1 and node.children[0].type in self._LITERAL_TYPES:
            return

        if t in {"identifier", "keyword_identifier"}:
            out.append("VAR")
            return

        if t in self._LITERAL_TYPES:
            out.append(t); return

        if not node.is_named:
            tok = node.text.decode()
            if tok.isspace():
                return
            if tok == ";":
                out.append("\n" + self.INDENT * indent)
                self._skip_indent_depth = indent
                return
            out.append(tok)
            return

        if t == "parenthesized_expression":
            for ch in node.children:
                if ch.is_named:
                    self._dfs(ch, out, indent)
            return

        if self._starts_block(t):
            for idx, child in enumerate(node.children):
                if self._is_block(child):
                    out.append("\n")
                    self._dfs(child, out, indent + 1)
                    if idx + 1 < len(node.children):
                        out.append("\n" + self.INDENT * indent)
                else:
                    self._dfs(child, out, indent)
                    if self._starts_block(child.type) and idx + 1 < len(node.children):
                        out.append("\n" + self.INDENT * indent)
            return

        if self._is_block(t):
            for ch in node.children:
                if ch.type == "comment" or (
                    ch.type == "expression_statement" and len(ch.children) == 1 and ch.children[0].type in self._LITERAL_TYPES
                ):
                    continue
                if self._skip_indent_depth is not None and self._skip_indent_depth == indent:
                    self._skip_indent_depth = None
                else:
                    out.append(self.INDENT * indent)
                self._dfs(ch, out, indent)
            return

        children = node.children
        for idx, child in enumerate(children):
            self._dfs(child, out, indent)
            next_node = children[idx + 1] if idx + 1 < len(children) else None
            if child.type in self._LINE_END_NODES and next_node is not None and not self._is_semicolon(next_node):
                out.append("\n" + self.INDENT * indent)
        if t in self._LINE_END_NODES | {"function_definition", "class_definition"}:
            out.append("\n")

    def pretty_print(self):
        if self.split_to_codeblocks_codebase(self._codebase_loc, self._codeblocks_loc):
            print_with_time("Split to codeblocks")
        self.src_root = Path(self._codeblocks_loc).resolve()
        if self.run():
            print_with_time("Pretty Printed")


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

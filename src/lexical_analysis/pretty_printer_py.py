from pathlib import Path
from typing import List
import shutil

from tree_sitter import Language, Parser
import tree_sitter_python as tspython

PY_LANGUAGE = Language(tspython.language())

class PrettyPrinterPython:
    INDENT = " " * 4

    _LITERAL_TYPES = {"string", "integer", "float", "true", "false", "none", "ellipsis"}

    _LINE_END_NODES = {
        "future_import_statement", "print_statement", "delete_statement", "pass_statement",
        "simple_statement", "expression_statement", "assignment", "return_statement", "decorator",
        "import_statement", "import_from_statement", "import_as_name", "break_statement",
        "assert_statement", "augmented_assignment", "raise_statement", "continue_statement",
        "global_statement", "nonlocal_statement", "exec_statement", "type_alias_statement",
    }

    def __init__(self, src_root: str | Path, dst_root: str | Path):
        self.src_root = Path(src_root).resolve()
        self.dst_root = Path(dst_root).resolve()
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

    def pretty_print(self) -> None:
        if self.dst_root.exists():
            shutil.rmtree(self.dst_root)
        self.dst_root.mkdir(parents=True)
        for src_file in self.src_root.rglob("*.py"):
            rel = src_file.relative_to(self.src_root)
            dst_file = self.dst_root / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_text(self._process(src_file.read_text("utf‑8")), "utf‑8")

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


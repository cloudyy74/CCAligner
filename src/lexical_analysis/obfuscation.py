from tree_sitter import Language, Parser
import tree_sitter_java as tsjava



class Obfuscator:
    def __init__(self, file_loc, file_dest, language):
        self.language = language
        self.file_loc = file_loc
        self.file_dest = file_dest
        self.token_map = dict()  # keys are old ids and values are new ones
        self.tree = None
        self.new_lines = None
        self.old_lines = None
        self.var_counter = 0

    @staticmethod
    def is_named_token(token_type):
        if token_type.endswith('identifier') or token_type.endswith('literal'):
            return True
        return False

    @staticmethod
    def reduction_of_type(node_type):
        f = lambda x: x[0] if len(x) > 0 else ""
        return ("".join(f(x) for x in node_type.split("_"))).upper()

    def rename_named_token(self, node):
        line_num, start_col = node.start_point
        _, end_col = node.end_point
        line = self.old_lines[line_num]
        first_non_indent_char_col = len(line) - len(line.lstrip())
        old_name = line[start_col:end_col]
        new_name = self.reduction_of_type(node.type)
        if start_col == first_non_indent_char_col:  # checking if this token is first in line
            self.new_lines[line_num] = self.new_lines[line_num].replace(old_name, new_name, 1)
            return
        token_start_new_line = self.new_lines[line_num].find(f' {old_name} ') + 1
        token_end_new_line = token_start_new_line + len(old_name)
        self.new_lines[line_num] = self.new_lines[line_num][:token_start_new_line] + new_name + \
                                   self.new_lines[line_num][token_end_new_line:]

    def dfs(self, node):
        """
        searching for identifiers nodes in tree and renaming them
        :param node:
        :return:
        """
        if node is None:
            return
        if (len(node.children) == 0 and self.is_named_token(node.type)) or node.type == "string_literal":
            self.rename_named_token(node)
            return
        for child in node.children:
            self.dfs(child)

    def obfuscate(self):
        parser = Parser()
        language = Language(tsjava.language())
        parser.set_language(language)
        with open(self.file_loc, 'rb') as f:
            content = f.read()
        with open(self.file_loc, 'r') as f:
            self.old_lines = f.readlines()
        self.new_lines = self.old_lines.copy()
        self.tree = parser.parse(content)
        root_node = self.tree.root_node
        self.dfs(root_node)
        file_name = self.file_loc.split('/')[-1]
        with open(self.file_dest + '/' + file_name, 'w') as nf:
            new_content = ''.join(self.new_lines)
            nf.write(new_content)

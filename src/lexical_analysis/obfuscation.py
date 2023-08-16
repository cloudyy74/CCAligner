from tree_sitter import Language, Parser


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

    def dfs(self, node):
        """
        searching for identifiers nodes in tree and renaming them
        :param node:
        :return:
        """
        if node is None:
            return
        if node.type.endswith('identifier') or node.type.endswith('literal'):
            line_num, start_col = node.start_point
            _, end_col = node.end_point
            line = self.old_lines[line_num]
            first_non_indent_char_col = len(line) - len(line.lstrip())
            old_name = line[start_col:end_col]
            new_name = node.type
            if start_col == first_non_indent_char_col:  # checking if this token is first in line
                self.new_lines[line_num] = self.new_lines[line_num].replace(old_name, new_name, 1)
                return
            token_start_new_line = self.new_lines[line_num].find(f' {old_name} ') + 1
            token_end_new_line = token_start_new_line + len(old_name)
            self.new_lines[line_num] = self.new_lines[line_num][:token_start_new_line] + new_name + self.new_lines[line_num][token_end_new_line:]
            return
        if len(node.children) == 0:
            return
        for child in node.children:
            self.dfs(child)

    def obfuscate(self):
        parser = Parser()
        language = Language('../build/my-languages.so', self.language.replace('-', '_'))
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



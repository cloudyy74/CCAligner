from tree_sitter import Language, Parser


class CommentRemover:
    def __init__(self, file_loc, file_dest, language):
        self.language = language
        self.file_loc = file_loc
        self.file_dest = file_dest
        self.tree = None
        self.new_lines = None
        self.old_lines = None

    def dfs(self, node):
        """
        searching for identifiers nodes in tree and renaming them
        :param node:
        :return:
        """
        if node.type.endswith('comment'):
            start_line, start_col = node.start_point
            end_line, end_col = node.end_point
            if node.type == 'line_comment':
                self.new_lines[start_line] = self.old_lines[start_line][:start_col] + '\n'
            if node.type == 'block_comment':
                if start_line == end_line:
                    line = self.old_lines[start_line]
                    self.new_lines[start_line] = line[:start_col] + (' ' * (end_col - start_col)) + line[end_col:]
                for line_num in range(start_line + 1, end_line):
                    self.new_lines[line_num] = ' \n'
                self.new_lines[start_line] = self.old_lines[start_line][:start_col]
                self.new_lines[end_line] = (' ' * end_col) + self.old_lines[end_line][end_col:]
            return
        if len(node.children) == 0:
            return
        for child in node.children:
            self.dfs(child)

    def remove_comments(self):
        parser = Parser()
        language = Language('../build/my-languages.so', self.language)
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



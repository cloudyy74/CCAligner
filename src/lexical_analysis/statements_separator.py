from tree_sitter import Language, Parser
from numpy import array, sort


class NewlineInserter:
    def __init__(self, file_loc, file_dest, language):
        self.language = language
        self.file_loc = file_loc
        self.file_dest = file_dest
        self.tree = None
        self.new_lines = None
        self.old_lines = None

        self.statements_ends = list()

    def bfs(self, node):

        if node is None:
            return
        if node.child_by_field_name('body') is not None:
            self.bfs(node.child_by_field_name('body'))
            body_start = node.child_by_field_name('body').start_point[1]
            self.statements_ends.append(body_start + 2)
            return
        if node.child_by_field_name('sequence') is not None:
            self.bfs(node.child_by_field_name('sequence'))
            sequence = node.child_by_field_name('sequence').start_point[1]
            self.statements_ends.append(sequence + 2)
            return
        if node.type == 'block':
            self.statements_ends.append(node.start_point[1] + 2)
        for child in node.children:
            _, st_end = child.end_point
            _, st_start = child.start_point

            if child.type.endswith('_statement') or child.type.endswith('_declaration'):
                self.statements_ends.append(st_end + 1)
                self.bfs(child)
            if child.type == 'block':
                self.bfs(child)


    def insert_new_lines(self):
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
        self.bfs(root_node)
        self.statements_ends = array(self.statements_ends)
        positions_for_new_lines = sort(self.statements_ends) + range(len(self.statements_ends))

        for position in positions_for_new_lines:
            self.new_lines[0] = self.new_lines[0][:position] + '\n' + self.new_lines[0][position:]
        file_name = self.file_loc.split('/')[-1]
        with open(self.file_dest + '/' + file_name, 'w') as nf:
            new_content = ''.join(self.new_lines)
            nf.write(new_content)

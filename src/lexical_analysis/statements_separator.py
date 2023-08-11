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
        """
        это поиск в ширину. когда мы переходим в очередную вершину, считаем, что все ее предки расположены как надо.
        отдельно обрабатываются:
        :param node:
        :return:
        """

        if node is None:
            return
        if node.type.endswith('for_statement'):
            body = node.child_by_field_name('body')
            if body.type != 'block':
                self.statements_ends.append(body.start_point[1])
            self.bfs(body)
            return
        if node.child_by_field_name('consequence') is not None:  # handling if_statement
            consequence = node.child_by_field_name('consequence')
            if consequence.type != 'block':
                self.statements_ends.append(consequence.start_point[1])
            self.bfs(consequence)
            if node.child_by_field_name('alternative') is not None:
                self.statements_ends.append(consequence.end_point[1] + 1)
                alternative = node.child_by_field_name('alternative')
                self.statements_ends.append(alternative.start_point[1])
                self.bfs(alternative)
            return
        if node.type == 'block':
            self.statements_ends.append(node.start_point[1] + 2)
        for child in node.children:
            _, st_end = child.end_point
            _, st_start = child.start_point

            if child.type.endswith('_statement') or child.type.endswith('_declaration') or child.type.endswith('clause'):
                self.statements_ends.append(st_end + 1)
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



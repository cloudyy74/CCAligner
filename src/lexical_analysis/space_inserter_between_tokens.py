from numpy import array, sort
from tree_sitter import Language, Parser
import tree_sitter_java as tsjava



class SpaceInserter:
    def __init__(self, file_loc, file_dest, language):
        self.language = language
        self.file_loc = file_loc
        self.file_dest = file_dest
        self.tree = None
        self.new_lines = None
        self.old_lines = None

    def insert_spaces(self):
        language = Language(tsjava.language())
        parser = Parser(language)
        with open(self.file_loc, 'rb') as f:
            content = f.read()
        with open(self.file_loc, 'r') as f:
            self.old_lines = f.readlines()
        self.new_lines = self.old_lines.copy()
        self.tree = parser.parse(content)
        root_node = self.tree.root_node

        query = language.query("""
        _ @any.node
        """)
        captures = query.captures(root_node)
        nodes_ends = list()
        for capture in captures:
            _, node_end = capture[0].end_point
            nodes_ends.append(node_end)

        nodes_ends = array(nodes_ends)
        positions_for_spaces = sort(nodes_ends) + range(len(nodes_ends))

        for position in positions_for_spaces:
            self.new_lines[0] = self.new_lines[0][:position] + ' ' + self.new_lines[0][position:]
        file_name = self.file_loc.split('/')[-1]
        with open(self.file_dest + '/' + file_name, 'w') as nf:
            new_content = ''.join(self.new_lines)
            nf.write(new_content)



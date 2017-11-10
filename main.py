from analyzer_utils import *
from minic.analysis import *
from pycparser import parse_file
from minic.c_ast_to_minic import transform
import os



test_file = os.path.join("./prog_inputs", "minic.c")

ast = parse_file(test_file)

minic_ast = transform(ast)

nodeVisitor = ReachingDefinitions()
nodeVisitor.visit(minic_ast)


for id in nodeVisitor.loops:
    nodeVisitor.show_rdefs(id)

nodeVisitor = LiveVariables()
nodeVisitor.visit(minic_ast)


for id in nodeVisitor.loops:
    nodeVisitor.show_rdefs(id)

from pycparser import parse_file
from minic.c_ast_to_minic import transform
from analyzer_utils import *

import os

test_file = os.path.join("./prog_inputs", "minic.c")

ast = parse_file(test_file)

minic_ast = transform(ast)

print("List of variables...")
VariablePrinter().visit(minic_ast)

print("-----------------")
print("List of written variables...")
fws = FuncWriteSetPrinter()
fws.visit(minic_ast)
fws.print_sets()

print("-----------------")
print("List of read variables...")
rws = FuncReadSetPrinter()
rws.visit(minic_ast)
rws.print_sets()
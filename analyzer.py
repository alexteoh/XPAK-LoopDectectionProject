from pycparser import parse_file
from pyminic.minic.c_ast_to_minic import transform
from analyzer_utils import *

import os

test_file = os.path.join("./pyminic/tests/c_files", "minic.c")

ast = parse_file(test_file)

minic_ast = transform(ast)

print("List of variables...")
VariablePrinter().visit(minic_ast)

print("-----------------")
print("List of written variables...")
fws = FuncWriteSetPrinter()
fws.visit(minic_ast)
fws.print_sets()
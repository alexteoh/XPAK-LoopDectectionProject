from analyzer_utils import *
from pycparser import parse_file
from pyminic.minic.c_ast_to_minic import transform
import os


def main():
    test_dir = "./prog_inputs"
    for filename in os.listdir(test_dir):
        if filename.endswith(".c"):
            print('\n=======================')
            print('Analyzing ' + filename + ' program')
            test_file = os.path.join(test_dir, filename)
            ast = parse_file(test_file)
            minic_ast = transform(ast)

            lv = LoopVisitor()
            lv.visit(minic_ast)
            print('')
            print(lv)
            print('=======================')


if __name__ == '__main__':
    main()
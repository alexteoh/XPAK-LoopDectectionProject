from loop_analysis import *
from pycparser import parse_file
from pyminic.minic.c_ast_to_minic import transform
import os


def main():
    test_file = os.path.join("./prog_inputs", "test5.c") 
    
    ast = parse_file(test_file)  
      
    
    minic_ast = transform(ast)
    
    lv = LoopVisitor()
    lv.visit(minic_ast)
    print('')
    print(lv)


if __name__ == '__main__':
    main()
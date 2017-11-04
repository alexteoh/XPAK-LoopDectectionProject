from pyminic.minic.minic_ast import *

##
## Copied from Victor Nicolet's tutorial examples.
## still working on visit_forloop
##

class VariablePrinter(NodeVisitor):
    # The type of node a function visits depends on its name
    # Here we want to do something special when the visitor
    # encounters an Assignment node (look at the c_ast.py to
    # see how it is defined).
    def visit_Assignment(self, assignment):
        # The assignment node has a 'lvalue' field, we just
        # want to show it here
        assignment.lvalue.show()


class WriteSetVisitor(NodeVisitor):
    def __init__(self):
        # The 'memory' of the node: the set of variables we are writing in.
        self.writeset = set()

    # What we do when we visit an assignment.
    def visit_Assignment(self, assignment):
        # Add the lvalue if is is an ID node
        # we don't care about other types of lvalues in this
        # very simple analysis.

        if isinstance(assignment.lvalue, ID):
            self.writeset.add(assignment.lvalue.name)

    # What happens when we visit a declaration.
    # Similar to the previous example: we add the variable name
    def visit_Decl(self, decl):
        if decl.init is not None:
            self.writeset.add(decl.name)

    # Here we have a single visitor looking in the whole tree. But you
    # might sometimes need to handle merge cases (when you have to
    # look in a specific way into different branches)
    # For example, we could have added the following function
    def visit_If(self, ifnode):
        wif = WriteSetVisitor()
        welse = WriteSetVisitor()
        wif.visit(ifnode.iftrue)
        welse.visit(ifnode.iffalse)
        self.writeset.union(wif.writeset.union(welse.writeset.union()))

    # In this case it is not really interesting, the visitor would have added
    # the variables anyway, but it could be in other cases.

#still working on this function
def visit_forloop(self,fornode):
        wfor = WriteSetVisitor()
        while wfor.cond != null:
             wnext  = WriteSetVisitor()
             wnext.vist(fornode.next)
             self.writeset.union(wfor.writeset.union(wnext.writeset.union)

# We can wrap this in a function visitor
class FuncWriteSetPrinter(NodeVisitor):
    def __init__(self):
        # The dict associates function names to write sets:
        self.writesets = {}

    def visit_FuncDef(self, funcdef):
        # Create a WriteSet visitor for the body of the function
        wsv = WriteSetVisitor()
        # Execute it on the function's body
        wsv.visit(funcdef.body)
        # Now it contains the writeset of the function
        self.writesets[funcdef.decl.name] = wsv.writeset

    def print_sets(self):
        for fname, writeset in self.writesets.items():
            # Print 'function string' writes in 'set representation'
            print ("%s writes in %r" % (fname, writeset))


class ReadSetVisitor(NodeVisitor):
    def __init__(self):
        # The 'memory' of the node: the set of variables we are writing in.
        self.readset = set()

    # What we do when we visit an assignment.
    def visit_Assignment(self, assignment):
        # Add all rvalue if it is an ID node
        # we don't care about other types of rvalue in this
        if isinstance(assignment.rvalue, BinaryOp):
            if isinstance(assignment.rvalue.left, ID):
                self.readset.add(assignment.rvalue.left.name)
            if isinstance(assignment.rvalue.right, ID):
                self.readset.add(assignment.rvalue.right.name)

    # What happens when we visit a arrayref.
    # Similar to the previous example: we add the variable name
    def visit_ArrayRef(self, aref):
        if isinstance(aref.name, ID):
            self.readset.add(aref.name.name)

    # Here we have a single visitor looking in the whole tree. But you
    # might sometimes need to handle merge cases (when you have to
    # look in a specific way into different branches)
    # For example, we could have added the following function
    def visit_If(self, ifnode):
        rif = ReadSetVisitor()
        relse = ReadSetVisitor()
        rif.visit(ifnode.iftrue)
        relse.visit(ifnode.iffalse)
        self.readset.union(rif.readset.union(relse.readset.union()))

    # In this case it is not really interesting, the visitor would have added
    # the variables anyway, but it could be in other cases.
                                 
#still working on this function
def visit_forloop(self,fornode):
        wfor = WriteSetVisitor()
        while wfor.cond != null:
             wnext  = WriteSetVisitor()
             wnext.vist(fornode.next)
             self.writeset.union(wfor.writeset.union(wnext.writeset.union)

# We can wrap this in a function visitor
class FuncReadSetPrinter(NodeVisitor):
    def __init__(self):
        # The dict associates function names to write sets:
        self.readsets = {}

    def visit_FuncDef(self, funcdef):
        # Create a WriteSet visitor for the body of the function
        rsv = ReadSetVisitor()
        # Execute it on the function's body
        rsv.visit(funcdef.body)
        # Now it contains the readset of the function
        self.readsets[funcdef.decl.name] = rsv.readset

    def print_sets(self):
        for fname, readset in self.readsets.items():
            # Print 'function string' writes in 'set representation'
            print ("%s reads in %r" % (fname, readset))

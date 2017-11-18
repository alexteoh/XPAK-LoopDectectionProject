from minic.minic_ast import *
from minic.analysis import *
import copy


class LoopVisitor():

    def __init__(self):
        # The 'memory' of the node: the set of variables we are writing in.
        self.liveVariables = LiveVariables()
        self.reachingDefinitions = ReachingDefinitions()
        self.loopRWVisitor = LoopRWVisitor()
        self.loops = list()

    def visit(self, node):
        
        self.liveVariables.visit(node)
        self.reachingDefinitions.visit(node)

        self.loopRWVisitor.visit(node)
        self.loops = [sid for sid in self.liveVariables.loops]
        print "self", self.loops
        print "self", self.loopRWVisitor.readsets
        print "self", self.loopRWVisitor.writesets
        print "self indexes", self.loopRWVisitor.indexes
        print "self children", self.loopRWVisitor.children
        print "self", self.liveVariables.str_of_rdef

    def __str__(self):
        res = "Here're the states of each loop in the given program. \n"
        res += "----------In this loop " + str(sid) + " ----------\n"
        res += "Read Variables are these: \n"
        res += str(self.loopRWVisitor.readsets[sid]) + "\n"
        res += "Write Variables are these: \n"
        res += str(self.loopRWVisitor.writesets[sid]) + "\n"
        res += "Live Variables are these: \n"
        res += self.liveVariables.str_of_rdef(sid)
        res += "Reaching Definitions are these\n"
        res += self.reachingDefinitions.str_of_rdef(sid)
        if sid in self.loopRWVisitor.indexes:
            res += "Indexes used and corresponding update statements\n"
            for (ind, stmt) in self.loopRWVisitor.indexes[sid]:
                res += "Index %s is updated in statement %s\n" % (ind, stmt)
        return res


    def nestedloop_printer(self, res, children, parent):
        if not children:
            return parent
        
        else:
            for (child, sid) in children:
                if not child.children:  
                    
		    lst = parent + [sid]
		    lst2 = "["
		    lst3 = []
		    for Id in lst:
			for (ind, stmt) in self.loopRWVisitor.indexes[Id]:
			    lst2 += ind + ", "
			    lst3.append(stmt)
			    
		    lst2 += " ]\n"
		    res += "Loop nest ...:"
		    res += "Index vector: " + lst2
		    res += "Dependence vectors:"
		    for s in lst3:
			res += "Statement: " + s
			                
                    
                else:
		    
		    lst = parent + [sid]
		    lst2 = "["
		    lst3 = []
		    for Id in lst:
			for (ind, stmt) in self.loopRWVisitor.indexes[Id]:
			    lst2 += ind + ", "
			    lst3.append(stmt)
			    
		    lst2 += " ]\n"
		    res += "Loop nest ...:"
		    res += "Index vector: " + lst2
		    res += "Dependence vectors:"
		    for s in lst3:
			res += "Statement: " + s		    
                    self.nested_print(res, child.children, parent.append(sid))
                    
                    
            
            
            
                           
    def normal_print(self, loopRWVisitor, res, sid):
        res += "----------In this loop----------\n"
        res += "Read Variables are these: \n"
        res += str(loopRWVisitor.readsets[sid]) + "\n"
        res += "Write Variables are these: \n"
        res += str(loopRWVisitor.writesets[sid]) + "\n"
        res += "Live Variables are these: \n"
        res += self.liveVariables.str_of_rdef(sid)
        res += "Reaching Definitions are these\n"
        res += self.reachingDefinitions.str_of_rdef(sid)  
        
        if sid in loopRWVisitor.indexes:
            res += "Indexes used and corresponding update statements\n"
            for (ind, stmt) in loopRWVisitor.indexes[sid]:
                res += "Index %s is updated in statement %s\n" % (ind, stmt)         
        

class LoopRWVisitor(NodeVisitor):

    def __init__(self):
        self.readsets = {}
        self.writesets = {}
        self.indexes = {}
        self.children = []
        self.loops = list()

    def visit_For(self, forstmt):
        forsid = forstmt.nid
        self.loops.append(forsid)
        bv = BlockRWVisitor(self)
        bv.visit(forstmt.stmt)
        self.writesets[forsid] = copy.deepcopy(bv.writeset)
        self.readsets[forsid] = copy.deepcopy(bv.readset)

        self.indexes[forsid] = list()
        for decl in forstmt.init.decls:
            self.indexes[forsid].append((decl.name, str(forstmt.next)))

    def visit_While(self, whilestmt):
        whilesid = whilestmt.nid
        self.loops.append(whilesid)
        bv = BlockRWVisitor(self)       
        bv.visit(whilestmt.stmt)
        self.writesets[whilesid] = copy.deepcopy(bv.writeset)
        self.readsets[whilesid] = copy.deepcopy(bv.readset)

    def visit_DoWhile(self, dowhilestmt):
        dowhilesid = dowhilestmt.nid
        self.loops.append(dowhilesid)
        bv = BlockRWVisitor(self)
        bv.visit(dowhilestmt.stmt)
        self.writesets[dowhilesid] = copy.deepcopy(bv.writeset)
        self.readsets[dowhilesid] = copy.deepcopy(bv.readset)


class BlockRWVisitor(NodeVisitor):

    def __init__(self, parent):
        self.readset = set()
        self.writeset = set()
        self.parent = parent

    def visit_Block(self, block):
        wsv = WriteSetVisitor()
        rsv = ReadSetVisitor()        
        for stmt in block.block_items:
            #check nested loop
            if isinstance(stmt, For) or isinstance(stmt, DoWhile) or isinstance(stmt, While):
                nest = LoopRWVisitor()
                nest.visit(stmt)
                self.parent.writesets.update(copy.deepcopy(nest.writesets))
                self.parent.readsets.update(copy.deepcopy(nest.readsets))
                self.parent.indexes.update(copy.deepcopy(nest.indexes))
                #self.parent.children.append(stmt.nid)
                self.parent.children.append((nest, stmt.nid))
            
                print "self.readset", self.readset
                print "self.writeset", self.writeset
                print "nest.indexs", nest.indexes
                print "nest.readsets", nest.readsets
                print "nest.writesets", nest.writesets                
                
            #print "visit_Block", stmt
            wsv.visit(stmt)
            self.writeset = self.writeset.union(wsv.writeset)
            rsv.visit(stmt)
            self.readset = self.readset.union(rsv.readset)


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

from pyminic.minic.minic_ast import *
from pyminic.minic.analysis import *
import copy


# A class to iterate through an AST tree and collect loop information
# It launches several NodeVisitor objects to get various required information.
class LoopVisitor():
    def __init__(self):
        # NodeVisitor to collect live variables set
        self.liveVariables = LiveVariables()
        # NodeVisitor to collect reaching definitions set
        self.reachingDefinitions = ReachingDefinitions()
        # NodeVisitor to collect read/write variables set in loop constructs
        self.loopRWVisitor = LoopRWVisitor()

        # List of loop statement ID (should be common in all NodeVisitors).
        self.loops = list()

    # Launch all NodeVisitors to go through the AST
    def visit(self, node):
        self.liveVariables.visit(node)
        self.reachingDefinitions.visit(node)
        self.loopRWVisitor.visit(node)
        self.loops = [sid for sid in self.loopRWVisitor.loops]

    # String representation of the information collected by this class
    def __str__(self):
        already_checked = []
        ret_str = "Here're the states of each loop in the given program. \n"

        for sid in self.loops:
            if sid not in already_checked:
                ret_str += "----------In this Loop----------\n"
                ret_str += "Read Variables are: \n"
                ret_str += "\t" + str(self.loopRWVisitor.readSets[sid]) + "\n"
                ret_str += "Write Variables are: \n"
                ret_str += "\t" + str(self.loopRWVisitor.writeSets[sid]) + "\n"
                ret_str += "Live Variables are: \n"
                liveVar_str = self.liveVariables.str_of_rdef(sid)
                liveVar_str = liveVar_str[: liveVar_str.find('\n')+1] + "\t" + liveVar_str[liveVar_str.find('\n')+1:]
                ret_str += "\t" + liveVar_str
                ret_str += "Reaching Definitions are: \n"
                ret_str += "\t" + self.reachingDefinitions.str_of_rdef(sid)

                # Print info on indices
                if sid in self.loopRWVisitor.indices:
                    ret_str += "\nIndexes used and corresponding update statements:\n"
                    for (ind, stmt) in self.loopRWVisitor.indices[sid]:
                        ret_str += "\tIndex %s is updated in statement %s\n" % (ind, stmt)

                # Print info on nested loops (e.g. Dependence Vector)
                nested_loops = self.loopRWVisitor.loop_hierarchy.get(sid)
                # If there's nested loops within this loop
                if nested_loops:
                    ret_str += "\nNested Loops information: \n"
                    ret_str += self.nestedloop_printer(nested_loops, [sid], "", already_checked)

        return ret_str

    # Print nested loops information (e.g. index vectors, dependence vectors)
    def nestedloop_printer(self, nested_loops, parent_loop_sid, print_indent, record):
        print_indent += "\t"
        print_output = ""

        for loop_sid in nested_loops:
            record.append(loop_sid)
            loop_sids = parent_loop_sid + [loop_sid]
            dependent_stmt_str = ""
            for sid in loop_sids:
                for (ind, stmt) in self.loopRWVisitor.indices[sid]:
                    dependent_stmt_str += print_indent + print_indent
                    dependent_stmt_str += "Index " + str(ind) + " is updated in statement " + stmt + " \n"

            print_output += print_indent + "----------In Nested Loop----------\n"
            print_output += print_indent + "Indexes used and corresponding update statements: \n"
            print_output += dependent_stmt_str + "\n"

            dependence_lst = self.loopRWVisitor.dependency_map.get(loop_sid)
            if dependence_lst:
                D_flow_vector_str = print_indent + "D_flow vectors: \n"
                D_anti_vectors_str = print_indent + "D_anti vectors: \n"
                D_flow_vectors = []
                D_anti_vectors = []

                left_indices = dependence_lst[0].values()[0]
                right_indices_mapping = dependence_lst[1].values()
                for right_indices in right_indices_mapping:
                    D_flow_vector = []
                    D_anti_vector = []
                    # TODO: need to fix, no state name
                    for left_index in left_indices.keys():
                        if left_index not in right_indices:
                            continue
                        D_flow_vector.append(int(left_indices.get(left_index)) - int(right_indices.get(left_index)))
                        D_anti_vector.append(int(right_indices.get(left_index)) - int(left_indices.get(left_index)))

                    D_flow_vectors.append(D_flow_vector)
                    D_anti_vectors.append(D_anti_vector)

                for s in D_flow_vectors:
                    D_flow_vector_str += print_indent + print_indent + "Statement: " + str(s) + "\n"
                for s in D_anti_vectors:
                    D_anti_vectors_str += print_indent + print_indent + "Statement: " + str(s) + "\n"

                print_output += D_flow_vector_str
                print_output += D_anti_vectors_str + "\n"

            doubly_nested_loops = self.loopRWVisitor.loop_hierarchy.get(loop_sid)
            if doubly_nested_loops:
                print_output += self.nestedloop_printer(doubly_nested_loops, loop_sids, print_indent, record)

        return print_output


# NodeVisitor that tracks read/write variable sets in loops.
class LoopRWVisitor(NodeVisitor):
    def __init__(self):
        # Track read/write variables
        self.readSets = {}
        self.writeSets = {}
        # Track indices used in loops
        self.indices = {}
        # List of statement id of loops
        self.loops = list()
        # Mapping of a loop and its nested loops
        self.loop_hierarchy = {}
        # Dependency maps to track dependence vectors
        # Format: {loop_sid: [left_indices_mapping, right_indices_mapping]}
        self.dependency_map = {}

    def visit_For(self, forstmt):
        forsid = forstmt.nid
        self.loops.append(forsid)
        self.loop_hierarchy[forsid] = []
        bv = BlockRWVisitor(self, forsid)
        bv.visit(forstmt.stmt)
        self.writeSets[forsid] = copy.deepcopy(bv.writeSet)
        self.readSets[forsid] = copy.deepcopy(bv.readSet)

        self.indices[forsid] = list()
        if hasattr(forstmt.init, 'decls'):
            for decl in forstmt.init.decls:
                self.indices[forsid].append((decl.name, str(forstmt.next)))
        else:
            self.indices[forsid].append((forstmt.init.lvalue.name, str(forstmt.next)))


# NodeVisitor that collects information in a block statement
class BlockRWVisitor(NodeVisitor):
    def __init__(self, parent, parentSID):
        self.readSet = set()
        self.writeSet = set()
        self.parent = parent
        self.parentSID = parentSID

    def visit_Block(self, block):
        wsv = WriteSetVisitor()
        rsv = ReadSetVisitor()

        for stmt in block.block_items:
            # check nested loop
            if isinstance(stmt, For):
                nest = LoopRWVisitor()
                nest.visit(stmt)

                self.parent.writeSets.update(copy.deepcopy(nest.writeSets))
                self.parent.readSets.update(copy.deepcopy(nest.readSets))
                self.parent.indices.update(copy.deepcopy(nest.indices))
                self.parent.loop_hierarchy[self.parentSID].append(stmt.nid)
                self.parent.loop_hierarchy.update(copy.deepcopy(nest.loop_hierarchy))

            dva = DependenceVectorAnalysis(stmt.nid)
            dva.visit(stmt)
            self.parent.dependency_map.update(dva.d_mapping)

            wsv.visit(stmt)
            self.writeSet = self.writeSet.union(wsv.writeSet)
            rsv.visit(stmt)
            self.readSet = self.readSet.union(rsv.readSet)


# NodeVisitor that does dependence vector analysis
class DependenceVectorAnalysis(NodeVisitor):
    def __init__(self, parentID):
        self.d_mapping = {}
        self.parentID = parentID
        self.left_indices_mapping = {}
        self.right_indices_mapping = {}

    def visit_Assignment(self, assignment):
        # handle left-hand side, which must be ArrayRef
        if isinstance(assignment.lvalue, ArrayRef):
            indices, d_values = process_ArrayRef(assignment.lvalue)
            mapping = copy.deepcopy(construct_dependency_mapping(assignment.lvalue.name, indices, d_values))
            self.left_indices_mapping.update(mapping)
        else:
            return

        # handle right-hand side
        # example: a[i][j]
        if isinstance(assignment.rvalue, ArrayRef):
            indices, d_values = process_ArrayRef(assignment.rvalue)
            mapping = copy.deepcopy(construct_dependency_mapping(assignment.rvalue.name, indices, d_values))
            self.right_indices_mapping.update(mapping)

        # examples:  #1.a[i][j] + 3    #2.(a[i][j] + 3)  (a[i+1][i+2)
        elif isinstance(assignment.rvalue, BinaryOp):
            self.right_indices_mapping.update(copy.deepcopy(process_BinaryOp(assignment.rvalue)))

        self.d_mapping[self.parentID] = [self.left_indices_mapping, self.right_indices_mapping]


# Process binaryOp statement and returns indices mapping
def process_BinaryOp(binaryOp):
    if not isinstance(binaryOp, BinaryOp):
        # Sanity check
        assert False
        return None

    right_indices_mapping = dict()

    def process_subscript(subscript):
        if isinstance(subscript, ArrayRef):
            right_indices, d_values = process_ArrayRef(subscript)
            right_indices_mapping.update(copy.deepcopy(construct_dependency_mapping(subscript, right_indices, d_values)))

    # Base case
    if isinstance(binaryOp.left, ArrayRef):
        process_subscript(binaryOp.left)
        process_subscript(binaryOp.right)
    else:
        process_subscript(binaryOp.right)
        if isinstance(binaryOp.left, BinaryOp):
            right_indices_mapping.update(process_BinaryOp(binaryOp.left))

    return right_indices_mapping


def process_ArrayRef(ref):
    if not isinstance(ref, ArrayRef):
        # Sanity check
        assert False
        return None, None

    indices = []
    d_values = []

    def process_subscript(subscript):
        if isinstance(subscript, ID):
            indices.append(subscript.name)
            d_values.append("0")
        elif isinstance(subscript, BinaryOp):
            if subscript.op == "+":
                if isinstance(subscript.left, ID):
                    indices.append(subscript.left.name)
                    d_values.append(subscript.right.value)
                else:
                    indices.append(subscript.right.name)
                    d_values.append(subscript.left.value)

            elif subscript.op == "-":
                if isinstance(subscript.left, ID):
                    indices.append(subscript.left.name)
                    d_values.append("-" + subscript.right.value)
                else:
                    indices.append(subscript.right.name)
                    d_values.append("-" + subscript.left.value)

    # Base case
    if isinstance(ref.name, ID):
        # example: if ref is a[i], then ref.name is a and ref.subscript is i
        process_subscript(ref.subscript)

    else:
        process_subscript(ref.subscript)
        if isinstance(ref.name, ArrayRef):
            more_indice, more_d_values = process_ArrayRef(ref.name)
            indices.extend(more_indice)
            d_values.extend(more_d_values)

    return indices, d_values


def construct_dependency_mapping(stmt_name, indices, d_values):
    mapping = dict()
    d_values_mapping = dict()

    for i in range(len(indices)):
        d_values_mapping[indices[i]] = d_values[i]

    mapping[stmt_name] = d_values_mapping
    return mapping


##################################
#
# Helper functions that are adopted from tutorial
#
##################################

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
        self.writeSet = set()

    # What we do when we visit an assignment.
    def visit_Assignment(self, assignment):
        # Add the lvalue if is is an ID node
        # we don't care about other types of lvalues in this
        # very simple analysis.

        if isinstance(assignment.lvalue, ID):
            self.writeSet.add(assignment.lvalue.name)

    # What happens when we visit a declaration.
    # Similar to the previous example: we add the variable name
    def visit_Decl(self, decl):
        if decl.init is not None:
            self.writeSet.add(decl.name)

    # Here we have a single visitor looking in the whole tree. But you
    # might sometimes need to handle merge cases (when you have to
    # look in a specific way into different branches)
    # For example, we could have added the following function
    def visit_If(self, ifnode):
        wif = WriteSetVisitor()
        welse = WriteSetVisitor()
        wif.visit(ifnode.iftrue)
        welse.visit(ifnode.iffalse)
        self.writeSet.union(wif.writeSet.union(welse.writeSet.union()))

        # In this case it is not really interesting, the visitor would have added
        # the variables anyway, but it could be in other cases.


# We can wrap this in a function visitor
class FuncWriteSetPrinter(NodeVisitor):
    def __init__(self):
        # The dict associates function names to write sets:
        self.writeSets = {}

    def visit_FuncDef(self, funcdef):
        # Create a WriteSet visitor for the body of the function
        wsv = WriteSetVisitor()
        # Execute it on the function's body
        wsv.visit(funcdef.body)
        # Now it contains the writeSet of the function
        self.writeSets[funcdef.decl.name] = wsv.writeSet

    def print_sets(self):
        for fname, writeSet in self.writeSets.items():
            # Print 'function string' writes in 'set representation'
            print ("%s writes in %r" % (fname, writeSet))


class ReadSetVisitor(NodeVisitor):
    def __init__(self):
        # The 'memory' of the node: the set of variables we are writing in.
        self.readSet = set()

    # What we do when we visit an assignment.
    def visit_Assignment(self, assignment):
        # Add all rvalue if it is an ID node
        # we don't care about other types of rvalue in this
        if isinstance(assignment.rvalue, BinaryOp):
            if isinstance(assignment.rvalue.left, ID):
                self.readSet.add(assignment.rvalue.left.name)
            if isinstance(assignment.rvalue.right, ID):
                self.readSet.add(assignment.rvalue.right.name)

    # What happens when we visit a arrayref.
    # Similar to the previous example: we add the variable name
    def visit_ArrayRef(self, aref):
        if isinstance(aref.name, ID):
            self.readSet.add(aref.name.name)

    # Here we have a single visitor looking in the whole tree. But you
    # might sometimes need to handle merge cases (when you have to
    # look in a specific way into different branches)
    # For example, we could have added the following function
    def visit_If(self, ifnode):
        rif = ReadSetVisitor()
        relse = ReadSetVisitor()
        rif.visit(ifnode.iftrue)
        relse.visit(ifnode.iffalse)
        self.readSet.union(rif.readSet.union(relse.readSet.union()))

        # In this case it is not really interesting, the visitor would have added
        # the variables anyway, but it could be in other cases.


# We can wrap this in a function visitor
class FuncReadSetPrinter(NodeVisitor):
    def __init__(self):
        # The dict associates function names to write sets:
        self.readSets = {}

    def visit_FuncDef(self, funcdef):
        # Create a WriteSet visitor for the body of the function
        rsv = ReadSetVisitor()
        # Execute it on the function's body
        rsv.visit(funcdef.body)
        # Now it contains the readSet of the function
        self.readSets[funcdef.decl.name] = rsv.readSet

    def print_sets(self):
        for fname, readSet in self.readSets.items():
            # Print 'function string' writes in 'set representation'
            print ("%s reads in %r" % (fname, readSet))

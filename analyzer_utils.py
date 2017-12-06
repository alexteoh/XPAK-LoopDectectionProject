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
        self.loops = [sid for sid in self.liveVariables.loops]
        # self.loops = [sid for sid in self.loopRWVisitor.loops]

    # String representation of the information collected by this class
    def __str__(self):
        already_checked = []
        res = "Here're the states of each loop in the given program. \n"

        for sid in self.loops:
            if sid not in already_checked:
                res += "----------In this loop----------\n"
                res += "Read Variables are these: \n"
                res += "\t" + str(self.loopRWVisitor.readSets[sid]) + "\n"
                res += "Write Variables are these: \n"
                res += "\t" + str(self.loopRWVisitor.writeSets[sid]) + "\n"
                res += "Live Variables are these: \n"
                res += "\t" + self.liveVariables.str_of_rdef(sid)
                res += "Reaching Definitions are these\n"
                res += "\t" + self.reachingDefinitions.str_of_rdef(sid)

                if sid in self.loopRWVisitor.indexes:
                    res += "\nIndexes used and corresponding update statements:\n"
                    for (ind, stmt) in self.loopRWVisitor.indexes[sid]:
                        res += "\tIndex %s is updated in statement %s\n" % (ind, stmt)

                nested_loops = self.loopRWVisitor.loop_hierarchy.get(sid)
                # If there's nested loops within this loop
                if nested_loops:
                    res += "\nNested Loops information: \n"
                    res += self.nestedloop_printer(nested_loops, [sid], "", already_checked)
                    # res += self.nestedloop_printer("", nested_loops, [sid], "", already_checked)

        return res

    # Print nested loops information (e.g. index vectors, dependence vectors)
    def nestedloop_printer(self, nested_loops, parent_loop_sid, print_indent, record):
        print_indent += "\t"
        print_output = ""

        for loop_sid in nested_loops:
            record.append(loop_sid)
            loop_sids = parent_loop_sid + [loop_sid]
            index_vectors_str = print_indent + "Index vector: ["
            dependent_stmt_str = print_indent + "Dependence vectors: \n"
            for sid in loop_sids:
                for item in self.loopRWVisitor.indexes[sid]:
                    (ind, stmt) = item
                    index_vectors_str += ind + ", "
                    dependent_stmt_str += print_indent + print_indent + "Statement: " + str(stmt) + "\n"

            index_vectors_str = index_vectors_str.rstrip(',')
            index_vectors_str += "]\n"
            print_output += print_indent + "------- Nested Loop ------\n"
            print_output += index_vectors_str
            print_output += dependent_stmt_str + "\n"

            dependence_vectors = self.loopRWVisitor.dependence_vector.get(loop_sid)
            if dependence_vectors:

                D_flow_vector_str = print_indent + "D_flow vectors: \n"
                D_anti_vectors_str = print_indent + "D_anti vectors: \n"
                D_flow_vectors = []
                D_anti_vectors = []


                states_value = dependence_vectors[0].values()[0]
                vector_value_lst = dependence_vectors[1].values()
                for dic in vector_value_lst:
                    temp_lst = []
                    temp_lst2 = []
                    # TODO: need to fix, no state name
                    for key in states_value.keys():
                        if key not in dic:
                            continue
                        temp_lst.append(int(states_value.get(key)) - int(dic.get(key)))
                        temp_lst2.append(int(dic.get(key)) - int(states_value.get(key)))

                    D_flow_vectors.append(temp_lst)
                    D_anti_vectors.append(temp_lst2)

                for s in D_flow_vectors:
                    D_flow_vector_str += print_indent + print_indent + "Statement: " + str(s) + "\n"
                for s in D_anti_vectors:
                    D_anti_vectors_str += print_indent + print_indent + "Statement: " + str(s) + "\n"

                print_output += D_flow_vector_str + "\n"
                print_output += D_anti_vectors_str + "\n"

            doubly_nested_loops = self.loopRWVisitor.loop_hierarchy.get(loop_sid)
            if doubly_nested_loops:
                print_output += self.nestedloop_printer(doubly_nested_loops, loop_sids, print_indent, record)

        return print_output


# NodeVisitor that tracks read/write variable sets in loops.
class LoopRWVisitor(NodeVisitor):
    def __init__(self):
        self.readSets = {}
        self.writeSets = {}
        self.indexes = {}
        self.loop_hierarchy = {}
        self.loops = list()

        self.dependence_vector = {}

    def visit_For(self, forstmt):
        forsid = forstmt.nid
        self.loops.append(forsid)
        self.loop_hierarchy[forsid] = []
        bv = BlockRWVisitor(self, forsid)
        bv.visit(forstmt.stmt)
        self.writeSets[forsid] = copy.deepcopy(bv.writeSet)
        self.readSets[forsid] = copy.deepcopy(bv.readSet)

        self.indexes[forsid] = list()
        if hasattr(forstmt.init, 'decls'):
            for decl in forstmt.init.decls:
                self.indexes[forsid].append((decl.name, str(forstmt.next)))
        else:
            self.indexes[forsid].append((forstmt.init.lvalue.name, str(forstmt.next)))

    def visit_While(self, whilestmt):
        whilesid = whilestmt.nid
        self.loops.append(whilesid)
        bv = BlockRWVisitor(self, whilesid)
        bv.visit(whilestmt.stmt)
        self.writeSets[whilesid] = copy.deepcopy(bv.writeSet)
        self.readSets[whilesid] = copy.deepcopy(bv.readSet)

    def visit_DoWhile(self, dowhilestmt):
        dowhilesid = dowhilestmt.nid
        self.loops.append(dowhilesid)
        bv = BlockRWVisitor(self, dowhilesid)
        bv.visit(dowhilestmt.stmt)
        self.writeSets[dowhilesid] = copy.deepcopy(bv.writeSet)
        self.readSets[dowhilesid] = copy.deepcopy(bv.readSet)


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
            # print "inside block: ", stmt

            # check nested loop
            if isinstance(stmt, For) or isinstance(stmt, DoWhile) or isinstance(stmt, While):
                nest = LoopRWVisitor()
                nest.visit(stmt)

                self.parent.writeSets.update(copy.deepcopy(nest.writeSets))
                self.parent.readSets.update(copy.deepcopy(nest.readSets))
                self.parent.indexes.update(copy.deepcopy(nest.indexes))
                self.parent.loop_hierarchy[self.parentSID].append(stmt.nid)
                self.parent.loop_hierarchy.update(copy.deepcopy(nest.loop_hierarchy))

            dva = DependenceVectorAnalysis(stmt.nid)
            dva.visit(stmt)
            self.parent.dependence_vector.update(dva.lst)
            # if isinstance(stmt, Assignment):
            #     d_mapping = generate_dependency_mapping(stmt)
            #     self.parent.dependence_vector.update(d_mapping)

            wsv.visit(stmt)
            self.writeSet = self.writeSet.union(wsv.writeSet)
            rsv.visit(stmt)
            self.readSet = self.readSet.union(rsv.readSet)


# NodeVisitor that do dependence vector analysis
class DependenceVectorAnalysis(NodeVisitor):
    def __init__(self, parentID):
        self.lst = {}
        self.parentID = parentID
        self.states = {}
        self.dependence_vector = {}

    def visit_Assignment(self, assignment):
        # handle lefthand side, and left side must be ArrayRef

        if isinstance(assignment.lvalue, ArrayRef):
            key, val = process_ArrayRef(assignment.lvalue)
            self.states.update(copy.deepcopy(helper_construct(assignment.lvalue.name, key, val)))
        else:
            return

        # handle right-hand side
        # example: a[i][j]
        if isinstance(assignment.rvalue, ArrayRef):
            key, val = process_ArrayRef(assignment.rvalue)
            self.dependence_vector.update(copy.deepcopy(helper_construct(assignment.rvalue.name, key, val)))

        # examples:  #1.a[i][j] + 3    #2.(a[i][j] + 3)  (a[i+1][i+2)
        elif isinstance(assignment.rvalue, BinaryOp):
            states = process_BinaryOp(assignment.rvalue)
            self.dependence_vector.update(copy.deepcopy(states))

        self.lst[self.parentID] = [self.states, self.dependence_vector]


def generate_dependency_mapping(assignment):
    if not isinstance(assignment, Assignment):
        # Sanity check
        assert False
        return None

    d_mapping = {}
    states = {}
    d_vectors = {}

    # handle left-hand side which must be ArrayRef
    if isinstance(assignment.lvalue, ArrayRef):
        key, val = process_ArrayRef(assignment.lvalue)
        states.update(copy.deepcopy(helper_construct(assignment.lvalue.name, key, val)))

    # handle right-hand side
    # example: a[i][j]
    if isinstance(assignment.rvalue, ArrayRef):
        key, val = process_ArrayRef(assignment.rvalue)
        d_vectors.update(copy.deepcopy(helper_construct(assignment.rvalue.name, key, val)))

    # examples:  #1.a[i][j] + 3    #2.(a[i][j] + 3)  (a[i+1][i+2)
    elif isinstance(assignment.rvalue, BinaryOp):
        sub_states = process_BinaryOp(assignment.rvalue)
        d_vectors.update(copy.deepcopy(sub_states))

    d_mapping[assignment.nid] = [states, d_vectors]
    return d_mapping


def process_BinaryOp(binaryOp):
    if not isinstance(binaryOp, BinaryOp):
        # Sanity check
        assert False
        return None

    states = dict()

    def process_subscript(subscript):
        if isinstance(subscript, ArrayRef):
            index, d_value = process_ArrayRef(subscript)
            states.update(copy.deepcopy(helper_construct(subscript, index, d_value)))

    # Base case
    if isinstance(binaryOp.left, ArrayRef):
        process_subscript(binaryOp.left)
        process_subscript(binaryOp.right)
    else:
        process_subscript(binaryOp.right)
        if isinstance(binaryOp.left, BinaryOp):
           states.update(process_BinaryOp(binaryOp.left))

    return states


def process_ArrayRef(ref):
    if not isinstance(ref, ArrayRef):
        # Sanity check
        assert False
        return None, None

    index = []
    d_value = []

    def process_subscript(subscript):
        if isinstance(subscript, ID):
            index.append(subscript.name)
            d_value.append("0")
        elif isinstance(subscript, BinaryOp):
            if subscript.op == "+":
                if isinstance(subscript.left, ID):
                    index.append(subscript.left.name)

                    d_value.append(subscript.right.value)
                else:
                    index.append(subscript.right.name)
                    d_value.append(subscript.left.value)

            elif subscript.op == "-":
                if isinstance(subscript.left, ID):
                    index.append(subscript.left.name)
                    d_value.append("-" + subscript.right.value)
                else:
                    index.append(subscript.right.name)
                    d_value.append("-" + subscript.left.value)

    # Base case
    if isinstance(ref.name, ID):
        # example: if ref is a[i], then ref.name is a and ref.subscript is i
        process_subscript(ref.subscript)

    else:
        process_subscript(ref.subscript)
        if isinstance(ref.name, ArrayRef):
            more_index, more_d_value = process_ArrayRef(ref.name)
            index.extend(more_index)
            d_value.extend(more_d_value)

    return index, d_value


def helper_construct(state, keys, values):
    output_dict = dict()
    val_dict = dict()

    for i in range(len(keys)):
        val_dict[keys[i]] = values[i]

    output_dict[state] = val_dict
    return output_dict


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

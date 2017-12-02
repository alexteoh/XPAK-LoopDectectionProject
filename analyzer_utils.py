from pyminic.minic.minic_ast import *
from pyminic.minic.analysis import *
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

    def __str__(self):
        already_checked = []
        res = "Here're the states of each loop in the given program. \n"
        for sid in self.loops:
            if sid not in already_checked:
                child_lst = self.loopRWVisitor.children.get(sid)
                # case that have a nested loop
                if child_lst:
                    res += "----------In this loop----------\n"
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

                    buf_blank, buf_res = "", ""
                    res += "\nHere're the nested loop of this loop. \n"
                    res += self.nestedloop_printer(buf_res, child_lst, [sid], buf_blank, already_checked)




                # case do not have a nested loop
                else:
                    res += "----------In this loop----------\n"
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

    def nestedloop_printer(self, res, children, parent, blank, record):

        if not children:
            return ""

        else:

            blank += "  "
            for child_id in children:
                child_lst = self.loopRWVisitor.children.get(child_id)
                if child_lst:
                    record.append(child_id)
                    index_vector_lst = parent + [child_id]
                    index_vector = blank + "Index vector: ["
                    dependent_stmt_lst = []
                    dependent_stmt = blank + "Dependence vectors: \n"
                    for rng in index_vector_lst:
                        for (ind, stmt) in self.loopRWVisitor.indexes[rng]:
                            index_vector += ind + ", "
                            dependent_stmt_lst.append(stmt)

                    for s in dependent_stmt_lst:
                        dependent_stmt += blank + blank + "Statement: " + s + "\n"

                    index_vector = index_vector[:-2]
                    index_vector += "]\n"
                    res += blank + "Nested Loop\n"
                    res += index_vector
                    res += dependent_stmt + "\n"
                    parent.append(child_id)

                    res += self.nestedloop_printer("", child_lst, parent, blank, record)

                else:
                    record.append(child_id)
                    index_vector_lst = parent + [child_id]
                    index_vector = blank + "Index vector: ["
                    dependent_stmt = blank + "D_flow vectors: \n"
                    dependent_stmt_lst = []
                    dependent_stmt_lst2 = []
                    for rng in index_vector_lst:
                        for (ind, stmt) in self.loopRWVisitor.indexes[rng]:
                            index_vector += ind + ", "

                    if self.loopRWVisitor.dependence_vector.get(child_id):

                        lst = self.loopRWVisitor.dependence_vector.get(child_id)
                        states_value = lst[0].values()[0]
                        vector_value_lst = lst[1].values()
                        temp_lst = []
                        temp_lst2 = []
                        for dic in vector_value_lst:
                            # TODO: need to fix, no state name
                            for key in states_value.keys():
                                temp_lst.append(int(states_value.get(key)) - int(dic.get(key)))
                                temp_lst2.append(int(dic.get(key)) - int(states_value.get(key)))

                            dependent_stmt_lst.append(temp_lst)
                            dependent_stmt_lst2.append(temp_lst2)
                            temp_lst = []
                            temp_lst2 = []

                    for s in dependent_stmt_lst:
                        dependent_stmt += blank + blank + "Statement: " + str(s) + "\n"

                    dependent_stmt2 = blank + "D_anti vectors: \n"

                    for s in dependent_stmt_lst2:
                        dependent_stmt2 += blank + blank + "Statement: " + str(s) + "\n"

                    index_vector = index_vector[:-2]
                    index_vector += "]\n"
                    res += index_vector
                    res += dependent_stmt + "\n"
                    res += dependent_stmt2 + "\n"

                    res += self.nestedloop_printer("", [], parent, blank, record)

            return res


class LoopRWVisitor(NodeVisitor):
    def __init__(self):
        self.readsets = {}
        self.writesets = {}
        self.indexes = {}
        self.children = {}
        self.loops = list()

        self.dependence_vector = {}

    def visit_For(self, forstmt):
        forsid = forstmt.nid
        self.loops.append(forsid)
        self.children[forsid] = []
        bv = BlockRWVisitor(self, forsid)
        bv.visit(forstmt.stmt)
        self.writesets[forsid] = copy.deepcopy(bv.writeset)
        self.readsets[forsid] = copy.deepcopy(bv.readset)

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
        self.writesets[whilesid] = copy.deepcopy(bv.writeset)
        self.readsets[whilesid] = copy.deepcopy(bv.readset)

    def visit_DoWhile(self, dowhilestmt):
        dowhilesid = dowhilestmt.nid
        self.loops.append(dowhilesid)
        bv = BlockRWVisitor(self, forsid)
        bv.visit(dowhilestmt.stmt)
        self.writesets[dowhilesid] = copy.deepcopy(bv.writeset)
        self.readsets[dowhilesid] = copy.deepcopy(bv.readset)


class BlockRWVisitor(NodeVisitor):
    def __init__(self, parent, parentID):
        self.readset = set()
        self.writeset = set()
        self.parent = parent
        self.parentId = parentID

    def visit_Block(self, block):
        wsv = WriteSetVisitor()
        rsv = ReadSetVisitor()

        for stmt in block.block_items:
            # print "inside block: ", stmt

            # check nested loop
            if isinstance(stmt, For) or isinstance(stmt, DoWhile) or isinstance(stmt, While):
                nest = LoopRWVisitor()
                nest.visit(stmt)

                self.parent.writesets.update(copy.deepcopy(nest.writesets))
                self.parent.readsets.update(copy.deepcopy(nest.readsets))
                self.parent.indexes.update(copy.deepcopy(nest.indexes))
                self.parent.children[self.parentId].append(stmt.nid)
                self.parent.children.update(copy.deepcopy(nest.children))

            dva = DepedenceVectorAnalysis(stmt.nid)
            dva.visit(stmt)
            self.parent.dependence_vector.update(dva.lst)

            wsv.visit(stmt)
            self.writeset = self.writeset.union(wsv.writeset)
            rsv.visit(stmt)
            self.readset = self.readset.union(rsv.readset)


class DepedenceVectorAnalysis(NodeVisitor):
    def __init__(self, parentID):
        self.lst = {}
        self.parentID = parentID
        self.states = {}
        self.dependence_vector = {}

    def visit_Assignment(self, assignment):
        # handle lefthand side, and left side must be ArrayRef

        if isinstance(assignment.lvalue, ArrayRef):
            fa_left = FetchArrayRef()
            fa_left.visit(assignment.lvalue)
            self.states.update(copy.deepcopy(helper_construct(assignment.lvalue.name, fa_left.key, fa_left.value)))

        # handle righthand side

        # case: a[i][j]
        if isinstance(assignment.rvalue, ArrayRef):
            fa_right = FetchArrayRef()
            fa_right.visit(assignment.rvalue)

            self.dependence_vector.update(
                copy.deepcopy(helper_construct(assignment.rvalue.name, fa_right.key, fa_right.value)))

        # case:  #1.a[i][j] + 3    #2.(a[i][j] + 3)  (a[i+1][i+2)
        elif isinstance(assignment.rvalue, BinaryOp):

            fb_right = FetchBinaryOp()
            fb_right.visit(assignment.rvalue)

            self.dependence_vector.update(copy.deepcopy(fb_right.states))


        elif isinstance(assignment.rvalue, Constant):
            pass


        else:
            pass

        self.lst[self.parentID] = [self.states, self.dependence_vector]


class FetchArrayRef(NodeVisitor):
    def __init__(self):
        self.key = []
        self.value = []

    def visit_ArrayRef(self, ref):

        # base case
        if isinstance(ref.name, ID):
            self.condition_analysis(ref.subscript)

        else:
            self.condition_analysis(ref.subscript)
            self.visit_ArrayRef(ref.name)

    def condition_analysis(self, most_right):

        if isinstance(most_right, ID):
            self.key.append(most_right.name)
            self.value.append("0")
        if isinstance(most_right, Constant):
            # currently ignore this case
            pass

        if isinstance(most_right, BinaryOp):
            if most_right.op == "+":
                if isinstance(most_right.left, ID):
                    self.key.append(most_right.left.name)

                    self.value.append(most_right.right.value)
                else:
                    self.key.append(most_right.right.name)
                    self.value.append(most_right.left.value)

            if most_right.op == "-":
                if isinstance(most_right.left, ID):
                    self.key.append(most_right.left.name)
                    self.value.append("-" + most_right.right.value)
                else:
                    self.key.append(most_right.right.name)
                    self.value.append("-" + most_right.left.value)


class FetchBinaryOp(NodeVisitor):
    def __init__(self):
        self.states = dict()

    def visit_BinaryOp(self, binaryop):
        # base case
        if isinstance(binaryop.left, ID):
            return

        if isinstance(binaryop.left, ArrayRef):
            self.condition_analysis(binaryop.left)
            self.condition_analysis(binaryop.right)

        else:
            self.condition_analysis(binaryop.right)
            self.visit_BinaryOp(binaryop.left)

    def condition_analysis(self, most_right):
        if isinstance(most_right, ArrayRef):
            fa = FetchArrayRef()
            fa.visit(most_right)

            self.states.update(copy.deepcopy(helper_construct(most_right, fa.key, fa.value)))


def helper_construct(state, keys, values):
    output_dict = dict()
    val_dict = dict()

    for i in range(len(keys)):
        val_dict[keys[i]] = values[i]

    output_dict[state] = val_dict
    return output_dict


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

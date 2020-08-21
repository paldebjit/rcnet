import json

from common.config import config
from common.utils import *

from pyverilog.vparser.ast import Node
from pyverilog.vparser.parser import parse
from pyverilog.vparser.preprocessor import VerilogPreprocessor



##############
# NODE PATCH #
##############
# DESCRIPTION:
# There are some issues with Pyverilog's node comparison function.
# Hence, we patch it here
def compareNodes(self, other):
    if type(self) != type(other):
        return False

    self_attrs = tuple([getattr(self, a) for a in self.attr_names])
    other_attrs = tuple([getattr(other, a) for a in other.attr_names])

    if self_attrs != other_attrs:
        return False

    other_children = other.children()

    if len(other_children) != len(self.children()):
        return False

    for i, c in enumerate(self.children()):
        if c != other_children[i]:
            return False

    return True

Node.__eq__ = compareNodes



####################
# HELPER FUNCTIONS #
####################
def _lcs(S,T):
    m = len(S)
    n = len(T)
    counter = [[0]*(n+1) for x in range(m+1)]
    longest = 0
    l_start = -1
    r_start = -1
    for i in range(m):
        for j in range(n):
            if S[i] == T[j]:
                c = counter[i][j] + 1
                counter[i+1][j+1] = c
                if c > longest:
                    longest = c
                    l_start = i - c + 1
                    r_start = j - c + 1

    return (l_start, r_start, longest)
    
def _cm(S, T, pt):
    closest_i = -1
    closest_j = -1
    closest_score = float("inf")
    closest_diff = []
    for i,s, in enumerate(S):
        for j,t in enumerate(T):
            diffs = get_ast_diff(s,t,pt)
            score = len(diffs)
            if (score < closest_score):
                closest_i = i
                closest_j = j
                closest_diff = diffs
                closest_score = score

    return closest_i, closest_j, closest_diff


#########################
# PRIMARY AST FUNCTIONS #
#########################
def get_ast(design, version):
    rtl_path = get_rtl_path(design, version)
    vfiles = get_vfile(design, version, config.designs[design]["exclude_files"])

    # Uncomment to dump preprocessed verilog file
    # pre = VerilogPreprocessor(vfiles, version + "_preprocess.out", [rtl_path], [])
    # pre.preprocess()

    ast, direct = parse(vfiles, preprocess_include=[rtl_path])

    # Uncomment to dump AST for debug:
    #with open(version + "_ast.out", "w") as f:
    #    ast.show(buf=f, attrnames=True, showlineno=True, debug=False)

    return ast

def get_ast_diff(ref_node, err_node, parent_type=""):
    out_diff_list = []

    if ref_node == err_node:
        return out_diff_list

    if type(ref_node) != type(err_node):
        out_diff_list.append(dict(diff_type="node_type", 
                                    ref_node_type=ref_node.__class__.__name__,
                                    err_node_type=err_node.__class__.__name__,
                                    ref_line_no=ref_node.lineno,
                                    err_line_no=err_node.lineno,
                                    parent_type=parent_type))

    if ref_node.attr_names != err_node.attr_names:
        if type(ref_node) == type(err_node):
            out_diff_list.append(dict(diff_type="attr_list",
                                        node_type=ref_node.__class__.__name__,
                                        ref_node_attrs=ref_node.attr_names,
                                        err_node_attrs=err_node.attr_names,
                                        ref_line_no=ref_node.lineno,
                                        err_line_no=err_node.lineno,
                                        parent_type=parent_type))
    else:
        for attr in ref_node.attr_names:
            ref_val = getattr(ref_node, attr) 
            err_val= getattr(err_node, attr)
            if ref_val != err_val:
                out_diff_list.append(dict(diff_type="attr",
                                            diff_attr=attr,
                                            node_type=ref_node.__class__.__name__,
                                            ref_attr_value=ref_val,
                                            err_attr_value=err_val,
                                            ref_line_no=ref_node.lineno,
                                            err_line_no=err_node.lineno,
                                            parent_type=parent_type))

    ref_children = ref_node.children()
    err_children = err_node.children()

    get_ast_children_diff(ref_children, err_children, out_diff_list, err_node.__class__.__name__)
    return out_diff_list

def get_ast_children_diff(ref_children, err_children, out_diff_list, parent_type=""):
    ls, rs, ln = _lcs(ref_children, err_children)

    if ln == 0:
        if len(err_children) == 0:
            for ref in ref_children:
                out_diff_list.append(dict(diff_type="remove_node",
                                            ref_node_type=ref.__class__.__name__,
                                            ref_node_name=getattr(ref, "name", ""),
                                            ref_line_no=ref.lineno,
                                            parent_type=parent_type))
        elif len(ref_children) == 0:
            for err in err_children:
                out_diff_list.append(dict(diff_type="add_node",
                                            err_node_type=err.__class__.__name__,
                                            err_node_name=getattr(err, "name", ""),
                                            err_line_no=err.lineno,
                                            parent_type=parent_type))
        else:
            ls, rs, diff = _cm(ref_children, err_children, parent_type)
            out_diff_list += diff
            get_ast_children_diff(ref_children[:ls], err_children[:rs], out_diff_list, parent_type)
            get_ast_children_diff(ref_children[ls+1:], err_children[rs+1:], out_diff_list, parent_type)
    else:
        get_ast_children_diff(ref_children[:ls], err_children[:rs], out_diff_list, parent_type)
        get_ast_children_diff(ref_children[ls+ln:], err_children[rs+ln:], out_diff_list, parent_type)



if __name__ == "__main__":
    if not config.available:
        config.read_config()

    err = get_ast("openmsp430", "v228_01")
    ref = get_ast("openmsp430", "v204_00")

    diff_list = get_ast_diff(ref, err)

    with open("diff.json", "w") as f:
        json.dump(diff_list, f, indent=4, separators=(',', ': '))

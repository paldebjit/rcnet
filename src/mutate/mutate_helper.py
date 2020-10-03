import random

from common.ast import *
from mutate.mutate_ctrl import *

def _check_parent_type(node, nodes, types):
    par = node
    while(nodes[par] != None):
        par = nodes[par]
        if type(par) in types:
            return True
    return False

def mutate_operator(root, nodes, path):
    candidates = [node 
                    for node in nodes.keys() 
                        if type(node) in OP_TYPES.keys()
                            and _check_parent_type(node, nodes, OP_PARENT_TYPES)]
    
    if len(candidates) == 0:
        return -1

    mut_node = random.choice(candidates)
    type_idx = OP_TYPES[type(mut_node)]
    new_node_type = random.choice([types for types in OP_MAP[type_idx] if types != type(mut_node)])

    mut_node.__class__ = new_node_type

    save_ast(root, path)
    
    return mut_node.lineno

def mutate_signal(root, nodes, path):
    candidates = [node 
                    for node in nodes.keys()
                        if type(node) == Identifier
                            and _check_parent_type(node, nodes, SIG_PARENT_TYPES)]

    if len(candidates) == 0:
        return -1 

    sigs = get_signals(root)

    while (True):
        mut_node = random.choice(candidates)
        name = mut_node.name
        if name in sigs.keys():
            sig_type = sigs[name]

            new_name = random.choice([sig for sig in sigs[sig_type] if sig != name])
            mut_node.name = new_name

            save_ast(root, path)

            return mut_node.lineno

def mutate_constant(root, nodes, path):
    return -1

def mutate_operand(root, nodes, path):
    return -1 

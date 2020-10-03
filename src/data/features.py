import numpy as np

from common.ast import *
from common.utils import *
from data.constants import *

def embed_cdfg_node_type(graph):
    for node, node_type in graph.nodes(data="typ"):
        graph.nodes[node]['features'].append(CDFG_TYPE.index(node_type))

def embed_ast_type_count(graph):
    for node, ast in graph.nodes(data='ast'):
        line_count = ast_type_count(ast)
        graph.nodes[node]['features'].extend(line_count.values())

def embed_ast_diff(design, mut, ref, g):
    file_wise_diff = {}
    ref_vfiles = get_vfile(design, ref)
    for mut_vf in get_vfile(design, mut):
        # Find equivalent file in Ref
        fname = os.path.basename(mut_vf)
        ref_vf = next(vf for vf in ref_vfiles if os.path.basename(vf) == fname)

        # Find ASTs and their Diff
        mut_ast = get_ast(design, mut, mut_vf)
        ref_ast = get_ast(design, ref, ref_vf)
        
        diff_list = get_ast_diff(ref_ast, mut_ast)

        # Count diff types per file and line no.
        file_wise_diff[fname] = {}
        for diff in diff_list:
            line = diff['err_line_no'] if 'err_line_no' in diff else diff['parent_line']
            if line not in file_wise_diff[fname]:
                file_wise_diff[fname][line] = np.zeros(len(AST_DIFF_TYPES))
            
            # TODO: Better ast diff features.
            file_wise_diff[fname][line][AST_DIFF_TYPES.index(diff['diff_type'])] += 1

    
    module_map = get_module_map(design, mut)


    for node in g.nodes():
        # Find node's defining and lineno range
        fname = module_map[g.nodes[node]['module']]
        fname = os.path.basename(fname)
        if 'ast' in g.nodes[node]:
            ast = g.nodes[node]['ast']  
            node_dict = get_all_nodes(ast)
            lines = [ key.lineno for key in node_dict.keys() ]
        else:
            lines = []
        

        # Find diff for the lines in node
        feat = np.zeros(len(AST_DIFF_TYPES))
        for line in lines:
            if line in file_wise_diff[fname]:
                feat += file_wise_diff[fname][line]

        # Push feature to list of features
        g.nodes[node]['features'].extend(feat.tolist())

        # Also label mutated lines with True label
        if fname in config.designs[design]["versions"][mut]["mutated_files"]:
            if any(line in lines for line in config.designs[design]["versions"][mut]["mutated_files"][fname]):
                g.nodes[node]["class_label"] = 1


def embed_features(design, mut, ref, graph):
    # Initialise empty features
    for node in graph.nodes():
        graph.nodes[node]['features'] = []

    # Add CDFG node type feature
    embed_cdfg_node_type(graph)

    # Add AST node type count feature
    embed_ast_type_count(graph)

    # Add AST Diff feature
    embed_ast_diff(design, mut, ref, graph)

    # TODO Add Simulation feature

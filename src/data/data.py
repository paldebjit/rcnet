import random
import torch

from common.config import config
from common.utils import *
from data.constants import *
from data.features import embed_features
#from data.labels import embed_labels

import warnings  
with warnings.catch_warnings():  
    warnings.filterwarnings("ignore",category=FutureWarning)
    from torch_geometric.data import Data

def graph_to_data(g):
    x = [features for node, features in g.nodes(data="features")]
    x = torch.tensor(x, dtype=torch.float)
    
    e_s = [ g.nodes[s]['id'] for (s,d) in g.edges() ]
    e_d = [ g.nodes[d]['id'] for (s,d) in g.edges() ]

    e = torch.tensor([e_s, e_d], dtype=torch.long)

    y = [label  for node, label in g.nodes(data="class_label", default=-1) ]
    mask = [(el != -1) for el in y]

    y = torch.tensor(y, dtype=torch.float)
    mask = torch.tensor(mask, dtype=torch.bool)
    
    return Data(x=x, edge_index=e, y=y, mask=mask)

def get_input_graph(design, mut, ref):
    # Get CDFG for the mutated version
    g = get_cdfg(design, mut)

    # TODO: Keep Subgraph of COI

    # Add Node ID for all nodes
    for idx, node in enumerate(g.nodes()):
        g.nodes[node]['id'] = idx

    # Add features for all nodes
    embed_features(design, mut, ref, g)

    # Add labels for all nodes
    #embed_labels(design, mut, ref, g)

    return g

def embed_label(g):
    nodes = [ node for node, lbl in g.nodes(data="class_label", default=-1) if lbl == -1 ]
    lbl_nodes = random.sample(nodes, ZERO_LABEL_COUNT)

    for node in nodes:
        g.nodes[node]["class_label"] = 0

def gen_all_data():
    if not config.available:
        config.read_config()

    all_data = []
    for design in config.designs.keys():
        ver_dict = config.designs[design]["versions"]
        mut_ver = {key:val["base_version"] for key,val in ver_dict.items() if val["mutated"] }
        ref_ver = [key for key,val in ver_dict.items() if not val["mutated"]]

        for ver,base in mut_ver.items():
            ref = random.choice([v for v in ref_ver if ver_dict[v]["svn_rev"] < ver_dict[base]["svn_rev"]])
            print(ver, ref)
            g = get_input_graph(design, ver, ref)
            embed_label(g)
            if any(label == 1 for _, label in g.nodes(data="class_label", default=-1)):
                all_data.append(graph_to_data(g))

    return all_data

def get_all_data():
    try:
        return pickle.load(open(get_raw_dataset_path(), 'rb'))
    except:
        data = gen_all_data()
        pickle.dump(data, open(get_raw_dataset_path(), 'wb'))
        return data

if __name__ == "__main__":
    if not config.available:
        config.read_config()
    data=get_all_data()

import os

import multiprocessing as mp
import networkx as nx

from common.utils import *

from functools import partial


def get_cdfg(design, version):
    top = config.designs[design]["top"]
    fname = top + "_fused_CDFG.gpickle"

    rtl_path = get_rtl_path(design, version)
    if os.path.exists(rtl_path + "/" + fname):
        return nx.read_gpickle(rtl_path + "/" + fname)

    dmp_dir = "./goldmine_dumps/" + design + "/" + version + "/"
    run_goldmine(design, version, " -S", dmp_dir)
    
    with open(dmp_dir + "/goldmine.out/"+top+"/static/"+top+"_fused_CDFG.gpickle", 'rb') as f:
        n,e = pickle.load(f)

    g = nx.DiGraph()
    g.add_nodes_from(n)
    g.add_edges_from(e)

    nx.write_gpickle(g, rtl_path + "/" + fname)

    return g

def gen_all_cdfg():
    print("Generating all CDFGs")

    for design in config.designs.keys():
        p = mp.Pool(mp.cpu_count())
        fn = partial(get_cdfg, design)
        p.map(fn, list(config.designs[design]["versions"].keys()))


if __name__ == "__main__":
    if not config.available:
        config.read_config()

    gen_all_cdfg()

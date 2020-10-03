import glob
import os
import pickle
import shutil

import networkx as nx

from common.config import config
from common.constants import *

from networkx.drawing.nx_pydot import read_dot

def get_dataset_path():
    return config.home + "/" + config.paths["dataset"]

def get_raw_dataset_path():
    path = get_dataset_path()
    return path + ".pickle"

def get_tb_path(design, version):
    tb_path = None

    if "tb_path" in config.designs[design]:
        tb_path = config.home + "/" + PPD_DIR + "/" + design + "/"
        tb_path += config.designs[design]["tb_path"] 
        if config.designs[design]["common_tb"] == False:
            tb_path += "/" + version

    return tb_path

def get_rtl_path(design, version):
    rtl_path = config.home + "/" + PPD_DIR + "/" + design + "/"
    rtl_path += config.designs[design]["rtl_path"] + "/" + version

    return rtl_path

def get_vfile(design, version):
    rtl_path = get_rtl_path(design, version)
    out = glob.glob(rtl_path + "/**/*.v", recursive=True)
    
    excl_files = config.designs[design].get("exclude_files")
    excl_dir = config.designs[design].get("exclude_dirs")

    if excl_dir != None:
        out = [f for f in out if not any(dir_name in f for dir_name in excl_dir)] 

    if excl_files != None:
        out = [f for f in out if os.path.basename(f) not in excl_files]

    return out

def read_file(filename):
    with open(filename, 'r') as f:
        return f.readlines()

def get_signals(ast):
    signals = {'input': [], 'output': [], 'reg': [], 'wire': []}
    get_signals_(ast, signals)
    
    return signals


# TODO: Extend to multi-bit signals
def get_signals_(ast, signals):
    name = getattr(ast, "name", "")

    if (getattr(ast,"width",None) == None):
        if (ast.__class__.__name__ == 'Input'):
            signals['input'].append(name)
            signals[name] = 'input'
        elif (ast.__class__.__name__ == 'Output'):
            signals['output'].append(name)
            signals[name] = 'output'
        elif (ast.__class__.__name__ == 'Reg'):
            signals['reg'].append(name)
            signals[name] = 'reg'
        elif (ast.__class__.__name__ == 'Wire'):
            signals['wire'].append(name)
            signals[name] = 'wire'

    for c in ast.children():
        get_signals_(c, signals)



def run_goldmine(design, version, cmdline_args="", tmpdir="./rundir"):
    print("Running goldmine on: " + design + "/" + version)

    # Clean previous runs and cd to tmpdir
    cwd = os.getcwd()
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir)
    os.chdir(tmpdir)

    # Create necessary vfiles
    os.makedirs("vfiles")
    rtl_path = get_rtl_path(design, version)

    with open("vfiles/vfile_" + config.designs[design]["top"], "w") as f:
        f.write("\n".join(get_vfile(design, version)))

    # Run Goldmine
    cmd = "python " + config.paths["goldmine"] + "/src/goldmine.py"
    cmd += " -m " + config.designs[design]["top"]
    cmd += " -c " + config.designs[design]["clk"] + ":1"
    cmd += " -r " + config.designs[design]["rst"] + ":1"
    cmd += " -u " + config.paths["goldmine"]

    for dirs in config.designs[design]["include_dirs"]:
        cmd += " -I " + rtl_path + "/" + dirs

    cmd += " -F ./vfiles/vfile_" + config.designs[design]["top"]
    cmd += " " + cmdline_args
    print(cmd)
    os.system(cmd)

    # Return to original CWD
    os.chdir(cwd)

def get_cdfg(design, version):
    #run_goldmine(design, version, " -S")

    top = config.designs[design]["top"]
    
    with open("./rundir/goldmine.out/"+top+"/static/"+top+"_fused_CDFG.gpickle", 'rb') as f:
        n,e = pickle.load(f)

    g = nx.DiGraph()
    g.add_nodes_from(n)
    g.add_edges_from(e)

    return g

import glob
import os
import shutil

from common.config import config
from common.constants import *

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



#def run_goldmine(tmpdir, design, version, cmdline_args):
#    print("Running goldmine on: " + design + "/" + version)
#
#    # Clean previous runs and cd to tmpdir
#    cwd = os.getcwd()
#    if os.path.exists(tmpdir):
#        shutil.rmtree(tmpdir)
#    os.makedirs(tmpdir)
#    os.chdir(tmpdir)
#
#    # Create necessary vfiles
#    os.makedirs("vfiles")
#    rtl_path = get_rtl_path(design, version)
#
#    with open("vfiles/vfile_" + config.designs[design]["top"], "w") as f:
#        f.write("\n".join(get_vfile(design, version, config.designs[design]["exclude_files"])))
#
#    # Run Goldmine
#    cmd = "python " + config.paths["goldmine"] + "/src/goldmine.py"
#    cmd += " -m " + config.designs[design]["top"]
#    cmd += " -c " + config.designs[design]["clk"]
#    cmd += " -r " + config.designs[design]["rst"]
#    cmd += " -u " + config.paths["goldmine"]
#    cmd += " -I " + rtl_path
#    cmd += " -F ./vfiles/vfile_" + config.designs[design]["top"]
#    cmd += " " + cmdline_args
#
#    os.system(cmd)
#
#    # Return to original CWD
#    os.chdir(cwd)

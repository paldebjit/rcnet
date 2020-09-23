import os
import shutil

from common.ast import *
from common.config import config
from common.constants import *
from common.utils import *

def preprocess():
    # Directory paths
    dsn_dir = config.home + "/" + DESIGN_DIR
    ppd_dir = config.home + "/" + PPD_DIR

    # If directory already exists, delete it
    if os.path.exists(ppd_dir):
        shutil.rmtree(ppd_dir)

    # Copy design design directory
    shutil.copytree(dsn_dir, ppd_dir)

    # For each RTL file in each version of a design,
    # Replace file with AST processed file
    # This reduces readability, removes comments, replaces defines with their values
    # But helps diff with mutant verilogs easier
    for design in config.designs.keys():
        for version in config.designs[design]["versions"].keys():
            for vf in get_vfile(design, version):
                print("Processing: " + vf)
                ast = get_ast(design, version, vf)
                save_ast(ast, vf)
                # Doing it twice gives cleaner output, its just the way pyverilog works.
                ast = get_ast(design, version, vf) 
                save_ast(ast, vf)


if __name__ == "__main__":
    if not config.available:
        config.read_config()

    preprocess()

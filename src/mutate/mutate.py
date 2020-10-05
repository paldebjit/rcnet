import os
import random
import shutil

from common.ast import *
from common.config import config
from common.utils import *

from mutate.mutate_ctrl import MUTATION_TYPES
from mutate.mutate_helper import *

def mutate_file(design, version, path):
    print("MUTATING: " + path)
    mutation_type = random.choice(MUTATION_TYPES)
    ast = get_ast(design, version, path)
    nodes = get_all_nodes(ast)

    if (mutation_type == "OPERATOR"):
        return mutate_operator(ast, nodes, path)
    if (mutation_type == "SIGNAL"):
        return mutate_signal(ast, nodes, path)
    if (mutation_type == "CONSTANT"):
        return mutate_constant(ast, nodes, path)
    if (mutation_type == "OPERAND"):
        return mutate_operand(ast, nodes, path)

def gen_mutate_version(design, ref_version, new_version):
    if "max_mutations_total" in config.mutate[design]["versions"][ref_version]:
        tot_mutants = config.mutate[design]["versions"][ref_version]["max_mutations_total"]
    else:
        tot_mutants = config.mutate[design]["max_mutations_total"]

    if "max_mutations_per_file" in config.mutate[design]["versions"][ref_version]:
        pf_mutants = config.mutate[design]["versions"][ref_version]["max_mutations_per_file"]
    else:
        pf_mutants = config.mutate[design]["max_mutations_per_file"]

    new_version_rtl_path = get_rtl_path(design, new_version)
    new_version_tb_path  = get_tb_path(design, new_version)

    ref_version_rtl_path = get_rtl_path(design, ref_version)
    ref_version_tb_path = get_tb_path(design, ref_version)

    # If new version exists, clear directory config entry
    if os.path.exists(new_version_rtl_path):
        shutil.rmtree(new_version_rtl_path)

    if new_version_tb_path != None and config.designs[design]["common_tb"] == False:
        if os.path.exists(new_version_tb_path):
            shutil.rmtree(new_version_tb_path)
    
    config.designs[design]["versions"].pop(new_version, None)

    # Copy ref version to new version directory
    shutil.copytree(ref_version_rtl_path, new_version_rtl_path)
    if ( new_version_tb_path != None and config.designs[design]["common_tb"] == False):
        shutil.copytree(ref_version_tb_path, new_version_tb_path)

    # Introduce mutations
    vfiles = get_vfile(design, new_version)
    vfiles_mutant_lines = {vf: [] for vf in vfiles}
    idx = 0
    while idx < tot_mutants:
        src_file = random.choice(vfiles)
        if len(vfiles_mutant_lines[src_file]) == pf_mutants:
            vfiles.remove(src_file)
            continue

        lineno = mutate_file(design, new_version, src_file)
        if lineno == -1:
            continue

        vfiles_mutant_lines[src_file].append(lineno)
        idx += 1

    # Update design config
    config.designs[design]["versions"][new_version] = dict(mutated=True, base_version=ref_version, mutated_files={})
    config.designs[design]["versions"][new_version]["example"] = config.mutate[design]["versions"][ref_version].get("example", False)

    for key,val in vfiles_mutant_lines.items():
        if len(val) > 0:
            config.designs[design]["versions"][new_version]["mutated_files"][os.path.basename(key)] = val
    
    config.update_config()


def mutate_design(design, base_version):
    # Initialise variables
    tot_vers = config.mutate[design]["versions"][base_version]["mutated_versions"]
    mut_type = config.mutate[design]["versions"][base_version].get("type")
    if mut_type == "sequential":
        ind_vers = 1
    elif mut_type == "hybrid":
        ind_vers = config.mutate[design]["versions"][base_version]["ind_count"]
    else:
        ind_vers = tot_vers

    # Generate "tot_vers" mutated versions
    for ver in range(tot_vers):
        new_version = base_version + f'_{ver:02d}'

        if ver >= ind_vers:
            ref_ver = random.randrange(ver)
            ref_version = base_version + f'_{ref_ver:02d}'
        else:
            ref_version = base_version

        gen_mutate_version(design, ref_version, new_version)
    

def mutate_all():
    for design in config.mutate.keys():
        for version in config.mutate[design]["versions"].keys():
            mutate_design(design, version)


if __name__ == "__main__":
    if not config.available:
        config.read_config()

    #mutate_all()
    gen_mutate_version("openmsp430", "v228", "v228_00")

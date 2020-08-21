import os
import random
import shutil

from common.config import config
from common.utils import *

def mutate_file(path):
    # Create vfile
    with open("tmp_vfile", "w") as f:
        f.write(path)

    # Run mutation code
    cmd = "python " + config.paths["mutation_code"]
    cmd += " -F " + "tmp_vfile"

    os.system(cmd)

    # Copy mutated verilog file to path
    module = os.path.splitext(os.path.basename(path))[0]
    mutant_file = random.choice(os.listdir("mutant_verilog/" + module))
    shutil.copyfile("mutant_verilog/" + module + "/" + mutant_file, path)

    # Clean up
    shutil.rmtree("mutant_verilog")
    os.remove("tmp_vfile")


def gen_mutate_version(design, base_version):
    # Initialise variables
    if "max_mutations_total" in config.mutate[design]["versions"][base_version]:
        tot_mutants = config.mutate[design]["versions"][base_version]["max_mutations_total"]
    else:
        tot_mutants = config.mutate[design]["max_mutations_total"]

    if "max_mutations_per_file" in config.mutate[design]["versions"][base_version]:
        pf_mutants = config.mutate[design]["versions"][base_version]["max_mutations_per_file"]
    else:
        pf_mutants = config.mutate[design]["max_mutations_per_file"]

    tot_vers = config.mutate[design]["versions"][base_version]["mutated_versions"]
    mut_type = config.mutate[design]["versions"][base_version]["type"]
    if mut_type == "sequential":
        ind_vers = 1
    elif mut_type == "hybrid":
        ind_vers = config.mutate[design]["versions"][base_version]["ind_count"]
    else:
        ind_vers = tot_vers

    for ver in range(tot_vers):
        new_version = base_version + f'_{ver:02d}'
        new_version_rtl_path = get_rtl_path(design, new_version)
        new_version_tb_path  = get_tb_path(design, new_version)

        if ver >= ind_vers:
            ref_ver = random.randrange(ver)
            ref_version = base_version + f'_{ref_ver:02d}'
        else:
            ref_version = base_version
    
        ref_version_rtl_path = get_rtl_path(design, ref_version)
        ref_version_tb_path = get_tb_path(design, ref_version)

        # If new version exists, clear directory config entry
        if os.path.exists(new_version_rtl_path):
            shutil.rmtree(new_version_rtl_path)

        if os.path.exists(new_version_tb_path):
            shutil.rmtree(new_version_tb_path)

        config.designs[design]["versions"].pop(new_version, None)

        # Copy ref version to new version directory
        shutil.copytree(ref_version_rtl_path, new_version_rtl_path)
        shutil.copytree(ref_version_tb_path, new_version_tb_path)

        # Introduce mutations
        vfiles = get_vfile(design, new_version, config.mutate[design]["exclude_files"])
        vfiles_mutant_count = dict.fromkeys(vfiles, 0)
        idx = 0
        while idx < tot_mutants:
            src_file = random.choice(vfiles)
            if vfiles_mutant_count[src_file] == pf_mutants:
                vfiles.remove(src_file)
                continue

            mutate_file(src_file)
            vfiles_mutant_count[src_file] += 1

            idx += 1

        # Update design config
        config.designs[design]["versions"][new_version] = dict(mutated=True, base_version=ref_version)
        config.designs[design]["versions"][new_version]["mutated_files"] = [os.path.basename(key) for key,val in vfiles_mutant_count.items() if val > 0]
    
    config.update_config()


def mutate_all():
    for design in config.mutate.keys():
        for version in config.mutate[design]["versions"].keys():
            gen_mutate_version(design, version)


if __name__ == "__main__":
    if not config.available:
        config.read_config()

    mutate_all()

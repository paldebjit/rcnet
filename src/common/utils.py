import os
import shutil

from common.config import config

def get_tb_path(design, version):
    if config.designs[design]["common_sim"]:
        tb_path = config.home + "/designs/" + design + "/"
        tb_path += config.designs[design]["tb_path"] + "/" + version

    return tb_path

def get_rtl_path(design, version):
    if config.designs[design]["common_sim"]:
        rtl_path = config.home + "/designs/" + design + "/"
        rtl_path += config.designs[design]["rtl_path"] + "/" + version

    return rtl_path

def get_vfile(design, version, excl_files):
    rtl_path = get_rtl_path(design, version)

    out = []
    for vf in os.listdir(rtl_path):
        if vf.endswith(".v") and vf not in excl_files:
            out.append(rtl_path + "/" + vf)

    return out


def run_goldmine(tmpdir, design, version, cmdline_args):
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
        f.write("\n".join(get_vfile(design, version, config.designs[design]["exclude_files"])))

    # Run Goldmine
    cmd = "python " + config.paths["goldmine"] + "/src/goldmine.py"
    cmd += " -m " + config.designs[design]["top"]
    cmd += " -c " + config.designs[design]["clk"]
    cmd += " -r " + config.designs[design]["rst"]
    cmd += " -u " + config.paths["goldmine"]
    cmd += " -I " + rtl_path
    cmd += " -F ./vfiles/vfile_" + config.designs[design]["top"]
    cmd += " " + cmdline_args

    os.system(cmd)

    # Return to original CWD
    os.chdir(cwd)

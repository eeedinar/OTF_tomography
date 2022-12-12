#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python
import argparse
from genericpath import isfile
import glob
import json
import os
import shutil
import subprocess
import sys
from shutil import copy2
import ast
import textwrap

from rln_helpers import *
from star_helpers import *

def run_cryolo():
    """
    Runs cryolo - checks to see if any files exist in motioncor directory before running
    Makes symlinks to recently generated files which are then low pass filtered
    Low pass filtered micrographs are given to cryolo to pick before temp directories are emptied ready for new files
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--o", type=str, help="outputdir")
    parser.add_argument("--in_mics", type=str, help="inputfile")
    parser.add_argument("--j", type=str, help="threads")
    parser.add_argument("--g", type=str, help="GPU ids", default=0)
    parser.add_argument("--boxsize", type=str, help="boxsize")
    parser.add_argument("--t", "--threshold", type=str, help="threshold")
    parser.add_argument("--model", type=str, help="Path to cryolo model")
    parser.add_argument("--extract_folder", type=str, help="Extract_folder")
    args = parser.parse_args()
    args.log_out, args.log_err = rln_init_log(args)
    rln_alias(args, "Cryolo", True)


    # Create config file for Cryolo
    config_string = {
        "model": {
            "architecture": "PhosaurusNet",
            "input_size": 1024,
            "anchors": [int(args.boxsize), int(args.boxsize)],
            "max_box_per_image": 700,
            "num_patches": 1,
            "filter": [0.1, f"{args.o}tmp_filtered"]
        },
        "other": {
            "log_path": f"{args.o}logs/"
        }
    }
    with open(f'{args.o}config.json', 'w+', encoding='utf-8') as f:
        json.dump(config_string, f, ensure_ascii=False, indent=4)

    # Give Relion node information for this job
    # https://github.com/3dem/relion/blob/ver4.0/src/pipeline_jobs.h

    node_string = f'''\
    data_output_nodes
    loop_
    _rlnPipeLineNodeName #1
    _rlnPipeLineNodeTypeLabel #2
    {args.o}autopick.star MicrographsCoords.star.relion.autopick
    '''

    with open(f'{args.o}RELION_OUTPUT_NODES.star', 'w+', encoding='utf-8') as f:
        f.write(textwrap.dedent(node_string))

    # Cryolo Parameters
    cryolo_version = '1.8.2_cu11'
    cryolo_executable = f'/programs/x86_64-linux/cryolo/{cryolo_version}/bin.capsules/cryolo_predict.py'
    

    with open("OTF/train_iter", "r+") as f:
        train_iter = f.read()
    with open("OTF/train_model", "r+") as f:
        train_model = f.read()
    with open("OTF/predict_model", "r+") as f:
        predict_model = f.read()

    # Model iteration
    # with open("relion_it_options.py", "r+") as f:
    #     opts = ast.literal_eval(f.read())
    # cryolo_model = opts["cryolo_train_model"]

    cryolo_model = predict_model
    args.log_out.info(f"Current Training Iteration: {train_iter}")
    args.log_out.info(f"Latest Training Model: {train_model}")
    args.log_out.info(f"Latest Cryolo Run: {predict_model}")
    if train_model != predict_model:
        cryolo_model = train_model
    args.log_out.info(f"Current model: {cryolo_model}")

    
    

    # if os.path.exists(f"{args.o}last_used_model"):
    #     with open(f"{args.o}last_used_model", "r+") as f:
    #         last_used_model = f.read()
    
        # if last_used_model != cryolo_model:
            # extract_parts = glob.glob("Extract/job*/particles.star")
            # extract_parts.sort(key=os.path.getmtime)
            # with open(extract_parts[-1], "w+") as f: pass

            # extract_raw_data = glob.glob("Extract/job*/Raw_data/")
            # extract_raw_data.sort(key=os.path.getmtime)
            # shutil.rmtree(extract_raw_data[-1])

            # with open(f"{args.o}cryolo_processed.txt", "w+") as f: pass

    # Make sure the Cryolo version specified exists
    if not os.path.exists(cryolo_model):
        args.log_err.info(f"Cryolo model {cryolo_model} was not found -- exiting...")
        rln_failure(args)
        sys.exit(1)

    # Make sure the Cryolo exe specified exists
    if not os.path.exists(cryolo_executable):
        args.log_err.info(f"Cryolo executable {cryolo_executable} was not found -- exiting...")
        rln_failure(args)
        sys.exit(1)

    args.log_out.info("Setup complete, starting Cryolo...")

    os.makedirs(f"{args.o}STAGE", exist_ok=True)
    cwd = os.getcwd()

    # Grab list of all micrographs processed
    processed_file = f'{args.o}processed.star'
    if os.path.exists(processed_file):
        dfs = load_starfile(processed_file)
        df_processed = dfs[0]
    else:
        df_processed = pd.DataFrame(columns=["_rlnMicrographName"])

    # Grab list of all micrographs present
    df_optics, df_micrographs = load_starfile(args.in_mics)
    df_mcorr = df_micrographs[["_rlnMicrographName"]]
    mic_path = os.path.dirname(df_mcorr.iloc[0][0])

    # Create list of all micrographs not yet processed
    df_merge = df_mcorr.merge(df_processed, how="left", indicator=True)
    df_unprocessed = df_merge.loc[df_merge["_merge"] == "left_only"]
    df_unprocessed = df_merge.drop(columns="_merge")

    if df_unprocessed.empty:
        args.log_out.info('No new .mrc files for Cryolo, skipping...')
        rln_success(args)
        return

    # Make links in staging
    for file in df_unprocessed["_rlnMicrographName"].tolist():
        source = f"{cwd}/{file}"
        dest = f"{cwd}/{args.o}STAGE/{os.path.basename(file)}"
        if not os.path.exists(dest):
            os.symlink(source, dest)

    args.log_out.info(f"Picking using {cryolo_model}")


    ### RUN CRYOLO
    cmd = f'{cryolo_executable} -c {args.o}config.json -w {cryolo_model} -i {args.o}STAGE/ \
    -t {args.t} -o {args.o} --cleanup -g {args.g}'

    # rln_liveoutput(args, cmd)
    run_output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    # args.log_out.info(run_output.stdout)
    with open(f"{args.o}cryolo.out", "a+") as f:
        f.write(run_output.stdout)
    # args.log_out.info("Cryolo finished, cleaning up...")


    ### POST-RUN
    cmd = f'rm {args.o}STAGE/*.mrc'
    subprocess.run(cmd, shell=True)

    df_processed = df_merge.drop(columns="_merge")
    df_processed.attrs['name'] = "df_processed"
    write_starfile([df_processed], processed_file)

    # Enable autopick viewing in Relion
    autopick_header = f'''\
    data_coordinate_files
    loop_
    _rlnMicrographName #1
    _rlnMicrographCoordinates #2
    '''

    mrc_files = [f"{mic_path}/{file.replace('.star', '.mrc')}" for file in os.listdir(f'{args.o}STAR')]
    coordinate_files = [f'{args.o}STAR/{file}' for file in os.listdir(f'{args.o}STAR')]

    with open(f'{args.o}autopick.star', 'w+') as f:
        f.write(textwrap.dedent(autopick_header))
        for mrc, coord in zip(sorted(mrc_files), sorted(coordinate_files)):
            f.write(f"{mrc} {coord}\n")

    # with open(f"{args.o}last_used_model", "w+") as f:
    #     f.write(cryolo_model)

    with open("OTF/predict_model", "w+") as f:
        f.write(cryolo_model)





    args.log_out.info("Done!")
    rln_success(args)
    return


if __name__ == "__main__":
    run_cryolo()

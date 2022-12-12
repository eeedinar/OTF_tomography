#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python
import os, argparse, time, subprocess
from distutils.util import strtobool

def main(args):
    debug = args.debug
    if debug:
        print('rsync program is running')
    ### Parameters
    runtime_hr      = args.runtime     # in hours 0.3 = 18 mins
    SOURCE_DATA_DIR = args.source      # /.../Intermediate_DATA/Intermediate_DATA/
    DES_DATA_DIR    = args.destination # /.../Raw_data/"
    # SOURCE_META_DIR = "/nfs/vast/emcenter/aalbashit/tm_tutorial/Intermediate_META/"
    # DES_META_DIR    = "/nfs/vast/emcenter/aalbashit/tm_tutorial/Meta_data/"
    clean_source    = False  ### True - remove source file
    LOG_OUTPUT      = os.path.join(DES_DATA_DIR,"rsync-tomo.out")

    ### create folder if not exist in the current folder
    def create_folder_if_not(folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder        # ex. motioncor_stacks

    # Program run only for RUN_TIME_HR hours
    endtime = time.time() + (3600 * runtime_hr)
    while time.time() < endtime:

        cmd = f'find {os.path.join(SOURCE_DATA_DIR)} -type f -mmin +5 | xargs -r -P5 -n1 -I% rsync -ltrv % {create_folder_if_not(os.path.join(DES_DATA_DIR))} | tee -a {LOG_OUTPUT}'
        if clean_source == True:
            cmd += " --remove-source-files"
        run_output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        # with open(f'{DES_DATA_DIR}/{LOG_OUTPUT}', "a+") as f:
        #     f.write(run_output.stdout)
        #     if run_output.stderr != "":
        #         f.write(run_output.stderr)

        time.sleep(60)

    print(f'Copying finished!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Argument for file transfer to Raw_data")
    parser.add_argument('-s', '--source',      type=str,   metavar='', required=True, help= "Absolute folder path where data will be copied from")
    parser.add_argument('-d', '--destination', type=str,   metavar='', required=True, help= "Absolute folder path where data will be copied to")
    parser.add_argument('-r', '--runtime',     type=float, metavar='', required=True, help= "Absolute folder path where data will be copied to")
    parser.add_argument('--debug',       type=lambda x:bool(strtobool(x)), nargs='?', const=True, default=False,  help= "Please enter 1 to debug")
    args = parser.parse_args()

    main(args)

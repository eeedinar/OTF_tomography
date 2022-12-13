#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python

### import packages
import os, argparse, time, subprocess, json
import pandas as pd
from distutils.util import strtobool

# Aretomo environment
os.environ["ARETOMO_X"] = "1.3.3"

### function to look for certain extension or static names containing files
def cwd_files_search_with(seek_str, search_where = 'end', directory = None):
    """
        files_sorted = cwd_files_search_with('.h5')
    """
    directory = os.getcwd() if directory == None else directory
    files = []
    if search_where == 'end':
        for file in [each for each in os.listdir(directory) if each.endswith(seek_str)]:
            files.append(file)

    elif search_where == 'start':
        for file in [each for each in os.listdir(directory) if each.startswith(seek_str)]:
            files.append(file)

    files_sorted = sorted(files)
    return files_sorted  # ex. ['23april2021_pl4g1meta_k1_64kx_d1_010.mrc.mdoc']

### create folder if not exist in the current folder
def create_folder_if_not(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder        # ex. motioncor_stacks

### unequal level of list depth/nesting
def flatten(S):
    """
    l = [2,[[1,2]],1]
    list(flatten(l))
    """
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])

def main(args):
    debug = args.debug
    if debug:
        print('Processing Program is running ...')
    
    ### Program location and parameters
    PWD            = args.working_dir           # project root directory where Raw_data, log files will be created --> /../tm_tutorial/ 
    DATA_DIR       = "Raw_data"                 # tif, mdoc, and mrc will be stored here
    LOG_FILE       = 'program_run.log'          # log file where the execution time is noted
    MOTION_COR_DIR = "motioncor_stacks"         # aligned motion corrected mrc is generated here
    ALIGNFRAMES_ARGS =  [ "-pixel", f'{args.pixel_size}']   # parameters to pass each time alignframes command is called - must be in the form of list ["-rfsum", "7", "-pixel", "0.138"]
    ARETOMO_DIR     = 'tomograms'
    ARETOMO_ARGS    = ["-VolZ", "1500", "-OutBin", "8" ,"-FlipVol" ,"1", "-OutImod" ,"1", "-OutXF" ,"1"]
    RUN_TIME_HR     = args.runtime ## in hours 0.3 = 18 mins
    PROG_CMD_LOG    = 'prog_cmds.log'

    ### log file for json
    listObj = []
    log_cmd = os.path.join(PWD, PROG_CMD_LOG)
    if os.path.isfile(log_cmd) is False:  # check if exist, if not, create
        with open(log_cmd, 'w') as json_file:
            json.dump(listObj, json_file, indent=4)
    with open(log_cmd) as fp:             # read current log file
        listObj = json.load(fp)

    # Program run only for RUN_TIME_HR hours
    endtime = time.time() + (3600 * RUN_TIME_HR)
    while time.time() < endtime:
        mdoc_list_all = cwd_files_search_with("mdoc", search_where = 'end', directory = create_folder_if_not(os.path.join(PWD, DATA_DIR)))
        mdoc_list     = mdoc_list_all.copy()   ## mdoc_list_all may contain mdoc but not all files copy yet that will be dropped in 

        ### check if already computed the mdoc files
        try:
            df = pd.read_csv(os.path.join(PWD,LOG_FILE))
            for i in df['mdoc_file'].tolist():     # df['mdoc_file'].tolist()   # ['/nfs/vast/emcenter/aalbashit/tm_tutorial/Raw_data/23april2021_pl4g1meta_k1_64kx_d1_010.mrc.mdoc']
                base_name = os.path.basename(i)
                if base_name in mdoc_list:
                    mdoc_list.remove(base_name)
        except: # no log file exit so create dataframe
            df = pd.DataFrame([], columns=['command','mdoc_file', 'exec_st_time', 'exec_end_time', 'run_time(mins)', 'gen_file', 'status']) 

        if debug:
            print(f"{time.strftime('%m/%d/%Y %A %H:%M:%S', time.localtime())}: - No new mdoc file to process")

        ### check all 'tif'
        word = 'SubFramePath'
        RotationAndFlip_dict = {}
        for mdoc_file in mdoc_list_all:
            files_list = []
            with open(os.path.join(PWD, DATA_DIR,mdoc_file), 'r') as fp:
                # read all lines in a list
                lines = fp.readlines()
                for line in lines:
                    # check if string present on a current line
                    if line.find(word) != -1:
                        files_list.append(line.split("=")[1].strip().split('\\')[-1])  # print('Line Number:', lines.index(line))

            rot_flip_var = 0

            for file in files_list:
                if os.path.exists(os.path.join(PWD, DATA_DIR,file))==False:
                    mdoc_list.remove(mdoc_file)
                    rot_flip_var = 1
                    break
            if rot_flip_var == 0:
                
                ## if Microscope == “Talos” then -rfsum 2  - otherwise leave as rfsum 7
                RotationAndFlip_dict[mdoc_file] = "2" if args.microscope=='talos' else "7"
                ## -rfsum parameter extraction from header
                # p = subprocess.run(["header", "--sbapp:a", "imod", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True )
                # search_str = p.stdout   # '\n RO image file on unit:  1 ...
                # idx = search_str.find("need")    # 1369
                # RotationAndFlip_dict[mdoc_file] = search_str[idx:].split('\n')[0][5:].strip() if idx != -1 else '7'  ### default rotation flip is 0


        ### if not computed do alignment
        for mdoc_file in mdoc_list:

            START = time.strftime('%m/%d/%Y %A %H:%M:%S', time.localtime())
            tic = time.perf_counter()

            mdoc_file_base_string = mdoc_file.split(".mrc.mdoc")[0]            ### split mdoc extension and get the string
            alignframes_output_file_name = mdoc_file_base_string + "_aligned.mrc"     ### output file name for alignframes

            # alignframes -mdoc Raw_data/23april2021_pl4g1meta_k1_64kx_d1_010.mrc.mdoc -path /nfs/vast/emcenter/aalbashit/tm_tutorial/Raw_data -rfsum 7 -pixel 0.138 -output motioncor_stacks/pl4g1meta_k1_64kx_d1_010_aligned.mrc
            args_rf = ['alignframes', '-mdoc', os.path.join(PWD, DATA_DIR, mdoc_file), '-path', os.path.join(PWD, DATA_DIR), '-rfsum', RotationAndFlip_dict[mdoc_file], ALIGNFRAMES_ARGS, '-output', os.path.join(create_folder_if_not(os.path.join(PWD,MOTION_COR_DIR)), alignframes_output_file_name)]
            cmd_align = flatten(args_rf)
            if args.super_res:
                print(f'super resoution is turned on - add argument later ...')

            if debug:
                print(f'alignframes Processing {mdoc_file}\n{" ".join(cmd_align)}')

            p = subprocess.run(cmd_align, stdout=subprocess.PIPE, stderr = subprocess.PIPE  , text=True )   #     print(p1.stdout)  stdout=sys.stdout, stderr = sys.stderr   stdout=subprocess.PIPE, stderr=subprocess.PIPE
            with open(f'{os.path.join(create_folder_if_not(os.path.join(PWD, MOTION_COR_DIR)), alignframes_output_file_name.split(".mrc")[0])}.log','w') as f:
                f.write(p.stdout)
                f.write(p.stderr)
            error_ = 0
            if p.returncode!=0:
                error_ = 1
            # log information into dataframe
            FINISH = time.strftime('%m/%d/%Y %A %H:%M:%S', time.localtime())
            tac = time.perf_counter()
            df.at[len(df)] = ['alignframes', mdoc_file, START, FINISH, (tac-tic)/60, alignframes_output_file_name, 'success' if error_==0 else 'failed/corrupted']
            if error_ == 1:
                if debug:
                    print(f'alignframes Processing for {mdoc_file} has processing error')
                continue
            # Aretomo starts here
            START = time.strftime('%m/%d/%Y %A %H:%M:%S', time.localtime())
            tic = time.perf_counter()

            # Tilt axis angle search
            p = subprocess.run(['header', os.path.join(PWD, MOTION_COR_DIR, alignframes_output_file_name)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True )
            search_str = p.stdout   # '\n RO image file on unit:  1 ...
            idx = search_str.find("Tilt axis angle")    # 1369
            tilt_axis_angle = search_str[idx:].split("=")[1].split(",")[0].strip()  # print(tilt_axis_angle) '174.3' from search_str[idx:] = 'Tilt axis angle = 174.3, binning = 1  spot = 3  camera = 1 bidir = 0.0      \n 

            cmd_aretomo = flatten(['AreTomo', '-InMrc' ,os.path.join(PWD, MOTION_COR_DIR, alignframes_output_file_name), '-OutMrc', os.path.join(create_folder_if_not(os.path.join(PWD,ARETOMO_DIR)), mdoc_file_base_string + "_TS.mrc"), ARETOMO_ARGS , '-TiltAxis', tilt_axis_angle])
            if debug:
                print(f'AreTomo Processing {mdoc_file}\n{" ".join(cmd_aretomo)}')

            p = subprocess.run(cmd_aretomo, stdout=subprocess.PIPE, stderr = subprocess.PIPE ,  text=True )   #     print(p.stdout)  stdout=sys.stdout, stderr = sys.stderr   stdout=subprocess.PIPE, stderr=subprocess.PIPE        
            with open(f'{os.path.join(create_folder_if_not(os.path.join(PWD, ARETOMO_DIR)), mdoc_file_base_string)}_TS.log','w') as f:
                f.write(p.stdout)
                f.write(p.stderr)

            error_ = 0
            if p.returncode!=0:
                error_ = 1
            try:
                ### renaming tomo file
                # print(os.path.isfile(os.path.join(PWD,ARETOMO_DIR, mdoc_file_base_string + "_TS", 'tomogram.mrc')))
                # os.rename(os.path.join(PWD,ARETOMO_DIR, mdoc_file_base_string + "_TS", 'tomogram.mrc'), os.path.join(PWD,ARETOMO_DIR, mdoc_file_base_string + "_TS", mdoc_file_base_string + "_TS" + ".mrc"))
                if debug:
                    print('Aretomo output mrc file creation was successful')
            except:
                error_ = 1
                if debug:
                    print('Aretomo output mrc file renaming failed')
            FINISH = time.strftime('%m/%d/%Y %A %H:%M:%S', time.localtime())
            tac = time.perf_counter()
            df.at[len(df)] = ['AreTomo', alignframes_output_file_name, START, FINISH, (tac-tic)/60, mdoc_file_base_string + "_TS.mrc", 'success' if error_==0 else 'failed/corrupted']

            log = { "mdoc file"             : mdoc_file,
                "Time"                      : time.strftime('%m/%d/%Y %A %H:%M:%S', time.localtime()),
                "Project directory"         : PWD,
                "Data folder"               : DATA_DIR,
                "Log file"                  : LOG_FILE,
                "Alignframes log directory" : MOTION_COR_DIR,
                "Aretomo log directory"     : ARETOMO_DIR,
                "Program parameter log file": PROG_CMD_LOG,
                "Email notification log files" : 'run.out and run.err',
                "rsync log file"            : 'Raw_data/rsync-tomo.out',
                "Pixel size"                : args.pixel_size,
                "Exposure rate"             : args.exposure_rate,
                "Super resolution"          : args.super_res,
                "Alignframes command"       : " ".join(cmd_align),
                "AreTomo command"           : " ".join(cmd_aretomo)}

            listObj.append(log)
            with open(log_cmd, 'w') as json_file:
                json.dump(listObj, json_file, indent=4)

            if debug:
                print(f'AreTomo finished processing for {mdoc_file}')
                print(f'{PROG_CMD_LOG} created')
        df.to_csv(os.path.join(PWD,LOG_FILE),mode='w',index=False)   # rewrite the  to log file
        time.sleep(60)                                      # wait before starting a loop

    print('Alignment Program Finished')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Argument for file transfer to Raw_data")
    parser.add_argument('-w', '--working_dir',   type=str,   metavar='', required=True,  help = "Project working directory")
    parser.add_argument('-r', '--runtime',       type=float, metavar='', required=True,  help = "Please enter program runtine in hours")
    parser.add_argument('-p', '--pixel_size',    type=float, metavar='', required=True,  help = "Please enter pixel size")
    parser.add_argument('-E', '--exposure_rate', type=float, metavar='', required=True,  help = "Please enter exposure rate")
    parser.add_argument('-m', '--microscope',    type=str,   metavar='', required=True,  help= "Please enter microscope")
    parser.add_argument('--debug',       type=lambda x:bool(strtobool(x)), nargs='?', const=True, default=False,  help= "Please enter 1 to debug")
    parser.add_argument('--super_res',       type=lambda x:bool(strtobool(x)), nargs='?', const=True, default=False,  help= "Please enter 1 to super resolution")
    args = parser.parse_args()

    main(args)

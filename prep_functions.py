#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python
import ast
import datetime
import glob
import os
import time
import traceback
import pandas as pd
import logging
import argparse
from distutils.util import strtobool

"""
    Parameters
    ----------
    args.do_monitor : bool
        Enable write-out of monitoring and check to production.
        
    args.email : str
        Email of user.
        
    args.log_out: logging.Logger object
        Outputs to "run.out".
        
    args.log_err: logging.Logger object
        Logs to "run.err".
        
    args.microscope : str
        The name of the microscope.  
        
    args.output : str
        The job output directory.
"""

def tomo_init_log(args):
    formatter = logging.Formatter('%(asctime)s [%(funcName)s]: %(message)s', datefmt='[%I:%M%p]')

    log_out = logging.getLogger('out')
    log_out.setLevel(logging.INFO)
    handler_out = logging.FileHandler(f'{args.o}run.out', mode='a+')
    handler_out.setFormatter(formatter)
    log_out.addHandler(handler_out)

    log_err = logging.getLogger('err')
    log_err.setLevel(logging.INFO)
    handler_err = logging.FileHandler(f'{args.o}run.err', mode='a+')
    handler_err.setFormatter(formatter)
    log_err.addHandler(handler_err)

    return log_out, log_err

def main(args):
    debug = args.debug
    if debug:
        print('Email program is running')
    """
    Function
    ----------
    Checks last movie copied - if unchanged for 20 mins create txt for automatic monitoring.
    """
    # print('Notification system is running ...')
    try:
        # Make microscope names lowercase for filenaming purposes
        # args.microscope = args.microscope.lower()

        # Skip check if no files are present yet in Raw_data/
        try:
            filelist = glob.glob('Raw_data/*.tif')
            latest_file = max(filelist, key=os.path.getmtime)
        except:
            args.log_out.info('No micrographs found in "Raw_data/", skipping check...')
            if debug:
                print('No micrographs found in "Raw_data/", skipping check...')
            return

        # Write to file if no new data in 1200 sec
        latest_time = os.path.getmtime(latest_file)
        if latest_time < (time.time() - 1200):
            args.log_out.info(
                f"No new micrographs found in 20 minutes --"
            )
            if debug:
                print('run.out file written')
            formatted_latest_time = datetime.datetime.fromtimestamp(latest_time).strftime("%b %d %Y, %H:%M")
            current_mics = len(os.listdir("Raw_data"))
            output = [
                f" {args.email}:", f" {args.microscope} has stopped collecting data for over 20 mins!",
                f" {current_mics} micrographs currently collected, the last micrograph",
                f" was {latest_file} at {formatted_latest_time}.\n"
            ]

            production_stop_path = f"/nfs/boston/EM_Logs/{args.microscope}_tomo_stop.txt"
            rln_stop_path = f"{args.o}{args.microscope}_stop.txt"

            with open(rln_stop_path, 'w+') as rln_file:
                rln_file.writelines(output)
                if debug:
                    print(f'{rln_stop_path} file is written')
            if args.do_monitor:
                if os.path.exists("/nfs/boston/EM_Logs/"):
                    with open(production_stop_path, "w+") as production_file:
                        production_file.writelines(output)
                        if debug:
                            print(f'{production_stop_path} file is written')
                        args.log_out.info(
                            f'Stop info written to "/nfs/boston/EM_Logs/monitoring_{args.microscope}_stop.txt".')
        else:
            args.log_out.info('New micrographs found in "Raw_data/", skipping check...')

    except Exception:
        args.log_err.warning('\n' + traceback.format_exc())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o",      type=str,   metavar='', required=True, help= "outputdir to write run.out and run.err")
    parser.add_argument('-e', '--email',       type=str,   metavar='', required=True, help= "Please enter email ID")
    parser.add_argument('-d', '--do_monitor',  type=bool,  metavar='', required=True, help= "check to send email notification")
    parser.add_argument('-m', '--microscope',  type=str,   metavar='', required=True, help= "Please enter microscope")
    parser.add_argument('-r', '--runtime',     type=float, metavar='', required=True,  help = "Please enter program runtine in hours")
    parser.add_argument('--debug',     type=lambda x:bool(strtobool(x)), nargs='?', const=True, default=False,  help= "Please enter 1 to debug")

    args = parser.parse_args()
    args.log_out, args.log_err = tomo_init_log(args)
    RUN_TIME_HR = args.runtime ## in hours 0.3 = 18 mins
    # Program run only for RUN_TIME_HR hours
    endtime = time.time() + (3600 * RUN_TIME_HR)
    while time.time() < endtime:
        main(args)
        time.sleep(60*5)                                      # wait 5 mins before starting a loop

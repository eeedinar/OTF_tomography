#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python
import subprocess, argparse, datetime
from multiprocessing import Process
from threading import Thread
import os, sys
from distutils.util import strtobool

def data_transfer(args):
    username = args.username
    runtime  = str(args.runtime)  # argument passed must be str type
    debug = str(args.debug)
    cmd = [args.python_path, os.path.join(args.prog_loc,'transfer_data.py'), \
                        '--source',  os.path.join(args.source_dir,'')  , \
                        '--destination', os.path.join(args.working_dir,'Raw_data',''), '--runtime', runtime, '--debug', debug ]
    subprocess.run(cmd, stdout=sys.stdout, stderr = sys.stderr , text=True)

def alignment(args):
    microscope = args.microscope.lower()
    runtime  = str(args.runtime)            # argument passed must be str type
    pixel_size = str(round(args.pixel_size/10,3))    # angstrom to nm
    debug = str(args.debug)
    super_res = str(args.super_res)
    exposure_rate = str(args.exposure_rate)
    cmd = [args.python_path, os.path.join(args.prog_loc, 'alignment.py'), \
                        '--working_dir', os.path.join(args.working_dir,''), '--exposure_rate', exposure_rate, \
                        '--pixel_size', pixel_size, '--runtime', runtime, '--microscope', microscope, '--debug', debug, '--super_res', super_res ]
    subprocess.run(cmd, stdout=sys.stdout, stderr = sys.stderr ,   text=True)  #     print(p.stdout)  stdout=sys.stdout, stderr = sys.stderr   stdout=subprocess.PIPE, stderr=subprocess.PIPE        

def email_notifications(args):
    microscope = args.microscope.lower()
    runtime  = str(args.runtime)            # argument passed must be str type
    debug = str(args.debug)
    cmd = [args.python_path, os.path.join(args.prog_loc, 'prep_functions.py'), \
                        '-o', os.path.join(args.working_dir,''), '-e', args.email, '-d', '0', '-m', microscope, '--runtime', runtime, '--debug', debug ]
    subprocess.run(cmd, stdout=sys.stdout, stderr = sys.stderr ,   text=True)  ## -d 0 means do not send email 1 = send email (write text in production dir)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Argument for file transfer to Raw_data")
    parser.add_argument('-u', '--username',      type=str,   metavar='', required=True,  help= "Please enter username")
    parser.add_argument('-e', '--email',         type=str,   metavar='', required=False, help= "Please enter email ID")
    parser.add_argument('-r', '--runtime',       type=float, metavar='', required=True,  help= "Please enter program runtine in hours")
    parser.add_argument('-p', '--pixel_size',    type=float, metavar='', required=True,  help= "Please enter pixel size")
    parser.add_argument('-E', '--exposure_rate', type=float, metavar='', required=True, help= "Please enter exposure rate")
    parser.add_argument('-m', '--microscope',    type=str,   metavar='', required=True,  help= "Please enter microscope")
    parser.add_argument('-c', '--working_dir',   type=str,   metavar='', required=True,  help= "Please enter project directory")
    parser.add_argument('-s', '--source_dir',    type=str,   metavar='', required=True,  help= "Please enter source directory where the Raw_data will be copied from")
    parser.add_argument('--python_path', type=str,   metavar='', required=True,  help= "Please enter python path")
    parser.add_argument('-l', '--prog_loc',      type=str,   metavar='', required=True,  help= "Please enter where programs are located")
    parser.add_argument('--debug',       type=lambda x:bool(strtobool(x)), nargs='?', const=True, default=False,  help= "Please enter 1 to debug")
    parser.add_argument('--super_res',       type=lambda x:bool(strtobool(x)), nargs='?', const=True, default=False,  help= "Please enter 1 to super resolution")

    args = parser.parse_args()
    p1 = Thread(target=data_transfer, args = (args,))  # p1 = Process(target=data_transfer)  p1 = Thread(target=data_transfer)
    p2 = Thread(target=alignment, args = (args,))                      # p2 = Process(target=alignment)  p2 = Thread(target=alignment)
    p3 = Thread(target=email_notifications, args = (args,))            # p3 = Process(target=email_notifications)  p2 = Thread(target=email_notifications)

    p1.start()
    p2.start()
    p3.start()

    d = datetime.datetime.now()
    print(f'Program finishes in {args.runtime} hours, approximately {datetime.datetime(year = d.year, month = d.month, day = d.day, hour = d.hour, minute = d.minute, second = d.second)+ datetime.timedelta(hours = args.runtime, minutes=3)} mins')

    p1.join()
    p2.join()
    p3.join()
#!/programs/x86_64-linux/python/3.7.0/bin.capsules/python

import subprocess
  
  
pytonProcess = subprocess.check_output("ps -ef | grep .py",shell=True).decode()
pytonProcess = pytonProcess.split('\n')
  
for process in pytonProcess:
    print(process)
import sys
import json
import os

filename = 'program_commands.log'
listObj = ['Hi']

if os.path.isfile(filename) is False:
    with open(filename, 'w') as json_file:
        json.dump(listObj, json_file, indent=4)

with open(filename) as fp:
    listObj = json.load(fp)

listObj.append({"Name":"Din"})
with open(filename, 'w') as json_file:
    json.dump(listObj, json_file, indent=4)
print(listObj)


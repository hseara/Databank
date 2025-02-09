#Organize experimental data into a databank
#Amount of each molecule in the membrane is given as a ratio. For a membrane of single molecule it's 1.

import os
import numpy as np

import yaml
import json

data_file ="/media/osollila/Data/NMRlipids/Databank/Data/experiments/10.1039/c2cp42738a/5/POPC_Order_Parameters.dat"

save_dir = "/media/osollila/Data/NMRlipids/Databank/Data/experiments/10.1039/c2cp42738a/5"

#experiment information

#save_info = {}
#save_info['DOI'] = "10.5281/zenodo.47488647"
#save_info['TEMPERATURE'] = 310
#save_info['MOLECULE_FRACTIONS'] = {'POPE': 1}
#print(save_info)

#outfileDICT = str(save_dir) + '/README.yaml'
    
#with open(outfileDICT, 'w') as f:
#    yaml.dump(save_info,f, sort_keys=False)


#write data in json

outfile = save_dir + "/POPC_Order_Parameters.json"
data = {}

with open(data_file) as OPfile:
    lines=OPfile.readlines()
    for line in lines:
        if "#" in line or line == "\n":
            continue
        print(line.split())
        OPname = line.split()[0] + " " + line.split()[1]
        OPvalues = [float(line.split()[2])] #, float(line.split()[3])]
        data[str(OPname)]=[]
        data[str(OPname)].append(OPvalues)
        
        with open(outfile, 'w') as f:
            json.dump(data,f)


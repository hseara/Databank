import os
import sys
import yaml
import json
import matplotlib.pyplot as plt
import numpy as np
import math
import argparse

from random import randint

from matplotlib import cm
from scipy.stats import norm

import urllib.request
from urllib.error import URLError,HTTPError,ContentTooShortError

sys.path.insert(1, '../BuildDatabank/')
from databankLibrary import download_link, lipids_dict, read_trajs_calc_OPs, parse_op_input, find_OP, OrderParameter
import buildH_calcOP_test


#order parameters or quality analysis
parser = argparse.ArgumentParser(description="")
parser.add_argument("-op",action='store_true', help="Calculate order parameters for simulations in data bank "
                        "format.")
parser.add_argument("-q",action='store_true', help="Quality evaluation of simulated order parameters "
                        "format.")
args = parser.parse_args()

lipid_numbers_list = lipids_dict.keys() # should contain all lipid names
#################################
class Simulation:
    def __init__(self, readme, data, indexingPath):
        self.readme = readme
        self.data = data #dictionary where key is the lipid type and value is order parameter file
        self.indexingPath = indexingPath
        
    def getLipids(self, molecules=lipid_numbers_list):
        lipids = []
        for key in molecules:
            try:
                if self.readme['N'+key] != [0,0]: 
                    lipids.append(key)
            except KeyError:
                continue
        return lipids     
        
class Experiment:
    pass
    
###########################################3

# # Analysis starts here

if args.op:
    for subdir, dirs, files in os.walk(r'../../Data/Simulations/'):
        FileFound = False
        
        for filename1 in files:
            filepath = subdir + os.sep + filename1
            #print(filepath)
            if filepath.endswith("OrderParameters.json"): 
                print("Order parameters exist in " + filepath)               
                FileFound = True

        for filename1 in files:
            if FileFound:
                break
            filepath = subdir + os.sep + filename1
            print(filepath)
            if filepath.endswith("README.yaml"):
                READMEfilepathSimulation = subdir + '/README.yaml'
                with open(READMEfilepathSimulation) as yaml_file_sim:
                    sim = yaml.load(yaml_file_sim, Loader=yaml.FullLoader)
                    indexingPath = "/".join(filepath.split("/")[4:8])
                    print(indexingPath)
                    #download files to
                    DATAdir = '../../Data/Simulations/' + indexingPath
                    #  dir_wrk = "/media/akiirikk/DATADRIVE1/tietokanta/Data/tmp/DATABANK/"
                    #  dir_tmp = os.path.join(dir_wrk, "tmp_6-" + str(randint(100000, 999999)))
                    # if (not os.path.isdir(dir_tmp)): 
                    #     os.mkdir(dir_tmp)
                
                    print("Calculating order parameters for all C-H bonds using the mapping file")
                
                    doi = sim['DOI']
                    trj=sim['TRJ'][0][0]
                    tpr=sim['TPR'][0][0]
                    trj_name = DATAdir + '/' + trj
                    tpr_name = DATAdir + '/' + tpr
                    trj_url = download_link(doi, trj)
                    tpr_url = download_link(doi, tpr)
                
                
                    #Download tpr and xtc files to a tmp directory in dir wrk defined in readme file / or should these be put into the same directory as README.yaml ???
                    if (not os.path.isfile(tpr_name)):
                        response = urllib.request.urlretrieve(tpr_url, tpr_name)
                        
                    if (not os.path.isfile(trj_name)):
                        response = urllib.request.urlretrieve(trj_url, trj_name)
                
                
                
                    software=sim.get('SOFTWARE')
                    EQtime=float(sim.get('TIMELEFTOUT'))*1000
                    unitedAtom = sim.get('UNITEDATOM_DICT')
                
                
    
                    ext=str(trj)[-3:] # getting the trajectory extension
                    #  print("Trajectory format: " + ext)
                    # BATUHAN: Adding a few lines to convert the trajectory into .xtc using MDTRAJ
                    # We will need users to install MDTRAJ in their system so that we can convert other trajectories into xtc
                    
                    if ext != "xtc" and ext != "trr":
         
                        print("converting the trajectory into xtc")
        
                        pdb = sim.get('PDB')
                        output_traj = str(DATAdir) + '/' + 'tmp_converted.xtc'
                        input_traj = str(DATAdir) + '/' + trj
                        input_pdb = str(DATAdir) + '/' + pdb
      
                        if os.path.isfile(output_traj): # when we're done with the converted trajectory we can simply remove it
                            os.system('rm {output_traj}')
        
                        os.system('echo System | mdconvert {input_traj} -o {output_traj} -t {input_pdb} --force # force overwrite')
        
                        # SAMULI: this xtcwhole does not necessarily have molecules as whole. Only if {input_traj} has.
                        xtcwhole = str(DATAdir) + '/' + 'tmp_converted.xtc'
                        tpr=input_pdb
        
                        print("trajectory conversion is completed")
        
                    else:
    
                        xtc = str(DATAdir) + '/' + str(trj)  
                        tpr = str(DATAdir) + '/' + str(tpr)
                        xtcwhole=str(DATAdir) + '/whole.xtc'

                    print("Make molecules whole in the trajectory")
                    os.system('echo System | gmx trjconv -f ' + xtc + ' -s ' + tpr + ' -o ' + xtcwhole + ' -pbc mol -b ' + str(EQtime))
    
                    if unitedAtom:
                        for key in sim['UNITEDATOM_DICT']:
                        #construct order parameter definition file for CH bonds from mapping file
                            def_file = open(str(DATAdir) + '/' + key + '.def', 'w')

                            mapping_file = sim['MAPPING_DICT'][key]
                            previous_line = ""
            
                            with open('./mapping_files/'+mapping_file, "r") as f:
                                for line in f.readlines():
                                    if not line.startswith("#"):
                                        regexp1_H = re.compile(r'M_[A-Z0-9]*C[0-9]*H[0-9]*_M')
                                        regexp2_H = re.compile(r'M_G[0-9]*H[0-9]*_M')
                                        regexp1_C = re.compile(r'M_[A-Z0-9]*C[0-9]*_M')
                                        regexp2_C = re.compile(r'M_G[0-9]_M')

                                        if regexp1_C.search(line) or regexp2_C.search(line):
                                            atomC = line.split()
                                            atomH = []
                                        elif regexp1_H.search(line) or regexp2_H.search(line):
                                            atomH = line.split()
                                        else:
                                            atomC = []
                                            atomH = []

                                        if atomH:
                                            items = [atomC[1], atomH[1], atomC[0], atomH[0]]
                                            def_line = items[2] + " " + items[3] + " " + key + " " + items[0] + " " + items[1] + "\n"
                                            if def_line != previous_line:
                                                def_file.write(def_line)
                                                print(def_line)
                                                previous_line = def_line
                            def_file.close()
                        #Add hydrogens to trajectory and calculate order parameters with buildH
                        ordPfile = str(DATAdir) + '/' + key + 'OrderParameters.dat' 
                        topfile = str(DATAdir) + '/frame0.gro'
                        
                        os.system('echo System | gmx trjconv -f ' + xtcwhole + ' -s ' + tpr + ' -dump 0 -o ' + topfile )
                         
                        deffile = str(DATAdir) + '/' + key + '.def' 
                        lipidname = sim['UNITEDATOM_DICT'][key]
                        #    print(lipidname)
                        buildH_calcOP_test.main(topfile,lipidname,deffile,xtcwhole,ordPfile)

                        outfile=open(ordPfile,'w')
                        line1="Atom     Average OP     OP stem"+'\n'
                        outfile.write(line1)
        
                        data = {}
                        outfile2=str(DATAdir) + '/' + key + 'OrderParameters.json'
        
                        with open(ordPfile + '.jmelcr_style.out') as OPfile:
                            lines=OPfile.readlines()
                            for line in lines:
                                if "#" in line:
                                    continue
                                line2 = line.split()[0] + " " + line.split()[1] + "  " + line.split()[5] + "  " + line.split()[6] + " " + line.split()[7] + "\n"
                                outfile.write(line2)

                                OPname = line.split()[0] + " " + line.split()[1]
                                OPvalues = [line.split()[5], line.split()[6] ,line.split()[7]]
                                data[str(OPname)]=[]
                                data[str(OPname)].append(OPvalues)
        
                            with open(outfile2, 'w') as f:
                                json.dump(data,f)

                        outfile.close()
                        outfile.close()

                        # os.system('cp ' + str(dir_tmp) + '/' + key + 'OrderParameters.dat ' + DATAdir) #Or should these be put into Data/Simulations/
                        # os.system('cp ' +str(dir_tmp) + '/' + key + 'OrderParameters.json ' + DATAdir)
                    else:
                        trj = str(DATAdir) + '/' + str(trj)
                        gro = str(DATAdir) + '/conf.gro'

                        #make gro file
                        print("\n Makin gro file")
                        os.system('echo System | gmx trjconv -f '+trj+' -s '+tpr+' -dump 0 -o ' +gro)
                    
                        for key in sim['MAPPING_DICT']:
                            if key in lipids_dict.keys(): 
                                mapping_file = sim['MAPPING_DICT'][key]
                                resname = sim[key]
                                OrdParam=find_OP('./mapping_files/'+mapping_file,gro,xtcwhole,resname)

                                outfile=open(str(DATAdir) + '/' + key + 'OrderParameters.dat','w')
                                line1="Atom     Average OP     OP stem"+'\n'
                                outfile.write(line1)
    
                                data = {}
                                outfile2=str(DATAdir) + '/' + key + 'OrderParameters.json' 

                                for i,op in enumerate(OrdParam):
                                    resops =op.get_op_res
                                    (op.avg, op.std, op.stem) =op.get_avg_std_stem_OP
                                    line2=str(op.name)+" "+str(op.avg)+" "+str(op.stem)+'\n'
                                    outfile.write(line2)
    
                                    data[str(op.name)]=[]
                                    data[str(op.name)].append(op.get_avg_std_stem_OP)
        
                                with open(outfile2, 'w') as f:
                                    json.dump(data,f)
                                outfile.close()
                                f.close()
                                # os.system('cp ' + str(dir_path) + '/' + key + 'OrderParameters.dat ' + DATAdir) #MUUTA
                                #os.system('cp ' +str(dir_path) + '/' + key + 'OrderParameters.json ' + DATAdir) #MUUTA
    
                    print("Order parameters calculated and saved to " + DATAdir)
                  
#################################
#Quality evaluation of simulated data
#assume that an order parameter calculated S from a simulation is normally distributed
# OP_sd = sqrt(N)*STEM, where N is number of lipids and STEM is standard error of mean
#def OP_sd(N, STEM):
#    op_sd = math.sqrt(N)*STEM
#    
#    return op_sd

# op_sd = STEM
    
# P: what is the probability that S_exp +/- 0.02 is in g(s) where g(s) is the probability density function of normal distribution N(s, S_sim, S_sim_sd)

def prob_S_in_g(OP_exp, exp_error, OP_sim, op_sim_sd):
    #normal distribution N(s, OP_sim, op_sim_sd)
    a = OP_exp - exp_error
    b = OP_exp + exp_error
    P_S = norm.cdf(b, loc=OP_sim, scale=op_sim_sd) - norm.cdf(a, loc=OP_sim, scale=op_sim_sd)

    if OP_exp > 0 or OP_exp < 0:
        print('experiment OP')
        print(OP_exp,exp_error)
        print('simulation OP')
        print(OP_sim,op_sim_sd)
        print('b')
        print(norm.cdf(b, loc=OP_sim, scale=op_sim_sd))
        print('a')
        print(norm.cdf(a, loc=OP_sim, scale=op_sim_sd))
        

        print('P')
        print(P_S)
    return P_S
    
# quality of simulated order parameter
#def OPquality(P_S,op_sim_STEM):
#   # print('probability')
#    #print(P_S)
#    if P_S != 0:
#        quality = 1-math.log(P_S) #/op_sim_STEM     # math.log(P_S/op_sim_STEM)      #/ math.sqrt(op_sim_STEM) #/ (op_sim_STEM*op_sim_STEM)
#    else:
#        quality = 0
   # quality_float = quality.item()
 #   print('quality')
 #   print(quality)
#    return quality
    
#
def OPquality(OP_exp, OP_sim):
    quality = np.absolute(OP_exp - OP_sim)
    return quality
    
# quality of molecule fragments

def evaluated_percentage(fragment, exp_op_data):
    count_value = 0
    fragment_size = 0
    for key, value in exp_op_data.items():
        if fragment in key:
            fragment_size += 1
            if value[0][0] != 'nan':
                count_value += 1
    if fragment_size != 0:
        return count_value / fragment_size
    else:
        return 0
    
def carbonError(OP_sim, OP_exp):
    
    E_i = 0
    quality = OPquality(OP_exp, OP_sim)

    if quality > 0.02:
        E_i = quality - 0.02
    else:
        E_i = 0
    return E_i  



def fragmentQuality(fragment, exp_op_data, sim_op_data):
    p_F = evaluated_percentage(fragment, exp_op_data)
    E_sum = 0
    if p_F != 0:
        for key_exp, value_exp in exp_op_data.items():
            #  print(key_exp)
            #  print(value_exp)
            if fragment in key_exp and value_exp[0][0] != 'nan':
                OP_exp = value_exp[0][0]
                print(OP_exp)
                OP_sim = sim_op_data[key_exp][0]
                print(OP_sim)
                E_sum += carbonError(OP_exp, OP_sim)
        E_F = E_sum / p_F
        return E_F
    else:
        return 'nan'

    
###################################################################################################
if args.q:
    simulations = []
    for subdir, dirs, files in os.walk(r'../../Data/Simulations/'): #
        for filename1 in files:
            filepath = subdir + os.sep + filename1
        
            if filepath.endswith("README.yaml"):
                READMEfilepathSimulation = subdir + '/README.yaml'
                with open(READMEfilepathSimulation) as yaml_file_sim:
                    readmeSim = yaml.load(yaml_file_sim, Loader=yaml.FullLoader)
                    indexingPath = "/".join(filepath.split("/")[4:8])
                    print(indexingPath)
                    print(filepath)
                    try:
                        if readmeSim['EXPERIMENT']:

                            simOPdata = {} #order parameter files for each type of lipid
                            for filename2 in files:
                                if filename2.endswith('OrderParameters.json'):
                                    key_data1 = filename2.replace('OrderParameters.json', '')
                                    OPfilepath = subdir + "/" + filename2
                                    with open(OPfilepath) as json_file:
                                        simOPdata[key_data1] = json.load(json_file)
                                        json_file.close()
                            simulations.append(Simulation(readmeSim, simOPdata, indexingPath))
                            yaml_file_sim.close()
                    except KeyError:
                       # print("No matching experimental data for system " + readmeSim['SYSTEM'] + " in directory " + indexingPath)
                        continue
                    

    if (not os.path.isdir('../../Data/QualityEvaluation/')): 
        os.system('mkdir ../../Data/QualityEvaluation/')

    for simulation in simulations:
        sub_dirs = simulation.indexingPath.split("/")
        os.system('mkdir ../../Data/QualityEvaluation/' + sub_dirs[0])
        os.system('mkdir ../../Data/QualityEvaluation/' + sub_dirs[0] + '/' + sub_dirs[1])
        os.system('mkdir ../../Data/QualityEvaluation/' + sub_dirs[0] + '/' + sub_dirs[1] + '/' + sub_dirs[2])    
        os.system('mkdir ../../Data/QualityEvaluation/' + sub_dirs[0] + '/' + sub_dirs[1] + '/' + sub_dirs[2] + '/' + sub_dirs[3])
        DATAdir = '../../Data/QualityEvaluation/' + str(sub_dirs[0]) + '/' + str(sub_dirs[1]) + '/' + str(sub_dirs[2]) + '/' + str(sub_dirs[3])
       # print(DATAdir)
     
    # measured values do not exist for all CH!!!!! need to take mapping name and find matching CH from simulation
    # read existing experimental values and mapping names to match with simulated CH bonds

        for lipid1 in simulation.getLipids():
            #print(lipid1)
            print(simulation.indexingPath)
            #print(simulation.data.keys())
        
           # OP_data_lipid = simulation.data[lipid1]
            OP_data_lipid = {}
            #convert elements to float because in some files the elements are strings
            for key, value in simulation.data[lipid1].items():
                OP_array = [float(x) for x in simulation.data[lipid1][key][0]]  
                OP_data_lipid[key] = OP_array
            
            OP_qual_data = {}
        # go through file paths in simulation.readme['EXPERIMENT']
            print(simulation.readme['EXPERIMENT'].values())
            for value in simulation.readme['EXPERIMENT'].values():
          # get readme file of the experiment
                experimentFilepath = "../../Data/experiments/" + value
                print(experimentFilepath)
                READMEfilepathExperiment  = experimentFilepath + '/README.yaml'
                experiment = Experiment()
                with open(READMEfilepathExperiment) as yaml_file_exp:
                    readmeExp = yaml.load(yaml_file_exp, Loader=yaml.FullLoader)
                    experiment.readme = readmeExp
                    #print(experiment.readme)
                yaml_file_exp.close()

                lipidExpOPdata = {}
                try:
                    exp_OP_filepath = experimentFilepath + '/' + lipid1 + '_Order_Parameters.json'
                #print(exp_OP_filepath)
                    with open(exp_OP_filepath) as json_file:
                        lipidExpOPdata = json.load(json_file)
                    json_file.close()
            
                    simulationREADMEsave = DATAdir + '/README.yaml'
                    with open(simulationREADMEsave, 'w') as f:
                        yaml.dump(simulation.readme,f, sort_keys=False)
                    f.close()
                except FileNotFoundError:
                    print("Experimental order parameter data do not exist for lipid " + lipid1 + ".")
                    continue

                exp_error = 0.02

                for key, value in lipidExpOPdata.items():
                    if lipidExpOPdata[key][0][0] is not 'NaN':
                        OP_array = OP_data_lipid[key] #[float(x) for x in OP_data_lipid[key][0]] #convert elements to float because in some files the elements are strings 
                        print(OP_array)
                        #print(type(OP_array))
                        OP_exp = value[0][0]
                        OP_sim = OP_array[0]
                        #op_sim_sd = OP_array[1] 
                        #op_sim_STEM = OP_array[2] 

                        #S_prob = prob_S_in_g(OP_exp, exp_error, OP_sim, op_sim_STEM) #(OP_exp, exp_error, OP_sim, op_sim_sd)
             
                        op_quality = OPquality(OP_exp, OP_sim)   #numpy float must be converted to float
                       # print(type(op_quality))
                        OP_array.append(op_quality)
                        #print(OP_array)
                
                        OP_qual_data[key] = OP_array

            print(OP_qual_data) 
        # quality data should be added into the OrderParameters.json file of the simulation                  
            outfile = DATAdir + '/' + lipid1 + '_OrderParameters.json'
        
            with open(outfile, 'w') as f:
                json.dump(OP_qual_data,f)
            f.close()
            
        # calculate quality for molecule fragments headgroup, sn-1, sn-2
            headgroup = fragmentQuality('M_G3', lipidExpOPdata, OP_data_lipid)
            sn1 = fragmentQuality('M_G1', lipidExpOPdata, OP_data_lipid)
            sn2 = fragmentQuality('M_G2', lipidExpOPdata, OP_data_lipid)
            
            fragment_quality = {}
            fragment_quality['headgroup'] = headgroup
            fragment_quality['sn-1'] = sn1
            fragment_quality['sn-2'] = sn2
           
            print('headgroup ')
            print(headgroup)
            print('sn1 ') 
            print(sn1)
            print('sn2 ') 
            print(sn2) 
            
            fragment_quality_file = DATAdir + '/' + lipid1 + '_FragmentQuality.json'
            
            with open(fragment_quality_file, 'w') as f:
                json.dump(fragment_quality,f)
            f.close()
        
        
        
     #   print(OP_qual_data)                        
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                

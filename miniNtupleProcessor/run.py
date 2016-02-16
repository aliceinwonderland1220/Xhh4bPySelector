# import miniNtupleProcessor
import ROOT
import time
from os.path import dirname, abspath
import os
import json
from optparse import OptionParser
import subprocess

ROOT.gROOT.SetBatch(True)

treename = "XhhMiniNtuple"

###################
# Nominal Samples #
###################

# data
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_data.txt"

# MC with Systematics
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_RSG_c10.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_RSG_c20.txt"
filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_2HDM.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_ttbar.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_Zjets.txt"

########################
# Inclusive ttbar only #
########################

# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_ttbar_inclusive.txt"

###################
# version control #
###################

# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_data_periodD_00-07-01.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_data_periodD_00-07-01_50Obj.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_data_periodD_00-07-00.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_data_periodD_00-06-02.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_data_periodD_00-06-02_newxAH.txt"

# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_test.txt"

########################
# btagging systematics #
########################

FT_SysNameList = [
                  '', 
                  'FT_EFF_Eigen_B_0__1down', 
                  'FT_EFF_Eigen_B_0__1up', 
                  'FT_EFF_Eigen_B_1__1down', 
                  'FT_EFF_Eigen_B_1__1up', 
                  'FT_EFF_Eigen_B_2__1down', 
                  'FT_EFF_Eigen_B_2__1up', 
                  'FT_EFF_Eigen_B_3__1down', 
                  'FT_EFF_Eigen_B_3__1up', 
                  'FT_EFF_Eigen_B_4__1down', 
                  'FT_EFF_Eigen_B_4__1up', 
                  'FT_EFF_Eigen_C_0__1down', 
                  'FT_EFF_Eigen_C_0__1up', 
                  'FT_EFF_Eigen_C_1__1down', 
                  'FT_EFF_Eigen_C_1__1up', 
                  'FT_EFF_Eigen_C_2__1down', 
                  'FT_EFF_Eigen_C_2__1up', 
                  'FT_EFF_Eigen_C_3__1down', 
                  'FT_EFF_Eigen_C_3__1up', 
                  'FT_EFF_Eigen_C_4__1down', 
                  'FT_EFF_Eigen_C_4__1up', 
                  'FT_EFF_Eigen_Light_0__1down', 
                  'FT_EFF_Eigen_Light_0__1up', 
                  'FT_EFF_Eigen_Light_1__1down', 
                  'FT_EFF_Eigen_Light_1__1up', 
                  'FT_EFF_Eigen_Light_10__1down', 
                  'FT_EFF_Eigen_Light_10__1up', 
                  'FT_EFF_Eigen_Light_11__1down', 
                  'FT_EFF_Eigen_Light_11__1up', 
                  'FT_EFF_Eigen_Light_12__1down', 
                  'FT_EFF_Eigen_Light_12__1up', 
                  'FT_EFF_Eigen_Light_13__1down', 
                  'FT_EFF_Eigen_Light_13__1up', 
                  'FT_EFF_Eigen_Light_2__1down', 
                  'FT_EFF_Eigen_Light_2__1up', 
                  'FT_EFF_Eigen_Light_3__1down', 
                  'FT_EFF_Eigen_Light_3__1up', 
                  'FT_EFF_Eigen_Light_4__1down', 
                  'FT_EFF_Eigen_Light_4__1up', 
                  'FT_EFF_Eigen_Light_5__1down', 
                  'FT_EFF_Eigen_Light_5__1up', 
                  'FT_EFF_Eigen_Light_6__1down', 
                  'FT_EFF_Eigen_Light_6__1up', 
                  'FT_EFF_Eigen_Light_7__1down', 
                  'FT_EFF_Eigen_Light_7__1up', 
                  'FT_EFF_Eigen_Light_8__1down', 
                  'FT_EFF_Eigen_Light_8__1up', 
                  'FT_EFF_Eigen_Light_9__1down', 
                  'FT_EFF_Eigen_Light_9__1up', 
                  'FT_EFF_extrapolation__1down', 
                  'FT_EFF_extrapolation__1up', 
                  'FT_EFF_extrapolation from charm__1down', 
                  'FT_EFF_extrapolation from charm__1up'
                 ]

def loadDataset(treename, filename):
	dataset = ROOT.TDSet('TTree', treename)

	suffix = filename.split('.')[-1]
	if suffix == "root":
		doFileList = False
	else:
		doFileList = True

	if not doFileList:	
		for datasetname in filename.split(','):
			dataset.Add(datasetname)
	else:
		filelist = open(filename)
		for line in filelist:
			dataset.Add(line[:-1])   # remove \n in the end

	return dataset

# Deprecated!
# def runLocal():
# 	dataset = ROOT.TChain("XhhMiniNtuple")
# 	dataset.Add(filename)
# 	dataset.Process("TPySelector", "miniNtupleProcessor")

def runProof(address, nworkers=0):
	# remove output directory
	# os.system('rm -rf output')

	dataset = loadDataset(treename, filename)

	if address != "lite://":
		ROOT.TProof.AddEnvVar("PROOF_INITCMD", "echo source %s/setup_fix.sh" % (os.environ["Xhh4bPySelector_dir"]))
	else:
		pass

	if nworkers > 0:
		proof = ROOT.TProof.Open(address, "workers=%i" % (nworkers))
	else:
		proof = ROOT.TProof.Open(address)

	proof.Exec('TPython::Exec("%s");' % ("import sys; sys.path.insert(0,'"+dirname(abspath("miniNtupleProcessor.py"))+"')"))

	time.sleep(1)

	dataset.Process("TPySelector", "miniNtupleProcessor")

	# ROOT.gSystem.Exit(-1)

	# merge output
	# For proof-lite, there is no problem in merging
	# However, for PoD, the temporary output file (for each slave) cannot be accessed by merger for some unknown reason. Therefore, we dump them to a place of control, and do the merging by hand

#######################################################################################################################

# kernel python running function
def runSys(sysName, doLite=False, nworkers=0):
	print "Running over systematic \'%s\'" % (sysName)

	if sysName == "Nominal":
		sysName = ""

	# a very stupid hard-coding ...
	if "FT_EFF_extrapolation_from_charm" in sysName:
		sysName = "FT_EFF_extrapolation from charm" + "__" + sysName.split("__")[1]

	# whether this is a b-tagging systematics
	isBtagSys = (sysName[:3] == "FT_")

	# setup treename
	global treename
	treename_base = treename

	if (sysName == "") or isBtagSys:
		treename = treename_base
	else:
		treename = treename_base + "Boosted_" + sysName

	print "Processing treename: %s" % (treename)

	#################
	# setup options #
	#################

	fOptions = open("options.json", "w")
	######################################################################
	dictOptions = {
	                "OutputDir" : os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor/outputSys/output%s" % (sysName.replace(" ", "_")),    # outputSys is hard-coded
	                # "ChannelCut": 301495.,   # m1000
	                # "ChannelCut": 301500,    # m1500
	                # "ChannelCut": 301501,    # m1600
	                # "ChannelCut": 301503.,   # m2000
	                # "ChannelCut": 301505,    # m2500
	                "BtagSys": (sysName if isBtagSys else ""),
	                "OverlapTree": True,
	                "Debug": False,
	              }
	######################################################################
	json.dump(dictOptions, fOptions)
	fOptions.close()

	# output dir protection
	if os.path.exists(dictOptions["OutputDir"]):
		print "Warning. %s already exists. It will be overwritten." % (dictOptions["OutputDir"])
		os.system("rm -rf %s" % (dictOptions["OutputDir"]))

	# run the proof
	if doLite:
		address = "lite://"
	else:
		address = "zengq@atlint04.slac.stanford.edu:21001"
		# address = "zengq@atlint03.slac.stanford.edu:21001"
	runProof(address, nworkers)

	# also remember to remove option files afterward
	os.remove("options.json")

# to be called from shell
def runShell():
	parser = OptionParser()
	parser.add_option("-a", "--allSys", action="store_true", dest="allSys", help="Whether do all systematics", default=False)
	parser.add_option("-s", "--sysName", dest="sysName", help="Systematics name to be considered", type="string", default="Nominal")
	parser.add_option("-l", "--doLite", action="store_true", dest="doLite", help="Whether use lite proof", default=False)
	parser.add_option("-n", "--nworkers", dest="nworkers", help="Number of workers to be used", type="int", default=0)
	(options, args) = parser.parse_args()

	if options.allSys:
		os.system("rm -rf outputSys")

		sysList = [
		           "Nominal", 
		           "JET_Hbb_Run1_pT__1up", 
		           "JET_Hbb_Run1_pT__1down", 
		           "JET_Hbb_Run1_mass__1up",
		           "JET_Hbb_Run1_mass__1down",
		           "JET_Hbb_CrossCalib_pT__1up", 
		           "JET_Hbb_CrossCalib_pT__1down", 
		           "JET_Hbb_CrossCalib_mass__1up",
		           "JET_Hbb_CrossCalib_mass__1down",
		           "JET_JER",
		           "JET_JMR",
		          ]

		for item in FT_SysNameList:
			if item == "":
				continue
			# item_shortcut = item.split("__")[0].replace(" ", "_")
			item_shortcut = item.replace(" ", "_")
			if item_shortcut not in sysList:
				sysList.append(item_shortcut)

		print "Batch processing systematics list:"
		print sysList

		for sysName in sysList:
			cmd = "python run.py -s %s -n %s" % (sysName, options.nworkers)
			if options.doLite:
				cmd += " -l"
			print "------> ",cmd
			os.system(cmd)
			time.sleep(5)
	else:
		runSys(options.sysName, doLite=options.doLite, nworkers=options.nworkers)

if __name__ == "__main__":
	runShell()



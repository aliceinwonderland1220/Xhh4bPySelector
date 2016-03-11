# import miniNtupleProcessor
import ROOT
import time
from os.path import dirname, abspath
import os
import json
from optparse import OptionParser
import subprocess
import sys

ROOT.gROOT.SetBatch(True)

treename = "XhhMiniNtuple"

###################
# Nominal Samples #
###################

# data
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-03/hh4b_v00-07-03_data.txt"

# MC with Systematics
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-03/hh4b_v00-07-03_RSG_c10.txt"
filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-03/hh4b_v00-07-03_RSG_c20.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-03/hh4b_v00-07-03_2HDM.txt"

# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-03/hh4b_v00-07-03_ttbar.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-03/hh4b_v00-07-03_Zjets.txt"

########################
# Inclusive ttbar only #
########################

# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-03/hh4b_v00-07-03_ttbar_inclusive.txt"

########
# test #
########

# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_btag77CDI70.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-07-00/hh4b_v00-07-00_RSG_c10.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_RSG_c10_No50MassCut.txt"

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

	# whether this is a b-tagging systematics
	isBtagSys = True
	sysNameItemList = []
	for sysNameItem in sysName.split(","):
		# a very stupid hard-coding ...
		if "FT_EFF_extrapolation_from_charm" in sysNameItem:
			sysNameItem = "FT_EFF_extrapolation from charm" + "__" + sysNameItem.split("__")[1]

		# special handle on Nominal
		if sysNameItem == "Nominal":
			sysNameItem = ""

		sysNameItemList.append(sysNameItem)

		isBtagSys = (isBtagSys and ((sysNameItem=="") or (sysNameItem[:3]=="FT_")) )

	# restore sysName
	sysName = ",".join(sysNameItemList)

	print "Restored sysName:",sysName

	if (not isBtagSys) and ("," in sysName):
		print "ERROR! Please do not run FT systematics and non-FT systematics all at once! Aborting ..."
		sys.exit(0)

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
	                # "OutputDir" : os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor/outputSys/output%s" % (sysName.replace(" ", "_")),    # outputSys is hard-coded
	                "OutputDir"   : os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor/outputSys/"+("FT/" if isBtagSys else "output"+sysName.replace(" ","_")),
	                # "ChannelCut": 301495.,   # m1000
	                # "ChannelCut": 301500,    # m1500
	                # "ChannelCut": 301501,    # m1600
	                # "ChannelCut": 301503.,   # m2000
	                # "ChannelCut": 301505,    # m2500
	                "BtagSys"     : (sysName if isBtagSys else ""),
	                "IsBtagSys"   : isBtagSys,
	                "TinyTree"    : True,
	                "OverlapTree" : True,
	                "SaveTreeAt"  : "",
	                "SaveMemory"  : True,
	                "PeekdEta"    : False,
	                "Debug"       : False,
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
	parser.add_option("-m", "--nworkers_nonbtag", dest="nworkers_nonbtag", help="Number of workers to be used, when processing non-btag systematics", type="int", default=0)
	(options, args) = parser.parse_args()

	if options.allSys:
		print "Removing outputSys ..."
		os.system("rm -rf outputSys")

		nonbtagSysList = [
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

		btagSysList = []
		for item in FT_SysNameList:
			item_shortcut = item.replace(" ", "_")
			if item_shortcut not in btagSysList:
				btagSysList.append(item_shortcut)

		# put b-tagging first
		sysList = [",".join(btagSysList)] + nonbtagSysList
		# sysList = nonbtagSysList

		print "Batch processing systematics list:"
		print sysList

		for isys, sysName in enumerate(sysList):
			if sysName in nonbtagSysList:
				nActualWorkers = options.nworkers_nonbtag
			else:
				nActualWorkers = options.nworkers

			cmd = "python run.py -s %s -n %s" % (sysName, nActualWorkers)
			if options.doLite:
				cmd += " -l"
			print "------> ",cmd
			os.system(cmd)

			if isys == 0:
				# after finishing b-tagging long-run, we wait for one minute
				time.sleep(60)
			else:
				time.sleep(5)
	else:
		runSys(options.sysName, doLite=options.doLite, nworkers=options.nworkers)

if __name__ == "__main__":
	runShell()



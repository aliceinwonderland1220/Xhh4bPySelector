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

filename = ""
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/filelist_WH.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/filelist_ZH.txt"

# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/filelist_JZXW.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/filelist_ttbar.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/filelist_Wjets.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/filelist_Zjets.txt"


########################
# btagging systematics #
########################

# CDI June27-2016 version
# Should be in total 50+1 b-tagging systematics
FT_SysNameList = [
                  '',
                  'FT_EFF_Eigen_B_0__1up',
                  'FT_EFF_Eigen_B_0__1down',
                  'FT_EFF_Eigen_B_1__1up',
                  'FT_EFF_Eigen_B_1__1down',
                  'FT_EFF_Eigen_B_2__1up',
                  'FT_EFF_Eigen_B_2__1down',
                  'FT_EFF_Eigen_B_3__1up',
                  'FT_EFF_Eigen_B_3__1down',
                  'FT_EFF_Eigen_B_4__1up',
                  'FT_EFF_Eigen_B_4__1down',
                  'FT_EFF_Eigen_C_0__1up',
                  'FT_EFF_Eigen_C_0__1down',
                  'FT_EFF_Eigen_C_1__1up',
                  'FT_EFF_Eigen_C_1__1down',
                  'FT_EFF_Eigen_C_2__1up',
                  'FT_EFF_Eigen_C_2__1down',
                  'FT_EFF_Eigen_C_3__1up',
                  'FT_EFF_Eigen_C_3__1down',
                  'FT_EFF_Eigen_Light_0__1up',
                  'FT_EFF_Eigen_Light_0__1down',
                  'FT_EFF_Eigen_Light_1__1up',
                  'FT_EFF_Eigen_Light_1__1down',
                  'FT_EFF_Eigen_Light_2__1up',
                  'FT_EFF_Eigen_Light_2__1down',
                  'FT_EFF_Eigen_Light_3__1up',
                  'FT_EFF_Eigen_Light_3__1down',
                  'FT_EFF_Eigen_Light_4__1up',
                  'FT_EFF_Eigen_Light_4__1down',
                  'FT_EFF_Eigen_Light_5__1up',
                  'FT_EFF_Eigen_Light_5__1down',
                  'FT_EFF_Eigen_Light_6__1up',
                  'FT_EFF_Eigen_Light_6__1down',
                  'FT_EFF_Eigen_Light_7__1up',
                  'FT_EFF_Eigen_Light_7__1down',
                  'FT_EFF_Eigen_Light_8__1up',
                  'FT_EFF_Eigen_Light_8__1down',
                  'FT_EFF_Eigen_Light_9__1up',
                  'FT_EFF_Eigen_Light_9__1down',
                  'FT_EFF_Eigen_Light_10__1up',
                  'FT_EFF_Eigen_Light_10__1down',
                  'FT_EFF_Eigen_Light_11__1up',
                  'FT_EFF_Eigen_Light_11__1down',
                  'FT_EFF_Eigen_Light_12__1up',
                  'FT_EFF_Eigen_Light_12__1down',
                  'FT_EFF_Eigen_Light_13__1up',
                  'FT_EFF_Eigen_Light_13__1down',
                  'FT_EFF_extrapolation__1up',
                  'FT_EFF_extrapolation__1down',
                  'FT_EFF_extrapolation from charm__1up',
                  'FT_EFF_extrapolation from charm__1down',
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
	print "Runing over sample:",filename
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
	                "OutputDir"   : os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor_VHqqbb/outputSys/"+("FT/" if isBtagSys else "output"+sysName.replace(" ","_")),
	                # "ChannelCut"  : 302321.,    # touch WH-1TeV
	                # "ChannelCut"  : 302331.,   # touch, WH-2TeV
	                # "ChannelCut"  : 302340.,     # touch, WH-5TeV
	                "BtagSys"     : (sysName if isBtagSys else ""),
	                "IsBtagSys"   : isBtagSys,
	                "TinyTree"    : True,
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
		# address = "zengq@atlint04.slac.stanford.edu:21001"
		address = "zengq@atlint03.slac.stanford.edu:21001"
	runProof(address, nworkers)

	# also remember to remove option files afterward
	os.remove("options.json")

	# check if all outputs are successful
	dirCheckList = []
	if isBtagSys:
		folderlist = subprocess.check_output("ls "+dictOptions['OutputDir'], shell=True).split("\n")[:-1]
		dirCheckList += [dictOptions['OutputDir']+"/"+folder+"/" for folder in folderlist ]
	else:
		dirCheckList += [dictOptions['OutputDir']]

	time.sleep(5)

	print "===================================================================================================="
	print "Summary of running over:",filename
	for dirToCheck in dirCheckList:
		print "==> Checking dir:",dirToCheck,"..."
		nCPUReceived = int(subprocess.check_output("ls %s | wc -l" % (dirToCheck), shell=True).split("\n")[0])
		if nCPUReceived != nworkers:
			print "*** ERROR ***! Number of workers expected is %s but only find %s. Please rerun this job!" % (nworkers, nCPUReceived)
		else:
			print "Looks OK!"
	print "===================================================================================================="

# to be called from shell
def runShell():
	parser = OptionParser()
	parser.add_option("-f", "--sampleName", dest="sampleName", help="sample name to be processed", default="")
	parser.add_option("-a", "--allSys", action="store_true", dest="allSys", help="Whether do all systematics", default=False)
	parser.add_option("-s", "--sysName", dest="sysName", help="Systematics name to be considered", type="string", default="Nominal")
	parser.add_option("-l", "--doLite", action="store_true", dest="doLite", help="Whether use lite proof", default=False)
	parser.add_option("-n", "--nworkers", dest="nworkers", help="Number of workers to be used", type="int", default=0)
	parser.add_option("-m", "--nworkers_nonbtag", dest="nworkers_nonbtag", help="Number of workers to be used, when processing non-btag systematics", type="int", default=0)
	(options, args) = parser.parse_args()

	global filename
	filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/v01-02-04_DS2/filelist_%s.txt" % (options.sampleName)

	if options.allSys:
		print "Removing outputSys ..."
		os.system("rm -rf outputSys")

		nonbtagSysList = [
		                   "JET_Rtrk_Baseline_Kin__1up",
		                   "JET_Rtrk_Baseline_Kin__1down",
		                   "JET_Rtrk_Tracking_Kin__1up",
		                   "JET_Rtrk_Tracking_Kin__1down",
		                   "JET_Rtrk_Modelling_Kin__1up",
		                   "JET_Rtrk_Modelling_Kin__1down",
		                   "JET_Rtrk_TotalStat_Kin__1up",
		                   "JET_Rtrk_TotalStat_Kin__1down",

		                   "JET_Rtrk_Baseline_Sub__1up",
		                   "JET_Rtrk_Baseline_Sub__1down",
		                   "JET_Rtrk_Tracking_Sub__1up",
		                   "JET_Rtrk_Tracking_Sub__1down",
		                   "JET_Rtrk_Modelling_Sub__1up",
		                   "JET_Rtrk_Modelling_Sub__1down",
		                   "JET_Rtrk_TotalStat_Sub__1up",
		                   "JET_Rtrk_TotalStat_Sub__1down",

		                   "JET_JER",
		                   "JET_JMR",
		                   "JET_JD2R",
		                 ]

		btagSysList = []
		for item in FT_SysNameList:
			item_shortcut = item.replace(" ", "_")
			if item_shortcut not in btagSysList:
				btagSysList.append(item_shortcut)

		# put b-tagging first
		sysList = [",".join(btagSysList)] + nonbtagSysList
		# sysList = [",".join(btagSysList)]                 # b-tagging only
		# sysList = nonbtagSysList                        # non b-tagging only

		print "Batch processing systematics list:"
		print sysList

		for isys, sysName in enumerate(sysList):
			if sysName in nonbtagSysList:
				nActualWorkers = options.nworkers_nonbtag
			else:
				nActualWorkers = options.nworkers

			cmd = "python run.py -f %s -s %s -n %s" % (options.sampleName, sysName, nActualWorkers)
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



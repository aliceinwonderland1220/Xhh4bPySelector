import miniNtupleProcessor
import ROOT
import time
from os.path import dirname, abspath
import os

treename = "XhhMiniNtuple"

filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-04-01/hh4b_v00-04-01_data.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-04-01/hh4b_v00-04-01_ttbar.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-04-01/hh4b_v00-04-01_RSG_c10.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_RSG_c10_m1000.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_RSG_c10_m1500.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_RSG_c10_m2000.txt"
# filename = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/filelist_RSG_c10_m2500.txt"

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

def runLocal():
	dataset = ROOT.TChain("XhhMiniNtuple")
	dataset.Add(filename)

	dataset.Process("TPySelector", "miniNtupleProcessor")

def runProof(address, nworkers=0):
	# remove output directory
	os.system('rm -rf output')

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

	# merge output
	# For proof-lite, there is no problem in merging
	# However, for PoD, the temporary output file (for each slave) cannot be accessed by merger for some unknown reason. Therefore, we dump them to a place of control, and do the merging by hand

if __name__ == "__main__":
	# runProof("lite://", 1)
	runProof("zengq@atlint04.slac.stanford.edu:21001")

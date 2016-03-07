import ROOT
import numpy as np
import subprocess
import os

# all reduced file should be put under inputDir
# aux file will be created and stored temporarily in "tmp/" directory
# The merged file would be put under outputDir
# outputDir should exists before using this function. No attempt to clear outputDir
# temporarily directory would be erased after merging
def ExpandReducedToAux(inputDir, baseName, outputDir):
	# create tempoary dir to store aux files
	tmpDir = "tmp"
	os.system("mkdir "+tmpDir)

	# read input reduced files
	f_base = ROOT.TFile(inputDir+"/"+baseName+".root")
	t_base = f_base.Get("EventsReduced")

	# cache the branch
	b_SFList = ROOT.vector(ROOT.Double)()
	b_SFNameList = ROOT.vector(ROOT.string)()
	t_base.SetBranchAddress("SFNameList", b_SFNameList)

	t_base.SetBranchAddress("SFList", b_SFList)

	# get SFNameList by sampling the first item
	# It is assumed that all events have the same list of b-tagging systematics
	t_base.GetEntry(0)
	SFNameList = [ t_base.SFNameList[i] for i in range(t_base.SFNameList.size()) ]

	f_outputList = []
	t_outputList = []
	SF_outputList = []
	for SFName in SFNameList:
		# It has been validated the TTree will be correctedly filled and assigned to correct TFile
		SFNameAppendix = ("" if SFName=="" else "_"+SFName)
		SFNameAppendix = SFNameAppendix.replace(" ", "_")

		f_output = ROOT.TFile(tmpDir+"/"+baseName+SFNameAppendix+".root", "RECREATE")
		t_output = ROOT.TTree("Events", "Events")

		SF_array = np.zeros(1, dtype=float)
		t_output.Branch("SF", SF_array, "SF/D")

		f_outputList.append(f_output)
		t_outputList.append(t_output)
		SF_outputList.append(SF_array)

	print "Begin Loop"

	for iEntry in range(t_base.GetEntries()):
		t_base.GetEntry(iEntry)

		if iEntry % 10000. == 0:
			print "==> Processed:",iEntry,"%.2f%%" % (100.*iEntry/t_base.GetEntries())

		for i, SFName in enumerate(SFNameList):
			SF_outputList[i][0] = b_SFList[i]
			t_outputList[i].Fill()

	print "End Loop"

	for i, f_output in enumerate(f_outputList):
		f_output.Write()
		f_output.Close()

	# merge the reduced + aux
	for SFName in SFNameList:
		SFNameAppendix = ("" if SFName=="" else "_"+SFName)
		SFNameAppendix = SFNameAppendix.replace(" ", "_")

		reducedFileName = inputDir+"/"+baseName+SFNameAppendix+".root"
		auxFileName = tmpDir+"/"+baseName+SFNameAppendix+".root"

		targetFileName = outputDir+"/"+baseName+SFNameAppendix+".root"

		cmd = "hadd -f %s %s %s" % (targetFileName, reducedFileName, auxFileName)
		os.system(cmd)

	# remove tmp dir storing aux files
	os.system("rm -rf "+tmpDir)

def batch(sampleName):
	baseList = [
	           # "JET_Hbb_Run1_pT__1up", 
	           # "JET_Hbb_Run1_pT__1down", 
	           # "JET_Hbb_Run1_mass__1up",
	           # "JET_Hbb_Run1_mass__1down",
	           # "JET_Hbb_CrossCalib_pT__1up", 
	           # "JET_Hbb_CrossCalib_pT__1down", 
	           # "JET_Hbb_CrossCalib_mass__1up",
	           # "JET_Hbb_CrossCalib_mass__1down",
	           # "JET_JER",
	           # "JET_JMR",
	           "",         # this would cover nominal and all b-tagging systematics
	          ]

	inputDir = "hist_%s_reduced" % (sampleName)
	baseName = "hist_%s" % (sampleName)
	outputDir = "hist_%s" % (sampleName)

	# remove outputDir if exists
	os.system("rm -rf "+outputDir)

	# then create a clean one
	os.system("mkdir "+outputDir)

	# then run!
	for baseName in baseList:
		baseName = "hist_%s%s" % (sampleName, ""if baseName=="" else "_"+baseName)
		ExpandReducedToAux(inputDir, baseName, outputDir)

if __name__ == "__main__":
	batch("RSG_c10_No50MassCut")


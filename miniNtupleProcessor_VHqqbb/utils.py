import ROOT
import re
import os

# run number range is all INCLUSIVE
dict_Period_RunNumberList = {
	"periodA": [266904, 267639],
	"periodB": [267358, 267599],
	"periodC": [270441, 272531],
	"periodD": [276073, 276954],
	"periodE": [278727, 279928],
	"periodF": [279932, 280422],
	"periodG": [280423, 281075],
	"periodH": [281130, 281411],
	"periodI": [281662, 282482],
	"periodJ": [282625, 284484],
}

def SortVecIndex(inputlist, FromSmallToBig=False):
	list_index = [(inputlist[index], index) for index in range(len(inputlist))]
	list_index_sorted = sorted(list_index, key=lambda item: item[0], reverse=(not FromSmallToBig))

	output = {
	  "SortedVec": [item[0] for item in list_index_sorted],
	  "SortedIndex": [item[1] for item in list_index_sorted]
	}

	return output

# parsing the PySelector and figure out all branches that will actually be used
def GenerateVariableList(filename):
	f = open(filename, 'r')
	wholetxt = f.read()

	p = re.compile("tree\.[0-9a-zA-Z_]*")
	matchlist = p.findall(wholetxt)

	# remove those redundant
	matchlist_simp = list(set(matchlist))

	# remove "tree."
	return [item[5:] for item in matchlist_simp]

# get list of run number for each version of miniNtuple
# make sure you setup rucio before using this function
def GetRunNumberList(queryString):
	import subprocess

	queryCmd = "rucio list-dids " + queryString
	output = subprocess.check_output(queryCmd.split(' '))

	lines = output.split('\n')

	RunNumberList = ""
	for line in lines:
		#if 'CONTAINER' not in line:
		if 'COLLECTION' not in line:
			continue

		start_index = line.find('data15_13TeV') + len('data15_13TeV') + 1
		end_index = line.rfind('physics_Main')-1

		segment = line[start_index:end_index]

		if "period" in segment:
			[runStart, runEnd] = dict_Period_RunNumberList[segment]
			RunNumberList += ("%s-%s" % (runStart, runEnd))
		else:
			RunNumberList += segment

		RunNumberList += ","

	RunNumberList = RunNumberList[:-1]  # eat the last ","

	RunNumberList_obj = RunNumberList.split(',')

	if len(set(RunNumberList_obj)) != len(RunNumberList_obj):
		print "WARNING: Some RunNumber appear more than once!"

	RunNumberList_mergeobj = list(set(RunNumberList_obj))

	return ','.join(RunNumberList_mergeobj)


###################################################################################################################################################
# check if all systematics variation files are complete. Help to diagonize whether there is any unnoticed error during batch production 
###################################################################################################################################################

def CheckSysNumber(dirName):
	import subprocess
	fileList = subprocess.check_output(['ls', dirName])
	fileList = fileList.split('\n')

	for fileName in fileList:
		if ".root" not in fileName: continue

		f = ROOT.TFile(dirName+"/"+fileName)
		h = f.Get("GoodEvent_Cutflow/CountEntry_Initial")
		
		print fileName,h.GetBinContent(1)

		f.Close()

###################################################################################################################################################
# Generate a file-list for a data-set that is transferred to SLAC-ATLAS-T3_GRIDFTP
###################################################################################################################################################

def GetGridFileList(datasetname):
	import subprocess

	outputList = []
	rawRucioOutput = subprocess.check_output(["rucio", "list-files", datasetname]).split("\n")
	for line in rawRucioOutput:
		if "pool.root" not in line: continue
		GridFileName = line.split("|")[1].replace(" ","")
		outputList.append(GridFileName)

	return outputList

def GenerateFileListR2D2(datasetname, RSE, outputFileName):
	import subprocess

	GridFileList = GetGridFileList(datasetname)
	LocalFileList = []
	for GridFileName in GridFileList:
		rawRucio = subprocess.check_output(["rucio", "list-file-replicas", GridFileName]).split("\n")
		for line in rawRucio:
			if "pool.root" not in line: continue
			if RSE not in line: continue

			FilePathAndName = line.split("|")[5].split(":")[-1]
			FilePathAndName = FilePathAndName[FilePathAndName.find("/"):]
			FilePathAndName = FilePathAndName.replace(" ", "")

			LocalFileList.append(FilePathAndName)
			break

	f = open(outputFileName, "w")
	for LocalFileName in LocalFileList:
		f.write("root://atlprf01.slac.stanford.edu:1094/"+LocalFileName+"\n")
	f.close()

def runGenerateFileListR2D2():
	R2D2_FileList = open("data/EXOT8/mc_r2d2.txt")
	for line in R2D2_FileList:
		if "EXOT8" not in line: continue

		line = line.split("\n")[0]
		line = line.split("/")[0]

		print "Processing",line,"..."
		GenerateFileListR2D2(line, "SLAC-ATLAS-T3_GRIDFTP", "data/EXOT8/filelist_"+line+".txt")		

###################################################################################################################################################
# Generate Xsection File
###################################################################################################################################################

class PMGXsectionReader:
	def __init__(self):
		self._db = dict()

	def ReadData(self, datalist):
		for datafile in datalist:
			f = open(datafile)
			content = f.readlines()
			head = content[0][1:-1].replace(" ", "").split("\t")

			for line in content[1:]:
				line_split = line[:-1].replace(" ", "").split("\t")

				DSID = line_split[0]

				if self._db.has_key(DSID):
					print "WARNING! DSID %s has already been registered before! It would be overwritten" % (DSID)

				self._db[DSID] = {}

				for index in range(1, len(line_split)):
					key = head[index]
					value = line_split[index]
					self._db[DSID][key] = value

	def GetInfo(self, DSID, key="ALL"):
		result = self._db.get(DSID, {})

		if key == "ALL":
			return result
		else:
			return result.get(key, None)

# we will scan all "submitDir_" under scanDir and obtain the counting information from each of them
# The X-section table would correspond to these samples
# please use absolute path for scanDir
def GenerateXsectionTable(scanDir, outputName):
	import subprocess
	import sys

	f_output = open(outputName, "w")

	# Initialize PMGTool
	PMGTool = PMGXsectionReader()
	PMGFileList = [
	                os.environ['Xhh4bPySelector_dir'] + '/External/PMGCrossSectionTool/data/' + "list_Xsec_Exotics_Other_Download.txt",
	                os.environ['Xhh4bPySelector_dir'] + '/External/PMGCrossSectionTool/data/' + "list_Xsec_Multijet_Download.txt",
	                os.environ['Xhh4bPySelector_dir'] + '/External/PMGCrossSectionTool/data/' + "list_Xsec_Wjets_Other_Download.txt",
	                os.environ['Xhh4bPySelector_dir'] + '/External/PMGCrossSectionTool/data/' + "list_Xsec_Zjets_Other_Download.txt",
	              ]
	PMGTool.ReadData(PMGFileList)

	# scan directory #
	folderlist = subprocess.check_output("ls "+scanDir, shell=True).split("\n")[:-1]
	for folder in folderlist:
		if folder.find("submitDir_") != 0: continue

		targetDir = scanDir+"/"+folder+"/data-metadata/"
		filelist = subprocess.check_output("ls "+targetDir, shell=True).split("\n")[:-1]
		if len(filelist) != 1:
			print "Error! More than one files encountered in %s! Only one is expected." % (targetDir)
			continue

		filename = targetDir+"/"+filelist[0]
		if not os.path.exists(filename):
			print "Error! %s does not exist!" % (filename)
			continue

		# now extract necessary information
		f = ROOT.TFile(filename)
		h = f.Get("MetaData_EventCount")

		# extract channel number
		DSID = filename.split("/")[-1].split(".")[1]
		xsec = float(PMGTool.GetInfo(DSID, "AMIXsec")) * 1000.  # pb -> fb
		eff  = float(PMGTool.GetInfo(DSID, "BRorFiltEff"))
		k    = float(PMGTool.GetInfo(DSID, "K-factor"))
		if "JZXW" in scanDir:
			print "WARNING! You are using number of entries instead of sum of weights. This should only happen for JZXW sample!"
			n = h.GetBinContent(1)    # number of entries before derivation
			# n = h.GetBinContent(3)
		else:
			n = h.GetBinContent(3)    # sum of weights before derivation

		# write it down
		f_output.write("xsec_%s  %s\n" % (DSID, xsec))
		f_output.write("eff_%s   %s\n" % (DSID, eff))
		f_output.write("k_%s     %s\n" % (DSID, k))
		f_output.write("n_%s     %s\n" % (DSID, n))
		f_output.write("\n")

	f_output.write("# last line\n")











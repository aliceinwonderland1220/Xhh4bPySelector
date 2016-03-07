import ROOT
import re
import os

dict_RSG_channelNumber_Mass = {

	301488: ('c10', 300),
	301489: ('c10', 400),
	301490: ('c10', 500),
	301491: ('c10', 600),
	301492: ('c10', 700),
	301493: ('c10', 800),
	301494: ('c10', 900),
	301495: ('c10', 1000),
	301496: ('c10', 1100),
	301497: ('c10', 1200),
	301498: ('c10', 1300),
	301499: ('c10', 1400),
	301500: ('c10', 1500),
	301501: ('c10', 1600),
	301502: ('c10', 1800),
	301503: ('c10', 2000),
	301504: ('c10', 2250),
	301505: ('c10', 2500),
	301506: ('c10', 2750),
	301507: ('c10', 3000),

	301508: ('c20', 300),
	301509: ('c20', 400),
	301510: ('c20', 500),
	301511: ('c20', 600),
	301512: ('c20', 700),
	301513: ('c20', 800),
	301514: ('c20', 900),
	301515: ('c20', 1000),
	301516: ('c20', 1100),
	301517: ('c20', 1200),
	301518: ('c20', 1300),
	301519: ('c20', 1400),
	301520: ('c20', 1500),
	301521: ('c20', 1600),
	301522: ('c20', 1800),
	301523: ('c20', 2000),
	301524: ('c20', 2250),
	301525: ('c20', 2500),
	301526: ('c20', 2750),
	301527: ('c20', 3000),
}

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
# merge metadata histogram 
# Works on SLAC machine
# format of hh4b_version should be something like hh4b-00-04-01
###################################################################################################################################################

def GetRSGMetaData(hh4b_version):
	def ConvertVersionToNumber(v):
		vSplit = v.split('-')[1:]
		vSplit = [int(item) for item in vSplit]
		return vSplit

	# 1 means v1 > v2; -1 means v1 < v2; 0 means v1 == v2
	# None means error
	def CompareVersion(v1, v2):
		v1Split = ConvertVersionToNumber(v1)
		v2Split = ConvertVersionToNumber(v2)

		if len(v1Split) != len(v2Split):
			print "length incompatible between %s and %s!" % (v1, v2)
			return None
		else:
			for index in range(len(v1)):
				v1Item = v1[index]
				v2Item = v2[index]

				if v1Item == v2Item:
					continue
				else:
					if v1Item > v2Item:
						return 1
					else:
						return -1

			return 0

	hh4b_version_output = hh4b_version[:4]+"_v"+hh4b_version[5:]
	hh4b_version_path = hh4b_version[:5]+'v'+hh4b_version[5:]

	if CompareVersion(hh4b_version, 'hh4b-00-04-01') == 1:
		path = "/atlas/local/zengq/XHHbbbb/miniNtuple/%s/mc15_13TeV_metadata/" % (hh4b_version_path)
	else: 
		path = "/atlas/local/zengq/XHHbbbb/miniNtuple/%s/mc15_13TeV/" % (hh4b_version_path)

	channelNumberList = dict_RSG_channelNumber_Mass.keys()

	for channelNumber in channelNumberList:

		# a special fix on hh4b-00-05-00
		if channelNumber == 301526:
			continue

		outputFileName = "%s_RSG_%s_M%s_metadata.root" % (hh4b_version_output, dict_RSG_channelNumber_Mass[channelNumber][0], dict_RSG_channelNumber_Mass[channelNumber][1])
		cmd = 'hadd -f %s %s' % ( outputFileName , path+"group.phys-exotics.mc15_13TeV."+str(channelNumber)+".*"+hh4b_version+"*metadata.root/*.root*" )
		print cmd
		os.system(cmd)

# hadd all samples in all dataset in specified directory
def DirtyHadd(baseDir):
	tmpDir = "Metadata_tmp"
	os.system("rm -rf "+tmpDir)
	os.system("mkdir -p "+tmpDir)

	import subprocess
	datasetList = subprocess.check_output(["ls", baseDir]).split("\n")[:-1]   # remove the last empty string
	for datasetName in datasetList:
		channelNumber = int(datasetName.split(".")[3])   # this is very specific to MiniNtuple format
		outputFileName = "%s/Metadata_RSG_%s_M%s.root" % (tmpDir, dict_RSG_channelNumber_Mass[channelNumber][0], dict_RSG_channelNumber_Mass[channelNumber][1])
		cmd = "hadd -f %s %s" % (outputFileName, baseDir+"/"+datasetName+"/"+"*.root*")
		
		print cmd
		os.system(cmd)


###################################################################################################################################################
# print out metadata of RSG
# hh4b_version should be something like 'hh4b_v00-04-01'
# if you specify ibin, it is the bin number in metadata histogram
###################################################################################################################################################

def ReadMetaData(hh4b_version, ibin=None):
	import subprocess
	fileList = subprocess.check_output(['ls', 'data/'+hh4b_version])
	fileList = fileList.split('\n')

	for fileName in fileList:
		if hh4b_version not in fileName: continue
		if 'metadata.root' not in fileName: continue

		f = ROOT.TFile('data/'+hh4b_version+'/'+fileName)
		h = f.Get("MetaData_EventCount")

		output = "%s : " % (fileName)
		for i in range(1, h.GetNbinsX()+1):
			if ibin is not None:
				if i != ibin: continue

			output += "%f (%s) " % (h.GetBinContent(i), h.GetXaxis().GetBinLabel(i))

		print output

# simply read all metadata files in a specified directories
def ReadMetaData2(baseDir, ibin=None):
	if ibin == None:
		ibin = 1

	import subprocess
	fileList = subprocess.check_output(["ls", baseDir]).split("\n")[:-1]   # remove the last empty string

	for iFile, fileName in enumerate(fileList):
		f = ROOT.TFile(baseDir+"/"+fileName)
		h = f.Get("MetaData_EventCount")

		if iFile == 0:
			binlabel = h.GetXaxis().GetBinLabel(ibin)
			print "=====> You are checking:",binlabel

		print fileName,":",h.GetBinContent(ibin)


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







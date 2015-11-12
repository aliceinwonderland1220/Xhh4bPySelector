import ROOT
import re
import os

dict_RSG_channelNumber_Mass = {
	301488: ('c10', 300),
	301490: ('c10', 500),
	301491: ('c10', 600),
	301492: ('c10', 700),
	301493: ('c10', 800),
	301494: ('c10', 900),
	301495: ('c10', 1000),
	301496: ('c10', 1100),
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
		if 'CONTAINER' not in line:
			continue

		start_index = line.find('data15_13TeV') + len('data15_13TeV') + 1
		end_index = line.rfind('physics_Main')-1

		RunNumberList += line[start_index:end_index]
		RunNumberList += ","

	RunNumberList = RunNumberList[:-1]  # eat the last ","

	return RunNumberList

# merge metadata histogram 
# Works on SLAC machine
def GetRSGMetaData(hh4b_version):
	# path = "/atlas/local/zengq/XHHbbbb/miniNtuple/%s/mc15_13TeV/" % (hh4b_version)
	path = "/atlas/local/zengq/XHHbbbb/miniNtuple/hh4b-v00-01-03/mc15_13TeV/"
	channelNumberList = dict_RSG_channelNumber_Mass.keys()

	for channelNumber in channelNumberList:
		outputFileName = "%s_RSG_%s_M%s_metadata.root" % (hh4b_version, dict_RSG_channelNumber_Mass[channelNumber][0], dict_RSG_channelNumber_Mass[channelNumber][1])
		cmd = 'hadd -f %s %s' % ( outputFileName , path+"group.phys-exotics.mc15_13TeV."+str(channelNumber)+".*"+hh4b_version+"*metadata.root/*.root" )
		print cmd
		os.system(cmd)

def ReadMetaData(hh4b_version):
	import subprocess
	fileList = subprocess.check_output(['ls', 'data'])
	fileList = fileList.split('\n')

	for fileName in fileList:
		if hh4b_version not in fileName: continue
		if 'metadata.root' not in fileName: continue

		f = ROOT.TFile('data/'+fileName)
		h = f.Get("MetaData_EventCount")

		output = "%s : " % (fileName)
		for i in range(1, h.GetNbinsX()+1):
			output += "%f (%s) " % (h.GetBinContent(i), h.GetXaxis().GetBinLabel(i))

		print output





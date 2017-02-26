import os
import ROOT
import utils
import PySelectorBase
import array
import sys
from collections import defaultdict

import time
import json

##################
## load library ##
##################

from ROOT import gSystem
print "Loading libraries ..."

# histogram maker service #
if(gSystem.Load(os.environ['Xhh4bPySelector_dir']+"/External/lib/AutoHists/libAutoHists.so") != 0):
	print "ERROR! Unable to load AutoHists!"
	sys.exit(0)

# ProofAnaCore #
if(gSystem.Load(os.environ['Xhh4bPySelector_dir']+"/External/lib/ProofAnaCore/libProofAnaCore.so") != 0):
	print "ERROR! Unable to load ProofAnaCore!"
	sys.exit(0)

# PileupReweighting #
if(gSystem.Load(os.environ['Xhh4bPySelector_dir']+"/External/lib/PileupReweighting/libPileupReweighting.so") != 0):
	print "ERROR! Unable to load PileupReweighting!"
	sys.exit(0)

# GRL #
if(gSystem.Load(os.environ['Xhh4bPySelector_dir']+"/External/lib/GoodRunsLists/libGoodRunsLists.so") != 0):
	print "ERROR! Unable to load GoodRunsLists!"
	sys.exit(0)
ROOT.gROOT.ProcessLine('.include %s' % (os.environ['Xhh4bPySelector_dir']+"/External/GoodRunsLists"))

# PMGCrossSectionTool #
if(gSystem.Load(os.environ['Xhh4bPySelector_dir']+"/External/lib/PMGCrossSectionTool/libPMGCrossSectionTool.so") != 0):
	print "ERROR! Unable to load PMGCrossSectionTool!"
	sys.exit(0)

print "Finish loading libraries!"

class miniNtupleProcessor(PySelectorBase.PySelectorBase):
	def Setup(self):
		####################
		# selector options #
		####################

		# self.histfile = os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor/output/test.root"       # use absolute path, and all output will be put under output folder
		self.printInterval = 1000
		# generate list of variables that will actuall be used by parsing current file
		print ": URL of file to be parsed for varable activation"
		parseFileName = __file__
		if parseFileName[-3:] == 'pyc':
			parseFileName = parseFileName[:-1]
		print parseFileName
		self.variables = utils.GenerateVariableList(parseFileName)
		print ': List of variables to be activated'
		print self.variables

		# if set None or [], then no optimization will be applied. The code will run for sure, but will be relatively slow
		# self.variables = None

		self.treeAccessor = 2
		self.useSetBranchStatus = 1

		################
		# options file #
		################

		print "Loading option file ..."

		self._dictOptions = {}
		optionFilePath = os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor_VHqqbb/options.json"
		if os.path.isfile(optionFilePath):
			_fOptions = open(optionFilePath)
			self._dictOptions = json.load(_fOptions)
			_fOptions.close()
		else:
			print "WARNING: Unable to find file %s. Empty option will be used." % (optionFilePath)

		print "========================"
		print "==      Options       =="
		print "========================"
		for key,value in self._dictOptions.items():
			print " %s : %s " % (key, value)
		print "========================"

		print "Finish loading option file!"

		# self._optXXXX is reserved for option taken from options.json
		self._optOutputDir   = self._dictOptions.get("OutputDir",   os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor_VHqqbb/output/")
		self._optChannelCut  = self._dictOptions.get("ChannelCut",  None)
		self._optBtagSys     = self._dictOptions.get("BtagSys",     "")
		self._optIsBtagSys   = self._dictOptions.get("IsBtagSys",   "FT_" in self._optBtagSys)
		self._optTinyTree    = self._dictOptions.get("TinyTree",    True)
		self._optSaveTreeAt  = self._dictOptions.get("SaveTreeAt",  "ALL")
		self._optSaveMemory  = self._dictOptions.get("SaveMemory",  False)
		self._optPeekdEta    = self._dictOptions.get("PeekdEta",    False)
		self._optDebug       = self._dictOptions.get("Debug",       False)

		# convert unicode (probably from the json file) to str
		self._btagSysList = []
		for _ in self._optBtagSys.split(","):
			self._btagSysList.append( str(_) )

		# setup output files for different b-tag variation
		for btagSysName in self._btagSysList:
			btagSysAppendix = btagSysName.replace(" ","_")

			if not self._optIsBtagSys:
				self.histfileList.append(self._optOutputDir+"/test.root")
			else:
				self.histfileList.append(self._optOutputDir+"/output"+btagSysAppendix+"/test.root")

		# check if optSaveTreeAt is among optBtagSys
		# If not, it will be reset to "ALL", meaning the tree will be filled for each output
		if self._optSaveTreeAt != "ALL":
			if self._optSaveTreeAt not in self._btagSysList:
				print "Warning: %s not found among %s. It is reset to \"ALL\"" % (self._optSaveTreeAt, self._btagSysList)
				self._optSaveTreeAt = "ALL"

		###################
		# physics options #
		###################

		# generic global options

		# make sure this is consistent with the CDI file you are using, so that b-tag systematics are correct
		self._BtagCutDict = {
		  'MV2c10_70': 0.6455,
		  'MV2c10_77': 0.3706,
		  'MV2c10_85': -0.1416,
		  '2D_70': (0.913, -0.561),
		  '2D_77': (0.671, -0.737),
		  '2D_85': (0.077, -0.759),
		}

		self._ForceDataMC = None                       # Force to run in either "Data" or "MC". This should be set as None most of the time.
		self._doBlindData = False    # touch            # whether we blind the data
		self._doJERStudy  = False   # touch            # turn on JERStudy --- basically the truth response stuffs
		self._VHAmbiguityScheme = 7 # touch            # How to solve V/H ambiguity:
		                                               # 1: based on V-tagging / anti-V-tagging
		                                               # 2: based on VH / HV combination and distance, using both V-tagging and H-tagging
		                                               # 3: same as 2, but requires at least 1 b-tag in Higgs-tagging definition

		self._ChannelNumberList = sorted(range(302316, 302340+1) + range(302366, 302390+1) + range(306776, 306783+1))      # from small to large
		self._ChannelNumberDict = defaultdict(lambda: -1)
		for index in range(len(self._ChannelNumberList)):
			self._ChannelNumberDict[self._ChannelNumberList[index]] = index                      # build map of channelnumber -> index

		# Luminosity
		# touch

		# 2015 reprocessed
		# self._GRLXml = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/data15_13TeV.periodAllYear_DetStatus-v79-repro20-02_DQDefects-00-02-02_PHYS_StandardGRL_All_Good_25ns.xml"        # 2015 GRL
		# self._Lumi = 3.21296          # Number for 2015 reprocessed data (20.7), using recommended GRL (above)
		                                # https://atlas-lumicalc.cern.ch/results/2781f5/result.html
		                                # same as number reported here: https://twiki.cern.ch/twiki/bin/view/AtlasProtected/GoodRunListsForAnalysisRun2#2015_13_TeV_pp_data_taking_summa

		# 2016
		self._GRLXml = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/data16_13TeV.periodAllYear_DetStatus-v83-pro20-15_DQDefects-00-02-04_PHYS_StandardGRL_All_Good_25ns.xml"          # 2016 GRL
		self._Lumi = 32.8616            # https://atlas-lumicalc.cern.ch/results/da969b/result.html (A~K) --> 27.0313
		                                # https://atlas-lumicalc.cern.ch/results/d8c076/result.html --> 6.22581
		                                # same as number reported here: https://twiki.cern.ch/twiki/bin/view/AtlasProtected/GoodRunListsForAnalysisRun2#2016_13_TeV_pp_data_taking_summa
		                                # After luminosity central value updates announced in Feb 15, 2017 --> 32.8616 (calculated with lumi tag OfLumi-13TeV-008, but content of GRL remains same)

		# 2015 + 2016 -- for MC
		# self._Lumi = 3.21296 + 32.8616

		# X-section

		self._ApplyXsecWeight = True
		self._XsectionConfig = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor_VHqqbb/data/v02-02-02_update2/filelist_Xsection.config"   # touch

		# Mtt stitching
		# touch

		self._doMttStitch = True  #touch                  # whether we do the mtt stitch
		self._MttStitchCut = 1100.                 # the cut on inclusive ttbar sample of mtt value
		self._MttScale_allhad = 1.27084395007                # the scale factor applied on allhad mtt slices when doing stitching
		self._MttScale_nonallhad = 1.02192743215             # the scale factor applied on nonallhad mtt slices when doing stitching

		# trigger
		# touch

		self._TriggerList = ["HLT_j420_a10_lcw_L1J100"]         # 2016 trigger
		# self._TriggerList = ["HLT_j360_a10_lcw_sub_L1J100"]     # 2015 trigger
		# self._TriggerList = ["HLT_j360_a10r_L1J100"]            # 2015 Moriond trigger. Since we need to compare b-tagging results with 20.1, this trigger is reserved
		self._doTriggerCut = True                               # When one wants to do the trigger study, make sure this option is turned OFF !

		# lepton/MET veto

		self._doLeptonVeto = True      # touch                  # no "loose" lepton in the event
		self._doMETVeto = True         # touch                 

		# calo-jet

		self._JetMassCut   = 50.                     # mass cut on calo-jet, BEFORE muon correction (because jet with mass < 50 GeV is not calibrated at all)
		self._JetPtUpBound = 1e9 #1500.              # upper bound of large-R jet, due to calibration issue. Jet with pT larger than that do not have proper JMS uncertainties, unless one uses TA-mass
		self._HiggsMassCut = (75, 145) #touch        # Standard Loose: 75~145, ~90%
		                                             # Standard Tight: 90~135, ~68%
		self._WZWP = "50"      # touch               # working point for W/Z tagging

		# track-jet

		self._TrackJetPtCut = 10.
		self._TrackJetEtaCut = 2.5
		self._TrackJetWP = "MV2c10_77" # touch                # Only one WP now. Make sure this is consistent with the calibration used during mini-ntuple production. Otherwise, please reset SF to be 1.
		self._ResetSF = False  # touch                         # if True, then SF all reset to 1.

		# muon correction

		self._doMuonCorrection = True
		self._MuonPtCut = 4.
		self._MuonEtaCut = 2.5
		self._MuonQualityCut = "Medium"      

		#######################
		# External Tool Setup #
		#######################

		#
		# PRW

		self._doPRW = False
		self._PRWConfigFile = ""
		self._PRWLumiCalcFile = ""

		# PMGCrossSectionTool -- not used this moment
		#

		self._PMGCrossSectionFiles = [
		                              "list_Xsec_TTbar_Download.txt",
		                              "list_Xsec_Exotics_Other_Download.txt",
		                            ]
		self._PMGCrossSectionTool = None


		#####################
		## Private Objects ##
		#####################

		self._XsecConfigObj = None

	def BookHistograms(self):

		#################
		# global stuffs #
		#################

		self._EvtWeight = array.array('d', [1.])
		self.counter = 0
		self.specialCount = 0

		########################
		# Histograms / Ntuples #
		########################

		# Define varaibles we want for tiny-Tree

		self.TrackJetNameList = [
		                         "LeadTrackJet_HCandidateJet",
		                         "SubLeadTrackJet_HCandidateJet",
		                         "LeadTrackJet_VCandidateJet",
		                         "SubLeadTrackJet_VCandidateJet",
		                        ]

		self.EventVarListPython__base = [
		                       "RunNumber",
		                       "EventNumber",
		                       "EventWeight",
		                       "ChannelNumber",
		                       "nPassBtag",
		                       "VHAmbiguityCategory",
		                       "PassVtagging",
		                       "AntiVtaggingCR",
		                       ]

		self.EventVarListPython__kinematic = [
		                       "DiJetMass",
		                       "DiJetDeltaR",
		                       "DiJetDeltaPhi",
		                       "DiJetDeltaEta",
		                       "DiJetDeltaY",
		                       "DiJetPtAsymm",

		                       "HCandidateJetPt",
		                       "HCandidateJetEta",
		                       "HCandidateJetPhi",
		                       "HCandidateJetM",
		                       "HCandidateJetD2",
		                       "HCandidateJetTau21",
		                       "HCandidateJetTau21WTA",
		                       "HCandidateJetNTrack",
		                       "HCandidateJetIsVtagged",
		                       "HCandidateJetNTrackJet",

		                       "VCandidateJetPt",
		                       "VCandidateJetEta",
		                       "VCandidateJetPhi",
		                       "VCandidateJetM",
		                       "VCandidateJetD2",
		                       "VCandidateJetTau21",
		                       "VCandidateJetTau21WTA",
		                       "VCandidateJetNTrack",
		                       "VCandidateJetIsVtagged",
		                       "VCandidateJetWtagCode",
		                       "VCandidateJetZtagCode",
		                       "VCandidateJetNTrackJet",

		                       "dRjj_HCandidateJet",
		                       "dRjj_VCandidateJet",

		                       "LeadTrackJet_HCandidateJet_Pt",
		                       "SubLeadTrackJet_HCandidateJet_Pt",
		                       "LeadTrackJet_VCandidateJet_Pt",
		                       "SubLeadTrackJet_VCandidateJet_Pt",

		                       "LeadTrackJet_HCandidateJet_Eta",
		                       "SubLeadTrackJet_HCandidateJet_Eta",
		                       "LeadTrackJet_VCandidateJet_Eta",
		                       "SubLeadTrackJet_VCandidateJet_Eta",

		                       "LeadTrackJet_HCandidateJet_MV2c10",
		                       "SubLeadTrackJet_HCandidateJet_MV2c10",
		                       "LeadTrackJet_VCandidateJet_MV2c10",
		                       "SubLeadTrackJet_VCandidateJet_MV2c10",
		                     ]

		self.EventVarListPython = self.EventVarListPython__base + self.EventVarListPython__kinematic

		# Define histograms we want

		self.histsvc = {}
		for ibtagSys, btagSysName in enumerate(self._btagSysList):
			self.histsvc[btagSysName] = self.BookHistogramsOneSys(btagSysName, self.outputfileList[ibtagSys])

		########################
		# Tools Initialization #
		########################

		#
		# PRW
		# 

		if self._doPRW:
			self.PRWTool = ROOT.CP.TPileupReweighting()
			self.PRWTool.AddConfigFile(self._PRWConfigFile)
			self.PRWTool.AddLumiCalcFile(self._PRWLumiCalcFile)
			self.PRWTool.Initialize()
		else:
			self.PRWTool = None

		#
		# GRL
		#

		if self._GRLXml != "":
			self.GRLTool = ROOT.Root.TGoodRunsListReader()
			self.GRLTool.SetXMLFile(self._GRLXml)
			self.GRLTool.Interpret()
			self.GRL = self.GRLTool.GetMergedGoodRunsList()
		else:
			self.GRLTool = None
			self.GRL = None

		#
		# PMGCrossSectionTool
		#

		self._PMGCrossSectionTool = ROOT.SampleInfo()
		PMGFileNameVector = ROOT.vector('string')()
		for fileName in self._PMGCrossSectionFiles:
			PMGFileNameVector.push_back( os.environ['Xhh4bPySelector_dir'] + '/External/PMGCrossSectionTool/data/' + fileName )
		if not self._PMGCrossSectionTool.readInfosFromFiles(PMGFileNameVector):
			print "WARNING! Problem in reading Xsection info!"


	def BookHistogramsOneSys(self, btagSysName, outputFile):

		output = {}

		#############################
		# Initialize the histograms #
		#############################

		if self._optDebug: print "BookHistogram of %s: Entering BookHistograms" % (btagSysName)

		histsvc = ROOT.Analysis_AutoHists(outputFile)

		histsvc.Book("ChannelNumber", "ChannelNumber", self._EvtWeight, len(self._ChannelNumberList)+1, -1.5, len(self._ChannelNumberList)-0.5)

		if not self._optSaveMemory:
			histsvc.Book("ChannelNumber_DiJetMass", "ChannelNumber", "DiJetMass", self._EvtWeight, len(self._ChannelNumberList)+1, -1.5, len(self._ChannelNumberList)-0.5, 100, 0, 5000)

		histsvc.Book("HCandidateJetPt", "HCandidateJetPt", self._EvtWeight, 60, 100, 1300)
		histsvc.Book("HCandidateJetEta", "HCandidateJetEta", self._EvtWeight, 24, -3.0, 3.0)
		histsvc.Book("HCandidateJetPhi", "HCandidateJetPhi", self._EvtWeight, 140, -3.5, 3.5)
		histsvc.Book("HCandidateJetM", "HCandidateJetM", self._EvtWeight, 100, 0, 1000)
		histsvc.Book("HCandidateJetD2", "HCandidateJetD2", self._EvtWeight, 40, 0, 8)
		histsvc.Book("HCandidateJetTau21", "HCandidateJetTau21", self._EvtWeight, 30, 0, 1.5)
		histsvc.Book("HCandidateJetTau21WTA", "HCandidateJetTau21WTA", self._EvtWeight, 30, 0, 1.5)
		histsvc.Book("HCandidateJetNTrack", "HCandidateJetNTrack", self._EvtWeight, 100, -0.5, 99.5)

		histsvc.Book("VCandidateJetPt", "VCandidateJetPt", self._EvtWeight, 60, 100, 1300)
		histsvc.Book("VCandidateJetEta", "VCandidateJetEta", self._EvtWeight, 24, -3.0, 3.0)
		histsvc.Book("VCandidateJetPhi", "VCandidateJetPhi", self._EvtWeight, 140, -3.5, 3.5)
		histsvc.Book("VCandidateJetM", "VCandidateJetM", self._EvtWeight, 100, 0, 1000)
		histsvc.Book("VCandidateJetD2", "VCandidateJetD2", self._EvtWeight, 40, 0, 8)
		histsvc.Book("VCandidateJetTau21", "VCandidateJetTau21", self._EvtWeight, 30, 0, 1.5)
		histsvc.Book("VCandidateJetTau21WTA", "VCandidateJetTau21WTA", self._EvtWeight, 30, 0, 1.5)
		histsvc.Book("VCandidateJetNTrack", "VCandidateJetNTrack", self._EvtWeight, 100, -0.5, 99.5)

		if not self._optSaveMemory:
			histsvc.Book("HCandidateJetM_VCandidateJetM", "HCandidateJetM", "VCandidateJetM", self._EvtWeight, 100, 0, 5000, 100, 0, 5000)
			histsvc.Book("HCandidateJetM_VCandidateJetM_fine", "HCandidateJetM", "VCandidateJetM", self._EvtWeight, 1000, 0, 1000, 1000, 0, 1000)

		histsvc.Book("DiJetDeltaPhi", "DiJetDeltaPhi", self._EvtWeight, 70, 0, 3.5)
		histsvc.Book("DiJetDeltaEta", "DiJetDeltaEta", self._EvtWeight, 80, -4, 4)
		histsvc.Book("DiJetDeltaY", "DiJetDeltaY", self._EvtWeight, 80, -4, 4)
		histsvc.Book("DiJetDeltaR", "DiJetDeltaR", self._EvtWeight, 100, 0, 5)
		histsvc.Book("DiJetMass", "DiJetMass", self._EvtWeight, 160, 0, 8000)
		histsvc.Book("DiJetPtAsymm", "DiJetPtAsymm", self._EvtWeight, 20, 0, 1)

		histsvc.Book("dRjj_HCandidateJet", "dRjj_HCandidateJet", self._EvtWeight, 75, 0, 1.5)
		histsvc.Book("dRjj_VCandidateJet", "dRjj_VCandidateJet", self._EvtWeight, 75, 0, 1.5)

		for TrackJetName in self.TrackJetNameList:
			histsvc.Book(TrackJetName + "_Pt", TrackJetName + "_Pt", self._EvtWeight, 50, 0, 500)
			histsvc.Book(TrackJetName + "_Eta", TrackJetName + "_Eta", self._EvtWeight, 24, -3.0, 3.0)
			histsvc.Book(TrackJetName + "_Phi", TrackJetName + "_Phi", self._EvtWeight, 140, -3.5, 3.5)
			histsvc.Book(TrackJetName + "_M", TrackJetName + "_M", self._EvtWeight, 100, 0, 1000)
			histsvc.Book(TrackJetName + "_E", TrackJetName + "_E", self._EvtWeight, 100, 0, 1000)
			histsvc.Book(TrackJetName + "_MV2c10", TrackJetName + "_MV2c10", self._EvtWeight, 220, -1.1, 1.1)

		output['histsvc'] = histsvc

		###############################
		# Initialize Tiny Output Tree #
		###############################

		if self._optDebug: print "BookHistogram of %s: Entering Tiny-Tree" % (btagSysName)

		if self._optTinyTree:
			ntuplesvc_tinytree = ROOT.Analysis_AutoTrees("EventsReduced")
			ntuplesvc_tinytree.GetTree().SetDirectory(outputFile)

			EventVarList = ROOT.vector(ROOT.TString)()
			for EventVar in self.EventVarListPython:
				EventVarList.push_back( EventVar )
			ntuplesvc_tinytree.SetEventVariableList(EventVarList)

			ntuplesvc_tinytree.AddObjVariable("SFList", -1.)
			ntuplesvc_tinytree.AddObjVariable_string("SFNameList", "Unknown")

			if not ntuplesvc_tinytree.SetupBranches():
				print "ERROR! Unable to setup ntuple branches!"
				sys.exit(0)

			output['ntuplesvc_tinytree'] = ntuplesvc_tinytree

		##########
		# return #
		##########

		return output


	def ProcessEntry(self, tree, entry):

		self.counter += 1

		##############################
		# Reset histograms / ntuples #
		##############################

		for btagSysName in self._btagSysList:
			self.histsvc[btagSysName]['histsvc'].Reset()

			if self._optTinyTree:
				self.histsvc[btagSysName]['ntuplesvc_tinytree'].ResetBranches()

		###################
		# Data/MC Control #
		###################

		if self._ForceDataMC is None:
			_isMC = hasattr(tree, 'mcEventWeight')
		else:
			if self._ForceDataMC == "Data":
				_isMC = False
			elif self._ForceDataMC == "MC":
				_isMC = True
			else:
				print "Unable to recognize self._ForceDataMC",self._ForceDataMC
				return

		#########################
		# MC Channel Number Cut #
		#########################

		if _isMC and (self._optChannelCut is not None):
			if tree.mcChannelNumber != self._optChannelCut:
				return

		################################
		# BtagSys event-by-event Setup #
		################################

		if self._optDebug: print "ProcessEntry: BtagSys event-by-event Setup"

		# for unknown reason, jet_ak2track_asso_sysname could be of size 0!
		_hasBtagSFBranch = hasattr(tree, "jet_ak2track_asso_sys")
		if _hasBtagSFBranch and (tree.jet_ak2track_asso_sysname.size() == 0):
			_hasBtagSFBranch = False

		# Indexing the btag systemaitcs under consideration
		_EventBtagIndex = {}
		for btagSysName in self._btagSysList:
			_EventBtagIndex[btagSysName] = -1

		for i in range(tree.jet_ak2track_asso_sysname.size()):
			currentBtagSysName = tree.jet_ak2track_asso_sysname[i]

			if currentBtagSysName not in self._btagSysList: continue

			if _EventBtagIndex[currentBtagSysName] == -1:
				_EventBtagIndex[currentBtagSysName] = i
			else:
				# this should never happen
				print "ERROR! Duplicate systematics name stored in MiniNtuple! Aborting now ..."
				sys.exit(0)

		#########################
		# Interlock on JERStudy #
		#########################

		if self._doJERStudy and (not _isMC):
			self._doJERStudy = False

		####################
		# Deal with weghts #
		####################

		if self._optDebug: print "ProcessEntry: Event weight computation"

		# interlock on ApplyXsec
		if (self._ApplyXsecWeight) and (not _isMC):
			self._ApplyXsecWeight = False

		if _isMC:
			if self._doPRW:
				PRW = self.PRWTool.GetCombinedWeight(tree.runNumber, tree.mcChannelNumber, tree.averageInteractionsPerCrossing)
			else:
				PRW = tree.weight_pileup
			self._EvtWeight[0] = tree.mcEventWeight * tree.weight_pileup * self.GetXsecWeight(tree)
		else:
			self._EvtWeight[0] = 1.

		if _isMC: 
			for btagSysName in self._btagSysList:
				histsvc = self.histsvc[btagSysName]['histsvc']
				histsvc.Set("ChannelNumber", tree.mcChannelNumber)

		########################
		# Mtt Stitching for MC #
		########################

		if self._optDebug: print "ProcessEntry: Mtt stitching for MC"

		if _isMC:
			# Interlock
			if self._doMttStitch and (not hasattr(tree, 'truth_mtt')):
				print "WARNING! No mtt information in n-tuple, while mtt stitching is requested. It will be turned OFF"
				self._doMttStitch = False

			# apply both mtt rejection for inclusive ttbar sample
			# and weight correction for mtt slices
			if self._doMttStitch:
				if not self.MttStitch(tree):
					return

			if hasattr(tree, 'truth_mtt'):
				for btagSysName in self._btagSysList:
					histsvc = self.histsvc[btagSysName]['histsvc']
					histsvc.AutoFill("GoodEvent", "_MttStudy", "truth_mtt_%s" % (tree.mcChannelNumber), tree.truth_mtt/1000., self._EvtWeight[0], 300, 0, 3000)


		############
		# Triggers #
		############

		if self._optDebug: print "ProcessEntry: Trigger"

		PassedTriggerList = list(set(tree.passedTriggers).intersection(set(self._TriggerList)))
		if len(PassedTriggerList) > 0: 
			PassedTriggerList.append("OR")
		PassedTriggerList.append("All")

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "Initial", _isMC)
		self.MakeCutflowPlot(tree, "Initial", _isMC)

		#
		# Trigger Cut
		#

		if self._doTriggerCut:

			if _isMC:
				# have to do the trigger emulation of HLT_j420_a10_lcw_L1J100 on MC
				if not self.MCTriggerEmulation(tree):
					return
			else:
				if "OR" not in PassedTriggerList:
					return

		self.MakeCutflowPlot(tree, "PassTrigger", _isMC)

		#######
		# GRL #
		#######

		if self._optDebug: print "ProcessEntry: GRL"

		if not _isMC:
			if self.GRL is None:
				print "WARNING! GRL not setup for Data!"
			else:
				if not self.GRL.HasRunLumiBlock(tree.runNumber, tree.lumiBlock):
					return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassGRL", _isMC)
		self.MakeCutflowPlot(tree, "PassGRL", _isMC)

		################
		# Jet Cleaning #
		################

		# old way, depricated
		# passJetCleaning = True
		# for iAKT4 in range(tree.resolvedJets_pt.size()):
		# 	AKT4_pt = tree.resolvedJets_pt[iAKT4]
		# 	AKT4_passClean = tree.resolvedJets_clean_passLooseBad[iAKT4]

		# 	if AKT4_pt < 30.: continue   # resolved people use GeV 

		# 	passJetCleaning = (passJetCleaning and (AKT4_passClean == 1))

		# if not passJetCleaning: return

		# for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassJetCleaning", _isMC)
		# self.MakeCutflowPlot(tree, "PassJetCleaning", _isMC)

		# recommended way
		passJetCleaning = tree.event_cleaning_qqbb

		if not passJetCleaning: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassJetCleaning", _isMC)
		self.MakeCutflowPlot(tree, "PassJetCleaning", _isMC)

		###############
		# Lepton Veto #
		###############

		if self._doLeptonVeto:

			if tree.n_muons_veto > 0: return

			for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassMuonVetoCut", _isMC)
			self.MakeCutflowPlot(tree, "PassMuonVetoCut", _isMC)

			if tree.n_electrons_veto > 0: return

			for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassElectronVetoCut", _isMC)
			self.MakeCutflowPlot(tree, "PassElectronVetoCut", _isMC)

			for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassLeptonVetoCut", _isMC)
			self.MakeCutflowPlot(tree, "PassLeptonVetoCut", _isMC)

		#####################
		# Calo-jet Business #
		#####################

		if self._optDebug: print "ProcessEntry: Calo-jet Business"

		#
		# calo-jet multiplicity cut
		#

		if tree.hcand_boosted_n < 2: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassCaloJetMultiCut", _isMC)
		self.MakeCutflowPlot(tree, "PassCaloJetMultiCut", _isMC)


		#
		# calo-jets Reconstruction
		#

		LeadCaloJet = ROOT.TLorentzVector()
		LeadCaloJet.SetPtEtaPhiM(tree.hcand_boosted_pt[0]/1000., tree.hcand_boosted_eta[0], tree.hcand_boosted_phi[0], tree.hcand_boosted_m[0]/1000.)
		LeadCaloJet = ROOT.Particle(LeadCaloJet)
		# old tagging tool
		if self._WZWP == "Medium":
			LeadCaloJet.Set("WtagCode", tree.hcand_boosted_Wtag_medium[0])
			LeadCaloJet.Set("ZtagCode", tree.hcand_boosted_Ztag_medium[0])
			LeadCaloJet.Set("WZTagged", (tree.hcand_boosted_Wtag_medium[0] == 3) or (tree.hcand_boosted_Ztag_medium[0] == 3))   # W/Z, mass+D2 cut, medium
		elif self._WZWP == "Tight":
			LeadCaloJet.Set("WtagCode", tree.hcand_boosted_Wtag_tight[0])
			LeadCaloJet.Set("ZtagCode", tree.hcand_boosted_Ztag_tight[0])
			LeadCaloJet.Set("WZTagged", (tree.hcand_boosted_Wtag_tight[0] == 3) or (tree.hcand_boosted_Ztag_tight[0] == 3))   # W/Z, mass+D2 cut, tight
		# new tagging tool
		elif self._WZWP == "50":
			LeadCaloJet.Set("WtagCode", tree.hcand_boosted_smoothWtag_50[0])
			LeadCaloJet.Set("ZtagCode", tree.hcand_boosted_smoothZtag_50[0])
			LeadCaloJet.Set("WZTagged", (tree.hcand_boosted_smoothWtag_50[0] == 1) or (tree.hcand_boosted_smoothZtag_50[0] == 1))
		elif self._WZWP == "80":
			LeadCaloJet.Set("WtagCode", tree.hcand_boosted_smoothWtag_80[0])
			LeadCaloJet.Set("ZtagCode", tree.hcand_boosted_smoothZtag_80[0])
			LeadCaloJet.Set("WZTagged", (tree.hcand_boosted_smoothWtag_80[0] == 1) or (tree.hcand_boosted_smoothZtag_80[0] == 1))
		else:
			print "ERROR! Unrecognized WZ Workign point:",self._WZWP
			sys.exit(0)
		LeadCaloJet.Set("D2", tree.hcand_boosted_D2[0])
		LeadCaloJet.Set("Tau21", tree.hcand_boosted_Tau21[0])
		LeadCaloJet.Set("Tau21WTA", tree.hcand_boosted_Tau21WTA[0])
		LeadCaloJet.Set("nTrack", tree.hcand_boosted_nTrack[0])
		LeadCaloJet.Set("nHBosons", tree.hcand_boosted_nHBosons[0])
		LeadCaloJet.Set("nWBosons", tree.hcand_boosted_nWBosons[0])
		LeadCaloJet.Set("nZBosons", tree.hcand_boosted_nZBosons[0])
		LeadCaloJet.Set("nTrackJet", tree.jet_ak2track_asso_n[0])

		SubLeadCaloJet = ROOT.TLorentzVector()
		SubLeadCaloJet.SetPtEtaPhiM(tree.hcand_boosted_pt[1]/1000., tree.hcand_boosted_eta[1], tree.hcand_boosted_phi[1], tree.hcand_boosted_m[1]/1000.)
		SubLeadCaloJet = ROOT.Particle(SubLeadCaloJet)
		# old tagging tool
		if self._WZWP == "Medium":
			SubLeadCaloJet.Set("WtagCode", tree.hcand_boosted_Wtag_medium[1])
			SubLeadCaloJet.Set("ZtagCode", tree.hcand_boosted_Ztag_medium[1])
			SubLeadCaloJet.Set("WZTagged", (tree.hcand_boosted_Wtag_medium[1] == 3) or (tree.hcand_boosted_Ztag_medium[1] == 3))  # W/Z, mass+D2 cut, medium
		elif self._WZWP == "Tight":
			SubLeadCaloJet.Set("WtagCode", tree.hcand_boosted_Wtag_tight[1])
			SubLeadCaloJet.Set("ZtagCode", tree.hcand_boosted_Ztag_tight[1])
			SubLeadCaloJet.Set("WZTagged", (tree.hcand_boosted_Wtag_tight[1] == 3) or (tree.hcand_boosted_Ztag_tight[1] == 3))  # W/Z, mass+D2 cut, tight
		# new tagging tool
		elif self._WZWP == "50":
			SubLeadCaloJet.Set("WtagCode", tree.hcand_boosted_smoothWtag_50[1])
			SubLeadCaloJet.Set("ZtagCode", tree.hcand_boosted_smoothZtag_50[1])
			SubLeadCaloJet.Set("WZTagged", (tree.hcand_boosted_smoothWtag_50[1] == 1) or (tree.hcand_boosted_smoothZtag_50[1] == 1))
		elif self._WZWP == "80":
			SubLeadCaloJet.Set("WtagCode", tree.hcand_boosted_smoothWtag_80[1])
			SubLeadCaloJet.Set("ZtagCode", tree.hcand_boosted_smoothZtag_80[1])
			SubLeadCaloJet.Set("WZTagged", (tree.hcand_boosted_smoothWtag_80[1] == 1) or (tree.hcand_boosted_smoothZtag_80[1] == 1))
		else:
			print "ERROR! Unrecognized WZ Working point:",self._WZWP
			sys.exit(0)
		SubLeadCaloJet.Set("D2", tree.hcand_boosted_D2[1])
		SubLeadCaloJet.Set("Tau21", tree.hcand_boosted_Tau21[1])
		SubLeadCaloJet.Set("Tau21WTA", tree.hcand_boosted_Tau21WTA[1])
		SubLeadCaloJet.Set("nTrack", tree.hcand_boosted_nTrack[1])
		SubLeadCaloJet.Set("nHBosons", tree.hcand_boosted_nHBosons[1])
		SubLeadCaloJet.Set("nWBosons", tree.hcand_boosted_nWBosons[1])
		SubLeadCaloJet.Set("nZBosons", tree.hcand_boosted_nZBosons[1])
		SubLeadCaloJet.Set("nTrackJet", tree.jet_ak2track_asso_n[1])

		CaloJetList = [LeadCaloJet, SubLeadCaloJet]

		#
		# some quick calo-jet kineamtics distribution before any cut
		#

		for btagSysName in self._btagSysList:
			histsvc = self.histsvc[btagSysName]['histsvc']

			histsvc.AutoFill("GoodEvent", "_BeforeCaloJetKinematicCut", "LeadCaloJetPt", LeadCaloJet.p.Pt(), self._EvtWeight[0], 50, 100, 3100)
			histsvc.AutoFill("GoodEvent", "_BeforeCaloJetKinematicCut", "SubLeadCaloJetPt", SubLeadCaloJet.p.Pt(), self._EvtWeight[0], 50, 100, 3100)

			histsvc.AutoFill("GoodEvent", "_BeforeCaloJetKinematicCut", "LeadCaloJetPt_fine", LeadCaloJet.p.Pt(), self._EvtWeight[0], 150, 0, 3000)
			histsvc.AutoFill("GoodEvent", "_BeforeCaloJetKinematicCut", "SubLeadCaloJetPt_fine", SubLeadCaloJet.p.Pt(), self._EvtWeight[0], 150, 0, 3000)

		# temporary hack
		# touch
		# return

		#
		# Calo-Jet Response (for MC Only). Should be before muon correciton
		#

		if self._doJERStudy:
			CaloJetListInputForJER = [(iCaloJet, CaloJet) for iCaloJet, CaloJet in enumerate(CaloJetList)]

			self.MakeJERPlots(tree, CaloJetListInputForJER, "BeforeCaloJetKinematicCut")
			self.MakeJERPlots2(tree, CaloJetListInputForJER, "BeforeCaloJetKinematicCut")

		##########################
		# Calo Jet Kinematic Cut #
		##########################

		if self._optDebug: print "ProcessEntry: Calo-jet kinematic cut"

		# reminder: the baseline 250 GeV and 2.0 eta cut is on calo-jet with NO muon correction

		#
		# pT/eta cut
		#

		# if LeadCaloJet.p.Pt() < 350.:      return
		if LeadCaloJet.p.Pt() < 450.:      return       # touch
		# if LeadCaloJet.p.Pt() < 250.:      return       # touch
		if abs(LeadCaloJet.p.Eta()) > 2.0: return

		if SubLeadCaloJet.p.Pt() < 250.:      return
		if abs(SubLeadCaloJet.p.Eta()) > 2.0: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassCaloKinematicsCut", _isMC)
		self.MakeCutflowPlot(tree, "PassCaloKinematicsCut", _isMC)

		#
		# mass cut (no muon correction)
		#

		if LeadCaloJet.p.M() < self._JetMassCut: return
		if SubLeadCaloJet.p.M() < self._JetMassCut: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassCaloJetMassCut", _isMC)
		self.MakeCutflowPlot(tree, "PassCaloJetMassCut", _isMC)

		#
		# pT upper bound (no muon correction)

		if LeadCaloJet.p.Pt() > self._JetPtUpBound: return
		if SubLeadCaloJet.p.Pt() > self._JetPtUpBound: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassCaloJetPtUpBound", _isMC)
		self.MakeCutflowPlot(tree, "PassCaloJetPtUpBound", _isMC)

		# 
		# look at calo-jet dEta distribution before cuts
		# 

		if self._optPeekdEta:
			self.FillOneVarForAllSignal(tree, _isMC, "BeforedEtaCut", "dEta", LeadCaloJet.p.Eta() - SubLeadCaloJet.p.Eta(), self._EvtWeight[0], 80, -4, 4)

			chi2 = ROOT.TMath.Exp(2*abs(LeadCaloJet.p.Rapidity() - SubLeadCaloJet.p.Rapidity()))
			self.FillOneVarForAllSignal(tree, _isMC, "BeforedEtaCut", "CosTheta", (chi2-1)/(chi2+1), self._EvtWeight[0], 60, -1, 2)

			DiJetSys = LeadCaloJet.p + SubLeadCaloJet.p
			LeadCaloJetp4_COM = ROOT.TLorentzVector(LeadCaloJet.p)
			SubLeadCaloJetp4_COM = ROOT.TLorentzVector(SubLeadCaloJet.p)

			LeadCaloJetp4_COM.Boost(-DiJetSys.BoostVector())
			SubLeadCaloJetp4_COM.Boost(-DiJetSys.BoostVector())

			self.FillOneVarForAllSignal(tree, _isMC, "BeforedEtaCut", "CosTheta_Lead", LeadCaloJetp4_COM.Vect().CosTheta(), self._EvtWeight[0], 60, -1, 2)
			self.FillOneVarForAllSignal(tree, _isMC, "BeforedEtaCut", "CosTheta_SubLead", SubLeadCaloJetp4_COM.Vect().CosTheta(), self._EvtWeight[0], 60, -1, 2)

		# 
		# Event Topology Cut
		# 

		dEta_beforeMuonCorr = abs(LeadCaloJet.p.Eta() - SubLeadCaloJet.p.Eta())
		dy_beforeMuonCorr = abs(LeadCaloJet.p.Rapidity() - SubLeadCaloJet.p.Rapidity())
		DiJetPtAsymm_beforeMuonCorr = abs(LeadCaloJet.p.Pt() - SubLeadCaloJet.p.Pt()) / (LeadCaloJet.p.Pt() + SubLeadCaloJet.p.Pt())
		DiJetMass_beforeMuonCorr = (LeadCaloJet.p + SubLeadCaloJet.p).M()

		# PassdEtaCut = ( dEta_beforeMuonCorr < (2e-4 * DiJetMass_beforeMuonCorr + 1.) )
		# PassdEtaCut = (dEta_beforeMuonCorr < 1.6)                                    # touch
		PassdEtaCut = (dy_beforeMuonCorr < 1.6)                                    
		
		# PassPtAsymmCut = (DiJetPtAsymm_beforeMuonCorr < 0.25)
		PassPtAsymmCut = True                             # don't cut on this anymore

		if not PassdEtaCut: return 

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassdEtaCut", _isMC)
		self.MakeCutflowPlot(tree, "PassdEtaCut", _isMC)

		if not PassPtAsymmCut: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassPtAsymmCut", _isMC)
		self.MakeCutflowPlot(tree, "PassPtAsymmCut", _isMC)

		# ***************************************************************************************************************************************

		#
		# At least one V-tagged cut not applied, in order to leave room for anti-V-tagging CR
		# 

		# #
		# # some quick calo-jet kineamtics distribution BEFORE V-tagging
		# #

		# for btagSysName in self._btagSysList:
		# 	histsvc = self.histsvc[btagSysName]['histsvc']

		# 	histsvc.AutoFill("GoodEvent", "_BeforeAtLeastOneVtag", "LeadCaloJetPt", LeadCaloJet.p.Pt(), self._EvtWeight[0], 50, 100, 3100)
		# 	histsvc.AutoFill("GoodEvent", "_BeforeAtLeastOneVtag", "SubLeadCaloJetPt", SubLeadCaloJet.p.Pt(), self._EvtWeight[0], 50, 100, 3100)
		# 	histsvc.AutoFill("GoodEvent", "_BeforeAtLeastOneVtag", "MJJ", (LeadCaloJet.p + SubLeadCaloJet.p).M(), self._EvtWeight[0], 160, 0, 8000)

		# #
		# # At least one calo-jet should be V-tagged
		# #

		# PassAtLeastOneVtag = (LeadCaloJet.Double("WZTagged") == 1) or (SubLeadCaloJet.Double("WZTagged") == 1)

		# if not PassAtLeastOneVtag: return

		# for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassAtLeastOneVtag", _isMC)
		# self.MakeCutflowPlot(tree, "PassAtLeastOneVtag", _isMC)

		# #
		# # some quick calo-jet kineamtics distribution AFTER V-tagging
		# #

		# for btagSysName in self._btagSysList:
		# 	histsvc = self.histsvc[btagSysName]['histsvc']

		# 	histsvc.AutoFill("GoodEvent", "_AfterAtLeastOneVtag", "LeadCaloJetPt", LeadCaloJet.p.Pt(), self._EvtWeight[0], 50, 100, 3100)
		# 	histsvc.AutoFill("GoodEvent", "_AfterAtLeastOneVtag", "SubLeadCaloJetPt", SubLeadCaloJet.p.Pt(), self._EvtWeight[0], 50, 100, 3100)
		# 	histsvc.AutoFill("GoodEvent", "_AfterAtLeastOneVtag", "MJJ", (LeadCaloJet.p + SubLeadCaloJet.p).M(), self._EvtWeight[0], 160, 0, 8000)

		# ***************************************************************************************************************************************


		############################
		# Track-jet Reconstruction #
		############################

		if self._optDebug: print "ProcessEntry: Track-jet Reconstruction"

		# INFO: Starting from hh4b-v00-v01-01, track-jet selection has already been applied when producing miniNtuple. So it becomes redundant to do it here

		if self._optDebug: print "ProcessEntry: Before processing first track-jet"

		LeadCaloJet.AddVec("AssocTrackJets")
		for iTrackJet in range(tree.jet_ak2track_asso_pt[0].size()):

			if iTrackJet >= 2: break           # we don't care third track-jet and so on

			TrackJet = ROOT.TLorentzVector()
			TrackJet.SetPtEtaPhiM(tree.jet_ak2track_asso_pt[0][iTrackJet]/1000., tree.jet_ak2track_asso_eta[0][iTrackJet], tree.jet_ak2track_asso_phi[0][iTrackJet], tree.jet_ak2track_asso_m[0][iTrackJet]/1000.)

			TrackJet = ROOT.Particle(TrackJet)
			TrackJet.Set("MV2c20", tree.jet_ak2track_asso_MV2c20[0][iTrackJet])
			TrackJet.Set("MV2c10", tree.jet_ak2track_asso_MV2c10[0][iTrackJet])
			TrackJet.Set("MV2c00", tree.jet_ak2track_asso_MV2c00[0][iTrackJet])
			TrackJet.Set("MV2c100", tree.jet_ak2track_asso_MV2c100[0][iTrackJet])

			for btagSysName in self._btagSysList:
				btagIndex = _EventBtagIndex[btagSysName]
				if (btagIndex == -1) or self._ResetSF:
					SF = 1.
				else:
					SF = tree.jet_ak2track_asso_sys[0][iTrackJet][btagIndex]

				TrackJet.Set("SF"+btagSysName, SF)

			LeadCaloJet.Add("AssocTrackJets", TrackJet)

		if self._optDebug: print "ProcessEntry: Before processing second track-jet"

		SubLeadCaloJet.AddVec("AssocTrackJets")
		for iTrackJet in range(tree.jet_ak2track_asso_pt[1].size()):

			if iTrackJet >= 2: break          # we don't care third track-jet and so on

			TrackJet = ROOT.TLorentzVector()
			TrackJet.SetPtEtaPhiM(tree.jet_ak2track_asso_pt[1][iTrackJet]/1000., tree.jet_ak2track_asso_eta[1][iTrackJet], tree.jet_ak2track_asso_phi[1][iTrackJet], tree.jet_ak2track_asso_m[1][iTrackJet]/1000.)

			TrackJet = ROOT.Particle(TrackJet)
			TrackJet.Set("MV2c20", tree.jet_ak2track_asso_MV2c20[1][iTrackJet])
			TrackJet.Set("MV2c10", tree.jet_ak2track_asso_MV2c10[1][iTrackJet])
			TrackJet.Set("MV2c00", tree.jet_ak2track_asso_MV2c00[1][iTrackJet])
			TrackJet.Set("MV2c100", tree.jet_ak2track_asso_MV2c100[1][iTrackJet])

			for btagSysName in self._btagSysList:
				btagIndex = _EventBtagIndex[btagSysName]
				if (btagIndex == -1) or self._ResetSF:
					SF = 1.
				else:
					SF = tree.jet_ak2track_asso_sys[1][iTrackJet][btagIndex]

				TrackJet.Set("SF"+btagSysName, SF)

			SubLeadCaloJet.Add("AssocTrackJets", TrackJet)

		#################################
		# Associate Muons to Track-jets #
		# No muon correction here!      #
		#################################

		if self._optDebug: print "ProcessEntry: Associating Muons to track-jets. Attention: No muon correction done here!"

		CaloJetListForMuonCorrection = [ LeadCaloJet, SubLeadCaloJet ]
		TrackJetListForMuonCorrection = []
		for CaloJet in CaloJetListForMuonCorrection: TrackJetListForMuonCorrection += [ TrackJet for TrackJet in CaloJet.ObjVec("AssocTrackJets") ]

		Muons = []
		for iMuon in range(tree.nmuon):
			Muon = ROOT.TLorentzVector()
			Muon.SetPtEtaPhiM(tree.muon_pt[iMuon], tree.muon_eta[iMuon], tree.muon_phi[iMuon], tree.muon_m[iMuon])
			Muon = ROOT.Particle(Muon)

			Muons.append( Muon )

			if self._doMuonCorrection:
				if Muon.p.Pt() < self._MuonPtCut:         continue
				if abs(Muon.p.Eta()) > self._MuonEtaCut:  continue
				if not self.PassMuonQualityCut(tree, iMuon): continue

				MatchTrackJet = None
				MatchTrackJetDR = 9e9
				for TrackJet in TrackJetListForMuonCorrection:
					dR = Muon.p.DeltaR(TrackJet.p)

					if dR > 0.2: continue
					if not self.PassTrackJetBtag(TrackJet, self._TrackJetWP): continue

					if dR < MatchTrackJetDR:
						MatchTrackJetDR = dR
						MatchTrackJet = TrackJet

				if MatchTrackJet is not None:
					if MatchTrackJet.Exists("MuonAssocIndex"):
						oldDR = MatchTrackJet.Double("MuonAssocDR")

						if MatchTrackJetDR < oldDR:
							MatchTrackJet.Set("MuonAssocIndex", iMuon)
							MatchTrackJet.Set("MuonAssocDR", MatchTrackJetDR)
					else:
						MatchTrackJet.Set("MuonAssocIndex", iMuon)
						MatchTrackJet.Set("MuonAssocDR", MatchTrackJetDR)


		###########################
		# Now solve V/H ambiguity #
		###########################

		# V/H ambiguity category

		VHAmbiguityCategory = -1   # -1: initialized value
		                           # 0 : ambiguous that one has to resort to mass distance
		                           # 1 : unambiguous by using V/H-tagging 

		if self._VHAmbiguityScheme == 1:
			#
			# one v-tagged, one anti-v-tagged
			#

			PassVtagCut = (LeadCaloJet.Double("WZTagged") != SubLeadCaloJet.Double("WZTagged"))
			if not PassVtagCut: return

			VHAmbiguityCategory = 1

			#
			# Determine V-candidate and the left-over is H-candidate automatically
			#

			if LeadCaloJet.Double("WZTagged") == 1:
				VCandidateJet = LeadCaloJet
				HCandidateJet = SubLeadCaloJet
			else:
				VCandidateJet = SubLeadCaloJet
				HCandidateJet = LeadCaloJet

		elif self._VHAmbiguityScheme in [2, 3]:
			# Higgs tagging first
			LeadCaloJet_Htag    = self.HiggsTagging(LeadCaloJet, Muons, self._HiggsMassCut, self._VHAmbiguityScheme == 3)
			SubLeadCaloJet_Htag = self.HiggsTagging(SubLeadCaloJet, Muons, self._HiggsMassCut, self._VHAmbiguityScheme == 3)

			scenario_VH = ( (LeadCaloJet.Double("WZTagged") == 1) and SubLeadCaloJet_Htag )
			scenario_HV = ( LeadCaloJet_Htag and (SubLeadCaloJet.Double("WZTagged") == 1) )
			scenario    = ( (scenario_VH << 1) | scenario_HV )

			# if scenario == 0: return

			if scenario == 1:
				VHAmbiguityCategory = 1
				VCandidateJet = SubLeadCaloJet
				HCandidateJet = LeadCaloJet
			elif scenario == 2:
				VHAmbiguityCategory = 1
				VCandidateJet = LeadCaloJet
				HCandidateJet = SubLeadCaloJet
			elif (scenario == 3) or (scenario == 0):
				VHAmbiguityCategory = 0
				# based on the distance now
				# V mass and Higgs mass number are hard-coded here
				distance_VH = (LeadCaloJet.p.M() - 85.)**2 + (SubLeadCaloJet.Double("MuonCorrectedMassIfHiggs") - 125.)**2
				distance_HV = (LeadCaloJet.Double("MuonCorrectedMassIfHiggs") - 125.)**2 + (SubLeadCaloJet.p.M() - 85.)**2

				if distance_VH <= distance_HV:
					if distance_VH == distance_HV:
						print "Are you kidding me?! A tie?! I am gonna assign randomly"
					VCandidateJet = LeadCaloJet
					HCandidateJet = SubLeadCaloJet
				else:
					VCandidateJet = SubLeadCaloJet
					HCandidateJet = LeadCaloJet
					
			else:
				print "ERROR! Unexpected scenario number: ",scenario
				sys.exit(0)

		elif self._VHAmbiguityScheme in [4, 5]:
			# Higgs tagging first
			LeadCaloJet_Htag    = self.HiggsTagging(LeadCaloJet, Muons, self._HiggsMassCut, self._VHAmbiguityScheme == 5)
			SubLeadCaloJet_Htag = self.HiggsTagging(SubLeadCaloJet, Muons, self._HiggsMassCut, self._VHAmbiguityScheme == 5)

			# make assignment based on V-tagging and distance
			scenario = ( ((LeadCaloJet.Double("WZTagged") == 1) << 1)  | (SubLeadCaloJet.Double("WZTagged") == 1) )

			if scenario == 0:
				print "ERROR! You are not supposed to get this scenario!"
				sys.exit(0)
			elif scenario == 1:
				VHAmbiguityCategory = 1
				VCandidateJet = SubLeadCaloJet
				HCandidateJet = LeadCaloJet
			elif scenario == 2:
				VHAmbiguityCategory = 1
				VCandidateJet = LeadCaloJet
				HCandidateJet = SubLeadCaloJet
			elif scenario == 3:
				if LeadCaloJet_Htag and (not SubLeadCaloJet_Htag):
					VHAmbiguityCategory = 1
					VCandidateJet = SubLeadCaloJet
					HCandidateJet = LeadCaloJet
				elif (not LeadCaloJet) and (SubLeadCaloJet_Htag):
					VHAmbiguityCategory = 1
					VCandidateJet = LeadCaloJet
					HCandidateJet = SubLeadCaloJet
				else:
					VHAmbiguityCategory = 0
					distance_VH = (LeadCaloJet.p.M() - 85.)**2 + (SubLeadCaloJet.Double("MuonCorrectedMassIfHiggs") - 125.)**2
					distance_HV = (LeadCaloJet.Double("MuonCorrectedMassIfHiggs") - 125.)**2 + (SubLeadCaloJet.p.M() - 85.)**2

					if distance_VH <= distance_HV:
						if distance_VH == distance_HV:
							print "Are you kidding me?! A tie?! I am gonna assign randomly"
						VCandidateJet = LeadCaloJet
						HCandidateJet = SubLeadCaloJet
					else:
						VCandidateJet = SubLeadCaloJet
						HCandidateJet = LeadCaloJet
			else:
				print "ERROR! Unexpected scenario number: ",scenario
				sys.exit(0)
		elif self._VHAmbiguityScheme == 6:
			# just to get the muon corrected mass, if it is Higgs
			LeadCaloJet_Htag    = self.HiggsTagging(LeadCaloJet, Muons, self._HiggsMassCut, False)
			SubLeadCaloJet_Htag = self.HiggsTagging(SubLeadCaloJet, Muons, self._HiggsMassCut, False)

			# assignment purely based on distance
			distance_VH = (LeadCaloJet.p.M() - 85.)**2 + (SubLeadCaloJet.Double("MuonCorrectedMassIfHiggs") - 125.)**2
			distance_HV = (LeadCaloJet.Double("MuonCorrectedMassIfHiggs") - 125.)**2 + (SubLeadCaloJet.p.M() - 85.)**2

			if distance_VH <= distance_HV:
				if distance_VH == distance_HV:
					print "Are you kidding me?! A tie?! I am gonna assign randomly"
				VCandidateJet = LeadCaloJet
				HCandidateJet = SubLeadCaloJet
			else:
				VCandidateJet = SubLeadCaloJet
				HCandidateJet = LeadCaloJet
		elif self._VHAmbiguityScheme == 7:
			# just see who is heavier
			VHAmbiguityCategory = 1

			if LeadCaloJet.p.M() > SubLeadCaloJet.p.M():
				HCandidateJet = LeadCaloJet
				VCandidateJet = SubLeadCaloJet
			else:
				HCandidateJet = SubLeadCaloJet
				VCandidateJet = LeadCaloJet

		else:
			print "ERROR! Undefined ambiguity scheme:",self._VHAmbiguityScheme
			sys.exit(0)


		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassVHAmbiguity", _isMC)
		self.MakeCutflowPlot(tree, "PassVHAmbiguity", _isMC)

		############
		# MET Veto #
		############

		if self._doMETVeto:

			passMETsumCut = (tree.METsum/1000. > 150.)

			dPhi_HcandMET = abs(tree.METphi - HCandidateJet.p.Phi())
			if(dPhi_HcandMET > ROOT.TMath.Pi()): dPhi_HcandMET = 2*ROOT.TMath.Pi() - dPhi_HcandMET
			passMETdphiCut = (dPhi_HcandMET > 120.*ROOT.TMath.Pi()/180.)

			if passMETsumCut and passMETdphiCut: return

			for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassMETVetoCut", _isMC)
			self.MakeCutflowPlot(tree, "PassMETVetoCut", _isMC)

		# probability of getting correct VH assignment #

		PassCorrectVHAssignment = (HCandidateJet.Double("nHBosons") == 1) and (VCandidateJet.Double("nWBosons") + VCandidateJet.Double("nZBosons") == 1)
		if PassCorrectVHAssignment:
			for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassVHAmbiguity__CorrectAssignment", _isMC)
			self.MakeCutflowPlot(tree, "PassVHAmbiguity__CorrectAssignment", _isMC)

		#########################################################################################
		# Categorize event based on V-tagging (a subset of anti-V-tagging might be used for CR) #
		#########################################################################################

		if (self._WZWP == "Medium") or (self._WZWP == "Tight"):
			PassVtagging = (VCandidateJet.Double("WZTagged") == 1)
			AntiVtaggingCR = (VCandidateJet.Double("WtagCode") <= 1) and (VCandidateJet.Double("ZtagCode") <= 1)     # fail both W and Z mass window cut, making sure it fails the V-tagging. However, the "actual" anti-V-tagging CR might still be a subset of this
		elif (self._WZWP == "50") or (self._WZWP == "80"):
			PassVtagging = (VCandidateJet.Double("WZTagged") == 1)

			WtagCodeInt = int(VCandidateJet.Double("WtagCode"))
			ZtagCodeInt = int(VCandidateJet.Double("ZtagCode"))
			AntiVtaggingCR = (WtagCodeInt & 60) and (ZtagCodeInt & 60)     # in new tagging tool, failing both W and Z mass window cut means & with code 111100 (60)
		else:
			print "ERROR! Unrecognized WZ Working point:",self._WZWP
			sys.exit(1)

		# in case buggy things happen ...
		if PassVtagging and AntiVtaggingCR:
			print "ERROR! PassVtagging and AntiVtaggingCR are supposed to be orthogonal to each other!"
			sys.exit(0)

		if (not PassVtagging) and (not AntiVtaggingCR): return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassVtaggingORAntiVtaggingCR", _isMC)
		self.MakeCutflowPlot(tree, "PassVtaggingORAntiVtaggingCR", _isMC)

		VtagString = "None"
		if PassVtagging:
			VtagString = "PassVtagging"
		if AntiVtaggingCR:
			VtagString = "AntiVtaggingCR"

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, VtagString, _isMC)
		self.MakeCutflowPlot(tree, VtagString, _isMC)

		##################################################
		# Now put in the muon-corrected 4-p for Calo-Jet #
		##################################################

		for iCaloJet, CaloJet in enumerate([HCandidateJet]):
			sumMuonCorr = ROOT.TLorentzVector()

			for TrackJet in CaloJet.ObjVec("AssocTrackJets"):
				if TrackJet.Exists("MuonAssocIndex"):
					sumMuonCorr += (Muons[TrackJet.Int("MuonAssocIndex")].p)

			CaloJet.p = CaloJet.p + sumMuonCorr

		#################################################
		# From now on, all calo-jet has muon correction #
		# For kinematics distribution, they should      #
		# start from here                               #
		#################################################

		####################################################################################################################

		############################
		# Fill Calo-Jet kinematics #
		############################

		for btagSysName in self._btagSysList:
			histsvc = self.histsvc[btagSysName]['histsvc']

			histsvc.Set("HCandidateJetPt", HCandidateJet.p.Pt())
			histsvc.Set("HCandidateJetEta", HCandidateJet.p.Eta())
			histsvc.Set("HCandidateJetPhi", HCandidateJet.p.Phi())
			histsvc.Set("HCandidateJetM", HCandidateJet.p.M())
			histsvc.Set("HCandidateJetD2", HCandidateJet.Double("D2"))
			histsvc.Set("HCandidateJetTau21", HCandidateJet.Double("Tau21"))
			histsvc.Set("HCandidateJetTau21WTA", HCandidateJet.Double("Tau21WTA"))
			histsvc.Set("HCandidateJetNTrack", HCandidateJet.Double("nTrack"))

			histsvc.Set("VCandidateJetPt", VCandidateJet.p.Pt())
			histsvc.Set("VCandidateJetEta", VCandidateJet.p.Eta())
			histsvc.Set("VCandidateJetPhi", VCandidateJet.p.Phi())
			histsvc.Set("VCandidateJetM", VCandidateJet.p.M())
			histsvc.Set("VCandidateJetD2", VCandidateJet.Double("D2"))
			histsvc.Set("VCandidateJetTau21", VCandidateJet.Double("Tau21"))
			histsvc.Set("VCandidateJetTau21WTA", VCandidateJet.Double("Tau21WTA"))
			histsvc.Set("VCandidateJetNTrack", VCandidateJet.Double("nTrack"))

			histsvc.Set("DiJetDeltaPhi", LeadCaloJet.p.DeltaPhi(SubLeadCaloJet.p))
			histsvc.Set("DiJetDeltaEta", LeadCaloJet.p.Eta() - SubLeadCaloJet.p.Eta())
			histsvc.Set("DiJetDeltaY", LeadCaloJet.p.Rapidity() - SubLeadCaloJet.p.Rapidity())
			histsvc.Set("DiJetDeltaR", LeadCaloJet.p.DeltaR(SubLeadCaloJet.p))
			histsvc.Set("DiJetMass", (LeadCaloJet.p + SubLeadCaloJet.p).M())
			histsvc.Set("DiJetPtAsymm", 1.0*abs(LeadCaloJet.p.Pt() - SubLeadCaloJet.p.Pt())/(LeadCaloJet.p.Pt() + SubLeadCaloJet.p.Pt()))

		#############################
		# Fill Track-Jet Kinematics #
		#############################

		# assign correct object
		LeadTrackJet_VCandidateJet    = None
		SubLeadTrackJet_VCandidateJet = None
		LeadTrackJet_HCandidateJet    = None
		SubLeadTrackJet_HCandidateJet = None

		if VCandidateJet.Objs("AssocTrackJets") >= 1:
			LeadTrackJet_VCandidateJet = VCandidateJet.Obj("AssocTrackJets", 0)
			if VCandidateJet.Objs("AssocTrackJets") >= 2:
				SubLeadTrackJet_VCandidateJet = VCandidateJet.Obj("AssocTrackJets", 1)

		if HCandidateJet.Objs("AssocTrackJets") >= 1:
			LeadTrackJet_HCandidateJet = HCandidateJet.Obj("AssocTrackJets", 0)
			if HCandidateJet.Objs("AssocTrackJets") >= 2:
				SubLeadTrackJet_HCandidateJet = HCandidateJet.Obj("AssocTrackJets", 1)

		# fill all variables
		self.FillTrackJetVars(LeadTrackJet_HCandidateJet,    "LeadTrackJet_HCandidateJet")
		self.FillTrackJetVars(SubLeadTrackJet_HCandidateJet, "SubLeadTrackJet_HCandidateJet")
		self.FillTrackJetVars(LeadTrackJet_VCandidateJet,    "LeadTrackJet_VCandidateJet")
		self.FillTrackJetVars(SubLeadTrackJet_VCandidateJet, "SubLeadTrackJet_VCandidateJet")

		# fill variables between track-jets
		for btagSysName in self._btagSysList:
			hitsvc = self.histsvc[btagSysName]["histsvc"]

			if (LeadTrackJet_HCandidateJet is not None) and (SubLeadTrackJet_HCandidateJet is not None):
				histsvc.Set("dRjj_HCandidateJet", LeadTrackJet_HCandidateJet.p.DeltaR(SubLeadTrackJet_HCandidateJet.p))
			if (LeadTrackJet_VCandidateJet is not None) and (SubLeadTrackJet_VCandidateJet is not None):
				histsvc.Set("dRjj_VCandidateJet", LeadTrackJet_VCandidateJet.p.DeltaR(SubLeadTrackJet_VCandidateJet.p))

		####################################################################################################################

		##########################################
		# Categorize based on H-candidate b-tags #
		##########################################

		nPassBtag = 0
		_EventBtagSF = {}

		for btagSysName in self._btagSysList:
			_EventBtagSF[btagSysName] = 1.

		for TrackJet in HCandidateJet.ObjVec("AssocTrackJets"):
			if self.PassTrackJetBtag(TrackJet, self._TrackJetWP):
				nPassBtag += 1
			for btagSysName in self._btagSysList:
				_EventBtagSF[btagSysName] = _EventBtagSF[btagSysName] * TrackJet.Double("SF"+btagSysName)

		##################
		# Blind the Data #
		##################

		if (not _isMC) and self._doBlindData:
			HMass = HCandidateJet.p.M()

			# define Blinding Region
			BlindRegion = False
			if PassVtagging and (HMass >= self._HiggsMassCut[0]) and (HMass < self._HiggsMassCut[1]):
				if nPassBtag >= 1: 
					BlindRegion = True

				# for 2015, no need to blind 0-tag above 3 TeV
				# elif (HCandidateJet.p + VCandidateJet.p).M() > 3000:
				# 	BlindRegion = True

			if BlindRegion: return

		##############################################
		# Histograms before b-tagging categorization #
		##############################################

		for btagSysName in self._btagSysList:
			histsvc = self.histsvc[btagSysName]['histsvc']
			histsvc.MakeHists("GoodEvent", "_"+VtagString+"_BeforeBTagging")

		###########################
		# Making plots in SR / CR #
		###########################

		# plots here are always categorized in nbtag and VtagString

		for btagSysName in self._btagSysList:
			GlobalSF = _EventBtagSF[btagSysName]
			histsvc = self.histsvc[btagSysName]['histsvc']

			#
			# no Higgs mass cut 
			#

			# cut-flow
			for triggerName in PassedTriggerList: self.MakeTriggerPlotOneSys(tree, btagSysName, triggerName, VtagString+"_HPass%sbtag"%(nPassBtag), _isMC, GlobalSF)
			self.MakeCutflowPlotOneSys(tree, btagSysName, VtagString+"_HPass%sbtag"%(nPassBtag), _isMC, GlobalSF)

			# histograms
			histsvc.MakeHists("GoodEvent", "_"+VtagString+"_HPass%sbtag"%(nPassBtag), GlobalSF)

			#
			# Now Higgs Mass Cut
			#

			HMass = HCandidateJet.p.M()

			if (HMass >= self._HiggsMassCut[0]) and (HMass < self._HiggsMassCut[1]):
				# 
				# b-tagging only
				#

				# cut-flow
				for triggerName in PassedTriggerList: self.MakeTriggerPlotOneSys(tree, btagSysName, triggerName, VtagString+"_HPass%sbtagHiggsMassCut"%(nPassBtag), _isMC, GlobalSF)
				self.MakeCutflowPlotOneSys(tree, btagSysName, VtagString+"_HPass%sbtagHiggsMassCut"%(nPassBtag), _isMC, GlobalSF)

				# check probability of correct assignment
				if PassCorrectVHAssignment:
					for triggerName in PassedTriggerList: self.MakeTriggerPlotOneSys(tree, btagSysName, triggerName, VtagString+"_HPass%sbtagHiggsMassCut__CorrectAssignment"%(nPassBtag), _isMC, GlobalSF)
					self.MakeCutflowPlotOneSys(tree, btagSysName, VtagString+"_HPass%sbtagHiggsMassCut__CorrectAssignment"%(nPassBtag), _isMC, GlobalSF)

				# histograms
				histsvc.MakeHists("GoodEvent", "_"+VtagString+"_HPass%sbtagHiggsMassCut"%(nPassBtag), GlobalSF)

				#
				# plus VHambiguity category now
				#

				# cut-flow
				for triggerName in PassedTriggerList: self.MakeTriggerPlotOneSys(tree, btagSysName, triggerName, VtagString+"_HPass%s%sbtagHiggsMassCut"%(nPassBtag, VHAmbiguityCategory), _isMC, GlobalSF)
				self.MakeCutflowPlotOneSys(tree, btagSysName, VtagString+"_HPass%s%sbtagHiggsMassCut"%(nPassBtag, VHAmbiguityCategory), _isMC, GlobalSF)

				# check probability of correct assignment
				if PassCorrectVHAssignment:
					for triggerName in PassedTriggerList: self.MakeTriggerPlotOneSys(tree, btagSysName, triggerName, VtagString+"_HPass%s%sbtagHiggsMassCut__CorrectAssignment"%(nPassBtag, VHAmbiguityCategory), _isMC, GlobalSF)
					self.MakeCutflowPlotOneSys(tree, btagSysName, VtagString+"_HPass%s%sbtagHiggsMassCut__CorrectAssignment"%(nPassBtag, VHAmbiguityCategory), _isMC, GlobalSF)

				# histograms
				histsvc.MakeHists("GoodEvent", "_"+VtagString+"_HPass%s%sbtagHiggsMassCut"%(nPassBtag, VHAmbiguityCategory), GlobalSF)


		####################
		# Fill Ntuple Here #
		####################

		# get SF list
		SFList = ROOT.vector(ROOT.Double)()
		SFNameList = ROOT.vector(ROOT.string)()
		for btagSysName in self._btagSysList:
			SFList.push_back(_EventBtagSF[btagSysName])
			SFNameList.push_back(btagSysName)

		for btagSysName in self._btagSysList:
			# save memory #
			if self._optSaveTreeAt not in ["ALL", btagSysName]:
				continue

			# histsvc for data retrieving #
			histsvc = self.histsvc[btagSysName]['histsvc']

			# ntuplesvc_tinytree #
			if self._optTinyTree:
				ntuplesvc_tinytree = self.histsvc[btagSysName]['ntuplesvc_tinytree']

				# add selection here, if needed
				PassNtupleCut = True

				if PassNtupleCut:
					ntuplesvc_tinytree.SetEventValue("RunNumber", tree.runNumber)
					ntuplesvc_tinytree.SetEventValue("EventNumber", tree.eventNumber)
					ntuplesvc_tinytree.SetEventValue("EventWeight", self._EvtWeight[0])

					# Event Level #
					ntuplesvc_tinytree.SetEventValue("nPassBtag", nPassBtag)
					ntuplesvc_tinytree.SetEventValue("VHAmbiguityCategory", VHAmbiguityCategory)
					ntuplesvc_tinytree.SetEventValue("PassVtagging", PassVtagging)
					ntuplesvc_tinytree.SetEventValue("AntiVtaggingCR", AntiVtaggingCR)

					if _isMC:
						ntuplesvc_tinytree.SetEventValue("ChannelNumber", tree.mcChannelNumber)
					else:
						ntuplesvc_tinytree.SetEventValue("ChannelNumber", 0)

					ntuplesvc_tinytree.SetEventValue("DiJetMass", histsvc.Get("DiJetMass"))
					ntuplesvc_tinytree.SetEventValue("DiJetDeltaR", histsvc.Get("DiJetDeltaR"))
					ntuplesvc_tinytree.SetEventValue("DiJetDeltaPhi", histsvc.Get("DiJetDeltaPhi"))
					ntuplesvc_tinytree.SetEventValue("DiJetDeltaEta", histsvc.Get("DiJetDeltaEta"))
					ntuplesvc_tinytree.SetEventValue("DiJetDeltaY", histsvc.Get("DiJetDeltaY"))
					ntuplesvc_tinytree.SetEventValue("DiJetPtAsymm", histsvc.Get("DiJetPtAsymm"))

					ntuplesvc_tinytree.SetEventValue("HCandidateJetPt", histsvc.Get("HCandidateJetPt"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetEta", histsvc.Get("HCandidateJetEta"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetPhi", histsvc.Get("HCandidateJetPhi"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetM", histsvc.Get("HCandidateJetM"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetD2", histsvc.Get("HCandidateJetD2"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetTau21", histsvc.Get("HCandidateJetTau21"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetTau21WTA", histsvc.Get("HCandidateJetTau21WTA"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetNTrack", histsvc.Get("HCandidateJetNTrack"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetIsVtagged", HCandidateJet.Double("WZTagged"))
					ntuplesvc_tinytree.SetEventValue("HCandidateJetNTrackJet", HCandidateJet.Double("nTrackJet"))

					ntuplesvc_tinytree.SetEventValue("VCandidateJetPt", histsvc.Get("VCandidateJetPt"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetEta", histsvc.Get("VCandidateJetEta"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetPhi", histsvc.Get("VCandidateJetPhi"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetM", histsvc.Get("VCandidateJetM"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetD2", histsvc.Get("VCandidateJetD2"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetTau21", histsvc.Get("VCandidateJetTau21"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetTau21WTA", histsvc.Get("VCandidateJetTau21WTA"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetNTrack", histsvc.Get("VCandidateJetNTrack"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetIsVtagged", VCandidateJet.Double("WZTagged"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetWtagCode", VCandidateJet.Double("WtagCode"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetZtagCode", VCandidateJet.Double("ZtagCode"))
					ntuplesvc_tinytree.SetEventValue("VCandidateJetNTrackJet", VCandidateJet.Double("nTrackJet"))

					ntuplesvc_tinytree.SetEventValue("dRjj_HCandidateJet", histsvc.Get("dRjj_HCandidateJet", -100, True))
					ntuplesvc_tinytree.SetEventValue("dRjj_VCandidateJet", histsvc.Get("dRjj_VCandidateJet", -100, True))

					ntuplesvc_tinytree.SetEventValue("LeadTrackJet_HCandidateJet_Pt", histsvc.Get("LeadTrackJet_HCandidateJet_Pt", -100, True))
					ntuplesvc_tinytree.SetEventValue("SubLeadTrackJet_HCandidateJet_Pt", histsvc.Get("SubLeadTrackJet_HCandidateJet_Pt", -100, True))
					ntuplesvc_tinytree.SetEventValue("LeadTrackJet_VCandidateJet_Pt", histsvc.Get("LeadTrackJet_VCandidateJet_Pt", -100, True))
					ntuplesvc_tinytree.SetEventValue("SubLeadTrackJet_VCandidateJet_Pt", histsvc.Get("SubLeadTrackJet_VCandidateJet_Pt", -100, True))

					ntuplesvc_tinytree.SetEventValue("LeadTrackJet_HCandidateJet_Eta", histsvc.Get("LeadTrackJet_HCandidateJet_Eta", -100, True))
					ntuplesvc_tinytree.SetEventValue("SubLeadTrackJet_HCandidateJet_Eta", histsvc.Get("SubLeadTrackJet_HCandidateJet_Eta", -100, True))
					ntuplesvc_tinytree.SetEventValue("LeadTrackJet_VCandidateJet_Eta", histsvc.Get("LeadTrackJet_VCandidateJet_Eta", -100, True))
					ntuplesvc_tinytree.SetEventValue("SubLeadTrackJet_VCandidateJet_Eta", histsvc.Get("SubLeadTrackJet_VCandidateJet_Eta", -100, True))

					ntuplesvc_tinytree.SetEventValue("LeadTrackJet_HCandidateJet_MV2c10", histsvc.Get("LeadTrackJet_HCandidateJet_MV2c10", -100, True))
					ntuplesvc_tinytree.SetEventValue("SubLeadTrackJet_HCandidateJet_MV2c10", histsvc.Get("SubLeadTrackJet_HCandidateJet_MV2c10", -100, True))
					ntuplesvc_tinytree.SetEventValue("LeadTrackJet_VCandidateJet_MV2c10", histsvc.Get("LeadTrackJet_VCandidateJet_MV2c10", -100, True))
					ntuplesvc_tinytree.SetEventValue("SubLeadTrackJet_VCandidateJet_MV2c10", histsvc.Get("SubLeadTrackJet_VCandidateJet_MV2c10", -100, True))

					# Obj Level # (SF info)
					ntuplesvc_tinytree.SetObjValue("SFList", SFList)
					ntuplesvc_tinytree.SetObjValue("SFNameList", SFNameList)

					ntuplesvc_tinytree.AutoFill()


	######################################################################
	# Below is utility region
	######################################################################

	def GetXsecWeight(self, tree):
		if self._ApplyXsecWeight:
			# first-time loading
			if self._XsecConfigObj == None:
				self._XsecConfigObj = ROOT.TEnv(self._XsectionConfig)

				if self._XsecConfigObj == None:
					print ': ERROR! Cannot open Xsec configuration file',self._XsectionConfig
					sys.exit(0)
			
			mcChannelNumber = tree.mcChannelNumber

			if not self._XsecConfigObj.Defined("xsec_%i" % (mcChannelNumber)):
				print "WARNING! DSID %i not defined in config file" % (mcChannelNumber)
			
			xsec = self._XsecConfigObj.GetValue("xsec_%i" % (mcChannelNumber), 1.)
			eff  = self._XsecConfigObj.GetValue("eff_%i" % (mcChannelNumber), 1.)
			k    = self._XsecConfigObj.GetValue("k_%i" % (mcChannelNumber), 1.)
			n    = self._XsecConfigObj.GetValue("n_%i" % (mcChannelNumber), 1.)

			return 1.0*self._Lumi*xsec*k*eff/n

		else:
			return 1.

	def MakeTriggerPlot(self, tree, triggerName, cutName, isMC, extraWeight=1.0):
		for btagSysName in self._btagSysList:
			self.MakeTriggerPlotOneSys(tree, btagSysName, triggerName, cutName, isMC, extraWeight)

	def MakeTriggerPlotOneSys(self, tree, btagSysName, triggerName, cutName, isMC, extraWeight=1.0):
		histsvc = self.histsvc[btagSysName]['histsvc']
		if isMC:
			histsvc.AutoFill("GoodEvent", "_TriggerStudy", "ChannelNumber_%s__%s" % (cutName, triggerName), self._ChannelNumberDict[tree.mcChannelNumber], self._EvtWeight[0]*extraWeight, len(self._ChannelNumberList)+1, -1.5, len(self._ChannelNumberList)-0.5)


	def MakeCutflowPlot(self, tree, cutName, isMC, extraWeight=1.0):
		for btagSysName in self._btagSysList:
			self.MakeCutflowPlotOneSys(tree, btagSysName, cutName, isMC, extraWeight)

	def MakeCutflowPlotOneSys(self, tree, btagSysName, cutName, isMC, extraWeight):
		histsvc = self.histsvc[btagSysName]['histsvc']

		histsvc.AutoFill("GoodEvent", "_Cutflow", "CountEntry_%s" % (cutName), 1, 1., 1, 0.5, 1.5) 
		histsvc.AutoFill("GoodEvent", "_Cutflow", "CountWeight_%s" % (cutName), 1, self._EvtWeight[0]*extraWeight, 1, 0.5, 1.5)

		if isMC: 
			# by default only record cut-flow of RSG_c10
			histsvc.AutoFill("GoodEvent", "_Cutflow", "ChannelNumber_CountEntry_%s" % (cutName), self._ChannelNumberDict[tree.mcChannelNumber], 1, len(self._ChannelNumberList)+1, -1.5, len(self._ChannelNumberList)-0.5)
			histsvc.AutoFill("GoodEvent", "_Cutflow", "ChannelNumber_CountWeight_%s" % (cutName), self._ChannelNumberDict[tree.mcChannelNumber], self._EvtWeight[0]*extraWeight, len(self._ChannelNumberList)+1, -1.5, len(self._ChannelNumberList)-0.5)

	
	def FillOneVarForAllSignal(self, tree, isMC, folderName, histNamePrefix, *histsvcOptions):
		for btagSysName in self._btagSysList:
			histsvc = self.histsvc[btagSysName]['histsvc']

			histNameAppendix = ("_"+str(tree.mcChannelNumber) if isMC else "")
			histsvc.AutoFill("GoodEvent", "_"+folderName, histNamePrefix + histNameAppendix, *histsvcOptions)

	def FillTrackJetVars(self, TrackJet, TrackJetName):
		for btagSysName in self._btagSysList:
			histsvc = self.histsvc[btagSysName]['histsvc']

			if TrackJet is None:
				return
			else:
				histsvc.Set(TrackJetName + "_Pt", TrackJet.p.Pt())
				histsvc.Set(TrackJetName + "_Eta", TrackJet.p.Eta())
				histsvc.Set(TrackJetName + "_Phi", TrackJet.p.Phi())
				histsvc.Set(TrackJetName + "_M", TrackJet.p.M())
				histsvc.Set(TrackJetName + "_E", TrackJet.p.E())
				histsvc.Set(TrackJetName + "_MV2c10", TrackJet.Double("MV2c10"))

	def PassMuonQualityCut(self, tree, iMuon):
		# muon quality branches are stored exclusively!
		if self._MuonQualityCut == "Tight":
			return tree.muon_isTight[iMuon] == 1
		elif self._MuonQualityCut == "Medium":
			return (tree.muon_isMedium[iMuon] == 1) or (tree.muon_isTight[iMuon] == 1)
		elif self._MuonQualityCut == "Loose":
			return (tree.muon_isLoose[iMuon] == 1) or (tree.muon_isMedium[iMuon] == 1) or (tree.muon_isTight[iMuon] == 1)
		else:
			print "Unrecognized muon quality cut",self._MuonQualityCut
			return False

	def PassTrackJetBtag(self, TrackJet, WP):
		btagAlg, bEff = WP.split("_")

		if btagAlg == "2D":
			MV2c00Cut, MV2c100Cut = self._BtagCutDict[WP]
			return (TrackJet.Double("MV2c00") >= MV2c00Cut) and (TrackJet.Double("MV2c100") >= MV2c100Cut)
		else:
			return TrackJet.Double(btagAlg) >= self._BtagCutDict[WP]

	def MttStitch(self, tree):
		mtt = tree.truth_mtt/1000.   # MeV -> GeV
		channelNumber = tree.mcChannelNumber

		if (channelNumber == 410007) or (channelNumber == 410000):
			# inclusive ttbar
			return mtt < self._MttStitchCut
		else:
			# other channels, including boosted mtt slices and irrlevant channels

			# for allhad/nonallhad mtt slices, a scale-factor needs to be applied for stitching purpose
			if (channelNumber >= 303722) and (channelNumber <= 303726):  # allhad
				self._EvtWeight[0] *= self._MttScale_allhad
			elif (channelNumber >= 301528) and (channelNumber <= 301532):  # nonallhad
				self._EvtWeight[0] *= self._MttScale_nonallhad

			return True

	# CaloJetList should be a list of (index, calojet) where index is the index in tree structure
	def MakeJERPlots(self, tree, CaloJetList, CutName):
		for btagSysName in self._btagSysList:
			histsvc = self.histsvc[btagSysName]['histsvc']

			for iCaloJet, CaloJet in CaloJetList:
				TruthMatched = tree.truth_hcand_boosted_match[iCaloJet]

				histsvc.AutoFill("GoodEvent", "_JERStudy", "CaloJetPt_CaloJetTruthMatch__"+CutName, CaloJet.p.Pt(), TruthMatched, self._EvtWeight[0], 40, 0, 2000, 2, -0.5, 1.5)

				if TruthMatched:
					MatchedTruthJet = ROOT.TLorentzVector()
					MatchedTruthJet.SetPtEtaPhiM(tree.truth_hcand_boosted_pt[iCaloJet]/1000., tree.truth_hcand_boosted_eta[iCaloJet], tree.truth_hcand_boosted_phi[iCaloJet], tree.truth_hcand_boosted_m[iCaloJet]/1000.)
					MatchedTruthJetD2 = tree.truth_hcand_boosted_d2[iCaloJet]

					# Inclusive mass bin
					histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetPtResponse__"+CutName, MatchedTruthJet.Pt(), (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
					if MatchedTruthJet.E() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetEResponse__"+CutName, MatchedTruthJet.Pt(), (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
					if MatchedTruthJet.M() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetMResponse__"+CutName, MatchedTruthJet.Pt(), (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
					if MatchedTruthJetD2 > 0   :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetD2Response__"+CutName, MatchedTruthJet.Pt(), (CaloJet.Double("D2"))/(MatchedTruthJetD2), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)

					TruthMass = MatchedTruthJet.M()
					if TruthMass < 50:
						MassBin = "M0"
					elif TruthMass < 100:
						MassBin = "M1"
					elif TruthMass < 150:
						MassBin = "M2"
					else:
						MassBin = "M3"

					# Exclusive mass bin
					histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetPtResponse_%s__%s" % (MassBin, CutName), MatchedTruthJet.Pt(), (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
					if MatchedTruthJet.E() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetEResponse_%s__%s" % (MassBin, CutName), MatchedTruthJet.Pt(), (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
					if MatchedTruthJet.M() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetMResponse_%s__%s" % (MassBin, CutName), MatchedTruthJet.Pt(), (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
					if MatchedTruthJetD2 > 0   :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetD2Response_%s__%s" % (MassBin, CutName), MatchedTruthJet.Pt(), (CaloJet.Double("D2"))/(MatchedTruthJetD2), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)

	# measure the response as function of m/pT, in bins of pT
	def MakeJERPlots2(self, tree, CaloJetList, CutName):
		for btagSysName in self._btagSysList:
			histsvc = self.histsvc[btagSysName]['histsvc']

			for iCaloJet, CaloJet in CaloJetList:
				TruthMatched = tree.truth_hcand_boosted_match[iCaloJet]

				if TruthMatched:
					MatchedTruthJet = ROOT.TLorentzVector()
					MatchedTruthJet.SetPtEtaPhiM(tree.truth_hcand_boosted_pt[iCaloJet]/1000., tree.truth_hcand_boosted_eta[iCaloJet], tree.truth_hcand_boosted_phi[iCaloJet], tree.truth_hcand_boosted_m[iCaloJet]/1000.)
					MatchedTruthJetD2 = tree.truth_hcand_boosted_d2[iCaloJet]

					TruthBoost = MatchedTruthJet.M()/MatchedTruthJet.Pt()

					# Inclusive pt bin
					histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetPtResponse__"+CutName, TruthBoost, (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
					if MatchedTruthJet.E() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetEResponse__"+CutName, TruthBoost, (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
					if MatchedTruthJet.M() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetMResponse__"+CutName, TruthBoost, (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
					if MatchedTruthJetD2 > 0   :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetD2Response__"+CutName, TruthBoost, (CaloJet.Double("D2"))/(MatchedTruthJetD2), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)

					TruthMass = MatchedTruthJet.M()
					if TruthMass < 50:
						MassBin = "M0"
					elif TruthMass < 100:
						MassBin = "M1"
					elif TruthMass < 150:
						MassBin = "M2"
					else:
						MassBin = "M3"

					# Exclusive pt bin
					histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetPtResponse_%s__%s" % (MassBin, CutName), TruthBoost, (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
					if MatchedTruthJet.E() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetEResponse_%s__%s" % (MassBin, CutName), TruthBoost, (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
					if MatchedTruthJet.M() > 0 :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetMResponse_%s__%s" % (MassBin, CutName), TruthBoost, (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
					if MatchedTruthJetD2 > 0   :  histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetD2Response_%s__%s" % (MassBin, CutName), TruthBoost, (CaloJet.Double("D2"))/(MatchedTruthJetD2), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)

	# emulate the Higgs tagging
	# Make sure one has already done the muon association to track-jets from calo-jet
	# also make sure you do not apply any change on CaloJet here! (i.e. only accessing information, not writing in any information)
	def HiggsTagging(self, CaloJet, Muons, MassWindow, doBtag):
		# at least 1-btags
		PassBtag = True
		if doBtag:
			BtaggedTrackJets = [ TrackJet for TrackJet in CaloJet.ObjVec("AssocTrackJets") if self.PassTrackJetBtag(TrackJet, self._TrackJetWP) ]
			nbtag = len(BtaggedTrackJets)
			PassBtag = (PassBtag and (nbtag >= 1)) 

		# muon corrected 4-momentum 
		sumMuonCorr = ROOT.TLorentzVector()
		for TrackJet in CaloJet.ObjVec("AssocTrackJets"):
			if TrackJet.Exists("MuonAssocIndex"):
				sumMuonCorr += (Muons[TrackJet.Int("MuonAssocIndex")].p)
		MuonCorrected4p = CaloJet.p + sumMuonCorr

		# mass cut
		CorrectedMass = MuonCorrected4p.M()
		PassMassWindow = ( (CorrectedMass >= MassWindow[0]) and (CorrectedMass < MassWindow[1]) )

		# store it
		CaloJet.Set("MuonCorrectedMassIfHiggs", CorrectedMass)

		return (PassBtag and PassMassWindow)

	def MCTriggerEmulation(self, tree):
		# reference trigger
		if "HLT_j300_a10_lcw_sub_L1J75" not in tree.passedTriggers:
			return False

		# at least one large-R jet
		if tree.hcand_boosted_n < 1:
			return False

		# pass 420 GeV (in principle this should be the untrimmed large-R jet ... but whatever ...)
		if tree.hcand_boosted_pt[0]/1000. < 420.:
			return False

		# OK
		return True














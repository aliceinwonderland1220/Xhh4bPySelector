import os
import ROOT
import utils
import PySelectorBase
import array
import sys
from collections import defaultdict

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

print "Finish loading libraries!"

class miniNtupleProcessor(PySelectorBase.PySelectorBase):
	def Setup(self):
		####################
		# selector options #
		####################

		self.histfile = os.environ['Xhh4bPySelector_dir']+"/miniNtupleProcessor/output/test.root"       # use absolute path, and all output will be put under output folder
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

		###################
		# physics options #
		###################

		self._MV2c20CutDict = {
			"70": -0.3098,
			"77": -0.6134,
			"85": -0.8433,
		}

		self._TriggerList = ["HLT_j70_btight_3j70", "HLT_j100_2j55_bmedium", "HLT_ht700", "HLT_4j85", "HLT_j360"]   # list of triggers to be combined in OR
		self._doTriggerCut = True

		self._TrackJetPtCut = 10.
		self._TrackJetEtaCut = 2.5
		self._TrackJetWP = ["70", "77", "85"]    # list of WP to consider

		self._ApplyXsecWeight = True
		self._XsectionConfig = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-01-03_Xsection.config"

		self._GRLXml = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/data15_13TeV.periodAllYear_DetStatus-v70-pro19-04_DQDefects-00-01-02_PHYS_StandardGRL_All_Good_25ns.xml"
		self._Lumi = 1.41126        # unit to be compatible with Xsection.config
		                            # Number for hh4b-v00-v01-03

		self._ForceDataMC = None     # Force to run in either "Data" or "MC". This should be set as None most of the time.

		#
		# PRW

		self._doPRW = False
		self._PRWConfigFile = ""
		self._PRWLumiCalcFile = ""

		#####################
		## Private Objects ##
		#####################

		self._XsecConfigObj = None

	def BookHistograms(self):

		#############################
		# Initialize the histograms #
		#############################

		self.histsvc = ROOT.Analysis_AutoHists(self.outputfile)

		self._EvtWeight = array.array('d', [1.])

		self.histsvc.Book("ChannelNumber_DiJetMass", "ChannelNumber", "DiJetMass", self._EvtWeight, 21, 301486.5, 301507.5, 50, 0, 5000)

		self.histsvc.Book("LeadCaloJetPt", "LeadCaloJetPt", self._EvtWeight, 12, 300, 900)
		self.histsvc.Book("LeadCaloJetEta", "LeadCaloJetEta", self._EvtWeight, 25, -2.5, 2.5)
		self.histsvc.Book("LeadCaloJetPhi", "LeadCaloJetPhi", self._EvtWeight, 35, -3.5, 3.5)
		self.histsvc.Book("LeadCaloJetM", "LeadCaloJetM", self._EvtWeight, 100, 0, 1000)

		self.histsvc.Book("SubLeadCaloJetPt", "SubLeadCaloJetPt", self._EvtWeight, 12, 300, 900)
		self.histsvc.Book("SubLeadCaloJetEta", "SubLeadCaloJetEta", self._EvtWeight, 25, -2.5, 2.5)
		self.histsvc.Book("SubLeadCaloJetPhi", "SubLeadCaloJetPhi", self._EvtWeight, 35, -3.5, 3.5)
		self.histsvc.Book("SubLeadCaloJetM", "SubLeadCaloJetM", self._EvtWeight, 100, 0, 1000)

		self.histsvc.Book("LeadCaloJetM_SubLeadCaloJetM", "LeadCaloJetM", "SubLeadCaloJetM", self._EvtWeight, 20, 0, 1000, 20, 0, 1000)

		self.histsvc.Book("DiJetDeltaPhi", "DiJetDeltaPhi", self._EvtWeight, 35, 0, 3.5)
		#self.histsvc.Book("DiJetMass", "DiJetMass", self._EvtWeight, 50, 0, 5000)
		self.histsvc.Book("DiJetMass", "DiJetMass", self._EvtWeight, 100, 0, 5000)

		self.TrackJetNameList = [
		                         "LeadTrackJet_LeadCaloJet",
		                         "SubLeadTrackJet_LeadCaloJet",
		                         "LeadTrackJet_SubLeadCaloJet",
		                         "SubLeadTrackJet_SubLeadCaloJet",
		                        ]

		for TrackJetName in self.TrackJetNameList:
			self.histsvc.Book(TrackJetName + "_Pt", TrackJetName + "_Pt", self._EvtWeight, 10, 0, 500)
			self.histsvc.Book(TrackJetName + "_Eta", TrackJetName + "_Eta", self._EvtWeight, 25, -2.5, 2.5)
			self.histsvc.Book(TrackJetName + "_Phi", TrackJetName + "_Phi", self._EvtWeight, 35, -3.5, 3.5)
			self.histsvc.Book(TrackJetName + "_M", TrackJetName + "_M", self._EvtWeight, 20, 0, 1000)
			self.histsvc.Book(TrackJetName + "_E", TrackJetName + "_E", self._EvtWeight, 20, 0, 1000)
			self.histsvc.Book(TrackJetName + "_MV2c20", TrackJetName + "_MV2c20", self._EvtWeight, 220, -1.1, 1.1)

		###############################
		# Initialize other tools here #
		###############################

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

		self.counter = 0

	def ProcessEntry(self, tree, entry):

		self.counter += 1

		#######################################
		# reset hist service at the beginning #
		#######################################

		self.histsvc.Reset()

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

		# We care about number of events before any cut ONLY IN MC
		# in Data, just skim through it!
		if not _isMC:
			if not self.QuickSkimming(tree): return

		####################
		# Deal with weghts #
		####################

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

		if _isMC: self.histsvc.Set("ChannelNumber", tree.mcChannelNumber)

		############
		# Triggers #
		############

		PassedTriggerList = list(set(tree.passedTriggers).intersection(set(self._TriggerList)))
		if len(PassedTriggerList) > 0: 
			PassedTriggerList.append("OR")
		PassedTriggerList.append("All")

		##################
		# Quick Skimming #
		##################

		# For MC, this is before any cut (including skimming)
		# For data, this is after skimming, before anything
		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "Initial", _isMC)
		self.MakeCutflowPlot(tree, "Initial", _isMC)

		if not self.QuickSkimming(tree): return

		#########################################################
		# From now on -- leadJet > 350GeV, subleadJet > 250 GeV #
		#########################################################

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassBoostSkim", _isMC)
		self.MakeCutflowPlot(tree, "PassBoostSkim", _isMC)

		#################################################
		# Things to do at the beginning (GRL, PRW etc.) #
		#################################################
		# PRW is moved to the beginning

		#
		# GRL
		#

		if not _isMC:
			if self.GRL is None:
				print "WARNING! GRL not setup for Data!"
			else:
				if not self.GRL.HasRunLumiBlock(tree.runNumber, tree.lumiBlock):
					return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassGRL", _isMC)
		self.MakeCutflowPlot(tree, "PassGRL", _isMC)

		##
		## Trigger Cut
		##

		if self._doTriggerCut:
			if "OR" not in PassedTriggerList:
				return

		self.MakeCutflowPlot(tree, "PassTrigger", _isMC)

		#####################
		# Calo-jet Business #
		#####################

		##
		## calo-jets Reconstruction
		##

		LeadCaloJet = ROOT.TLorentzVector()
		LeadCaloJet.SetPtEtaPhiM(tree.hcand_boosted_pt[0]/1000., tree.hcand_boosted_eta[0], tree.hcand_boosted_phi[0], tree.hcand_boosted_m[0]/1000.)
		LeadCaloJet = ROOT.Particle(LeadCaloJet)

		SubLeadCaloJet = ROOT.TLorentzVector()
		SubLeadCaloJet.SetPtEtaPhiM(tree.hcand_boosted_pt[1]/1000., tree.hcand_boosted_eta[1], tree.hcand_boosted_phi[1], tree.hcand_boosted_m[1]/1000.)
		SubLeadCaloJet = ROOT.Particle(SubLeadCaloJet)

		self.histsvc.Set("LeadCaloJetPt", LeadCaloJet.p.Pt())
		self.histsvc.Set("LeadCaloJetEta", LeadCaloJet.p.Eta())
		self.histsvc.Set("LeadCaloJetPhi", LeadCaloJet.p.Phi())
		self.histsvc.Set("LeadCaloJetM", LeadCaloJet.p.M())

		self.histsvc.Set("SubLeadCaloJetPt", SubLeadCaloJet.p.Pt())
		self.histsvc.Set("SubLeadCaloJetEta", SubLeadCaloJet.p.Eta())
		self.histsvc.Set("SubLeadCaloJetPhi", SubLeadCaloJet.p.Phi())
		self.histsvc.Set("SubLeadCaloJetM", SubLeadCaloJet.p.M())

		self.histsvc.Set("DiJetDeltaPhi", LeadCaloJet.p.DeltaPhi(SubLeadCaloJet.p))
		self.histsvc.Set("DiJetMass", (LeadCaloJet.p + SubLeadCaloJet.p).M())

		##
		## calo-jet dEta cuts
		## 

		PassdEtaCut = (abs(LeadCaloJet.p.Eta() - SubLeadCaloJet.p.Eta()) < 1.7)

		if not PassdEtaCut:
			return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassdEtaCut", _isMC)
		self.MakeCutflowPlot(tree, "PassdEtaCut", _isMC)

		# #####################################################
		# # Reference Histogram with Standard Cuts in N-tuple #
		# #####################################################

		# if tree.Pass4Btag:
		# 	if tree.PassSignalMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass4b70_SRMass")
		# 	if tree.PassControlMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass4b70_CRMass")
		# 	if tree.PassSidebandMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass4b70_SBMass")
		# if tree.Pass3Btag or tree.Pass2Btag:
		# 	if tree.PassSignalMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass2b3b70_SRMass")
		# 	if tree.PassControlMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass2b3b70_CRMass")
		# 	if tree.PassSidebandMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass2b3b70_SBMass")
		# if tree.Pass3Btag or tree.Pass4Btag:
		# 	if tree.PassSignalMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass3b4b70_SRMass")
		# 	if tree.PassControlMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass3b4b70_CRMass")
		# 	if tree.PassSidebandMass:
		# 		self.histsvc.MakeHists("GoodEvent", "_CrossCheckPass3b4b70_SBMass")

		###############
		# mass region #
		###############

		MassRegion = self.GetDiJetMassWindow(LeadCaloJet, SubLeadCaloJet)
		PassSRMass = (MassRegion == 0)
		PassCRMass = (MassRegion == 1)
		PassSBMass = (MassRegion == 2)

		# no b-tags, no track-jet multiplicity requirement
		if PassSBMass:
			self.MakeCutflowPlot(tree, "PassdEtaCutPassSBMass", _isMC)
		if PassCRMass:
			self.MakeCutflowPlot(tree, "PassdEtaCutPassCRMass", _isMC)
		if PassSRMass:
			self.MakeCutflowPlot(tree, "PassdEtaCutPassSRMass", _isMC)

		############################
		# Track-jet Reconstruction #
		############################

		# INFO: Starting from hh4b-v00-v01-01, track-jet selection has already been applied when producing miniNtuple. So it becomes redundant to do it here

		AssocTrackJets_LeadCaloJet = []
		for iTrackJet in range(tree.jet_ak2track_asso_pt[0].size()):
			TrackJet = ROOT.TLorentzVector()
			TrackJet.SetPtEtaPhiM(tree.jet_ak2track_asso_pt[0][iTrackJet]/1000., tree.jet_ak2track_asso_eta[0][iTrackJet], tree.jet_ak2track_asso_phi[0][iTrackJet], tree.jet_ak2track_asso_m[0][iTrackJet]/1000.)

			if TrackJet.Pt() < self._TrackJetPtCut: continue
			if abs(TrackJet.Eta()) > self._TrackJetEtaCut: continue

			TrackJet = ROOT.Particle(TrackJet)
			TrackJet.Set(ROOT.MomKey("MV2c20"), tree.jet_ak2track_asso_MV2c20[0][iTrackJet])

			AssocTrackJets_LeadCaloJet.append( TrackJet )

		AssocTrackJets_SubLeadCaloJet = []
		for iTrackJet in range(tree.jet_ak2track_asso_pt[1].size()):
			TrackJet = ROOT.TLorentzVector()
			TrackJet.SetPtEtaPhiM(tree.jet_ak2track_asso_pt[1][iTrackJet]/1000., tree.jet_ak2track_asso_eta[1][iTrackJet], tree.jet_ak2track_asso_phi[1][iTrackJet], tree.jet_ak2track_asso_m[1][iTrackJet]/1000.)

			if TrackJet.Pt() < self._TrackJetPtCut: continue
			if abs(TrackJet.Eta()) > self._TrackJetEtaCut: continue

			TrackJet = ROOT.Particle(TrackJet)
			TrackJet.Set(ROOT.MomKey("MV2c20"), tree.jet_ak2track_asso_MV2c20[1][iTrackJet])

			AssocTrackJets_SubLeadCaloJet.append( TrackJet )

		##
		## Track-jet multiplicity
		##

		TrackJetMultiPattern = [ len(AssocTrackJets_LeadCaloJet), len(AssocTrackJets_SubLeadCaloJet) ]

		Pass4GoodTrackJet = ((TrackJetMultiPattern[0] >= 2) and (TrackJetMultiPattern[1] >= 2))
		Pass3GoodTrackJet = ( ( (TrackJetMultiPattern[0] >= 2) and (TrackJetMultiPattern[1] == 1) ) or ( (TrackJetMultiPattern[0] == 1) and (TrackJetMultiPattern[1] >= 2) ) )

		if (not Pass4GoodTrackJet) and (not Pass3GoodTrackJet):
			return

		# just an alert here ... 
		if Pass4GoodTrackJet and Pass3GoodTrackJet:
			print "ERROR! Pass4GoodTrackJet and Pass3GoodTrackJet should be exclusive to each other!"
			sys.exit()
			return

		if Pass4GoodTrackJet:
			for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "Pass4GoodTrackJet", _isMC)
			self.MakeCutflowPlot(tree, "Pass4GoodTrackJet", _isMC)
		if Pass3GoodTrackJet:
			for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "Pass3GoodTrackJet", _isMC)
			self.MakeCutflowPlot(tree, "Pass3GoodTrackJet", _isMC)

		AssocTrackJets = [ AssocTrackJets_LeadCaloJet, AssocTrackJets_SubLeadCaloJet ]

		# assign correct object
		LeadTrackJet_LeadCaloJet       = AssocTrackJets[0][0]
		SubLeadTrackJet_LeadCaloJet    = (AssocTrackJets[0][1] if len(AssocTrackJets[0]) >= 2 else None)
		LeadTrackJet_SubLeadCaloJet    = AssocTrackJets[1][0]
		SubLeadTrackJet_SubLeadCaloJet = (AssocTrackJets[1][1] if len(AssocTrackJets[1]) >= 2 else None)

		# fill all variables
		self.FillTrackJetVars(LeadTrackJet_LeadCaloJet, "LeadTrackJet_LeadCaloJet")
		self.FillTrackJetVars(SubLeadTrackJet_LeadCaloJet, "SubLeadTrackJet_LeadCaloJet")
		self.FillTrackJetVars(LeadTrackJet_SubLeadCaloJet, "LeadTrackJet_SubLeadCaloJet")
		self.FillTrackJetVars(SubLeadTrackJet_SubLeadCaloJet, "SubLeadTrackJet_SubLeadCaloJet")

		# no b-tags, but with track-jet multiplicity requirement
		if Pass4GoodTrackJet:
			if PassSBMass:
				self.MakeCutflowPlot(tree, "Pass4GoodTrackJetPassSBMass", _isMC)
			if PassCRMass:
				self.MakeCutflowPlot(tree, "Pass4GoodTrackJetPassCRMass", _isMC)
			if PassSRMass:
				self.MakeCutflowPlot(tree, "Pass4GoodTrackJetPassSRMass", _isMC)
		if Pass3GoodTrackJet:
			if PassSBMass:
				self.MakeCutflowPlot(tree, "Pass3GoodTrackJetPassSBMass", _isMC)
			if PassCRMass:
				self.MakeCutflowPlot(tree, "Pass3GoodTrackJetPassCRMass", _isMC)
			if PassSRMass:
				self.MakeCutflowPlot(tree, "Pass3GoodTrackJetPassSRMass", _isMC)

		###########################
		# Now we play with b-tags #
		###########################

		numbtrackjet_WP = defaultdict(lambda: 0)
		numbtrackjet_WP_detail = defaultdict(lambda: [0,0])

		for iCaloJet in range(2):
			for iTrackJet in range( min(2, len(AssocTrackJets[iCaloJet])) ):
				TrackJet = AssocTrackJets[iCaloJet][iTrackJet]
				MV2c20 = TrackJet.Double(ROOT.MomKey("MV2c20"))

				for WP in self._TrackJetWP:
					if MV2c20 > self._MV2c20CutDict[WP]:
						numbtrackjet_WP[WP] += 1
						numbtrackjet_WP_detail[WP][iCaloJet] += 1

		# when we say nbtags == 2, we require they should be at the same side, otherwise, nbtags will be set as 211
		for WP in self._TrackJetWP:
			if numbtrackjet_WP[WP] == 2:
				if (numbtrackjet_WP_detail[WP][0] != 2) and (numbtrackjet_WP_detail[WP][1] != 2): numbtrackjet_WP[WP] = 211

		# a dictionary to record all b-tagging states
		PassBtagDict = dict()
		for WP in self._TrackJetWP:
			numbtrackjet = numbtrackjet_WP[WP]

			content = dict()
			content['Pass2b3b'] = ((numbtrackjet == 2) or (numbtrackjet == 3))
			content['Pass4b'] = (numbtrackjet == 4)
			content['Pass3b'] = (numbtrackjet == 3)
			content['Pass2b'] = (numbtrackjet == 2)
			content['Pass3b4b'] = ((numbtrackjet == 3) or (numbtrackjet == 4))

			PassBtagDict[WP] = content

		# fill histogram for each ROI
		for WP, PassBtags in PassBtagDict.items():
			for PassBtagName, PassBtagDecision in PassBtags.items():
				if PassBtagDecision:
					self.MakeCutflowPlot(tree, PassBtagName+WP, _isMC)

					if Pass4GoodTrackJet:
						if PassSBMass:
							self.MakeCutflowPlot(tree, "Pass4GoodTrackJet"+PassBtagName+WP+"PassSBMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass4GoodTrackJet"+PassBtagName+WP+"PassSBMass")
						if PassCRMass:
							self.MakeCutflowPlot(tree, "Pass4GoodTrackJet"+PassBtagName+WP+"PassCRMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass4GoodTrackJet"+PassBtagName+WP+"PassCRMass")
						if PassSRMass:
							self.MakeCutflowPlot(tree, "Pass4GoodTrackJet"+PassBtagName+WP+"PassSRMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass4GoodTrackJet"+PassBtagName+WP+"PassSRMass")
					if Pass3GoodTrackJet:
						if PassSBMass:
							self.MakeCutflowPlot(tree, "Pass3GoodTrackJet"+PassBtagName+WP+"PassSBMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass3GoodTrackJet"+PassBtagName+WP+"PassSBMass")
						if PassCRMass:
							self.MakeCutflowPlot(tree, "Pass3GoodTrackJet"+PassBtagName+WP+"PassCRMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass3GoodTrackJet"+PassBtagName+WP+"PassCRMass")
						if PassSRMass:
							self.MakeCutflowPlot(tree, "Pass3GoodTrackJet"+PassBtagName+WP+"PassSRMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass3GoodTrackJet"+PassBtagName+WP+"PassSRMass")

	######################################################################
	# Below is utility region
	######################################################################

	def GetXsecWeight(self, tree):
		if self._ApplyXsecWeight:
			# first-time loading
			if self._XsecConfigObj is None:
				self._XsecConfigObj = ROOT.TEnv(self._XsectionConfig)

				if self._XsecConfigObj is None:
					print ': ERROR! Cannot open Xsec configuration file',self._XsectionConfig
					sys.exit(0)
			
			mcChannelNumber = tree.mcChannelNumber
			xsec = self._XsecConfigObj.GetValue("xsec_%i" % (mcChannelNumber), 1.)
			eff  = self._XsecConfigObj.GetValue("eff_%i" % (mcChannelNumber), 1.)
			k    = self._XsecConfigObj.GetValue("k_%i" % (mcChannelNumber), 1.)
			n    = self._XsecConfigObj.GetValue("n_%i" % (mcChannelNumber), 1.)

			return 1.0*self._Lumi*xsec*k*eff/n

		else:
			return 1.

	def GetDiJetMassWindow(self, j1, j2):
		Hlead = 125.
		HSubl = 115.

		mass_lead = j1.p.M()
		mass_sublead = j2.p.M()

		if (mass_lead <= 0) or (mass_sublead <= 0):
			print 'WARNING! How could you get non-positive mass? It will be assigned to side-band region',mass_lead,mass_sublead
			return 2

		Xhh = ROOT.TMath.Sqrt( pow( (mass_lead - Hlead)/(0.1*mass_lead), 2 ) + pow( (mass_sublead - HSubl)/(0.1*mass_sublead), 2 ) )

		# always exclusive to each other
		# same as XhhCommon cutflow
		if Xhh < 1.6:
			return 0
		elif ( (mass_lead > 95.) and (mass_lead < 160.) and (mass_sublead > 85.) and (mass_sublead < 155.) ):
			return 1
		else:
			return 2

	def MakeTriggerPlot(self, tree, triggerName, cutName, isMC):
		if isMC:
			self.histsvc.AutoFill("GoodEvent", "_TriggerStudy", "ChannelNumber_%s__%s" % (cutName, triggerName), tree.mcChannelNumber, self._EvtWeight[0], 21, 301486.5, 301507.5)

	def MakeCutflowPlot(self, tree, cutName, isMC):
		self.histsvc.AutoFill("GoodEvent", "_Cutflow", "CountEntry_%s" % (cutName), 1, 1., 1, 0.5, 1.5) 
		self.histsvc.AutoFill("GoodEvent", "_Cutflow", "CountWeight_%s" % (cutName), 1, self._EvtWeight[0], 1, 0.5, 1.5)

		if isMC: 
			self.histsvc.AutoFill("GoodEvent", "_Cutflow", "ChannelNumber_CountEntry_%s" % (cutName), tree.mcChannelNumber, 1, 21, 301486.5, 301507.5)
			self.histsvc.AutoFill("GoodEvent", "_Cutflow", "ChannelNumber_CountWeight_%s" % (cutName), tree.mcChannelNumber, self._EvtWeight[0], 21, 301486.5, 301507.5)
	
	def FillTrackJetVars(self, TrackJet, TrackJetName):
		if TrackJet is None:
			return
		else:
			self.histsvc.Set(TrackJetName + "_Pt", TrackJet.p.Pt())
			self.histsvc.Set(TrackJetName + "_Eta", TrackJet.p.Eta())
			self.histsvc.Set(TrackJetName + "_Phi", TrackJet.p.Phi())
			self.histsvc.Set(TrackJetName + "_M", TrackJet.p.M())
			self.histsvc.Set(TrackJetName + "_E", TrackJet.p.E())
			self.histsvc.Set(TrackJetName + "_MV2c20", TrackJet.Double(ROOT.MomKey("MV2c20")))

	def QuickSkimming(self, tree):
		if tree.hcand_boosted_n < 2:                 return False
		if tree.hcand_boosted_pt[0]/1000. < 350.:    return False
		
		return True







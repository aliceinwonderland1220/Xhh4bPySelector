import os
import ROOT
import utils
import PySelectorBase
import array
import sys
from collections import defaultdict

import time

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

		self._TriggerList = ["HLT_j360_a10r_L1J100"]   # only fat-jet trigger since v00-05-00 !
		self._doTriggerCut = True

		self._TrackJetPtCut = 10.
		self._TrackJetEtaCut = 2.5
		self._TrackJetWP = ["77"]                # list of WP to consider

		self._doMuonCorrection = True
		self._MuonPtCut = 4.
		self._MuonEtaCut = 2.5
		self._MuonQualityCut = "Tight"
		self._MuonAddBackBtagWP = "77"           # the b-tagging working point for track-jet considered for muon adding back; Also used as nominal WP for anything

		self._ApplyXsecWeight = True
		# self._XsectionConfig = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-05-00/hh4b_v00-05-00_Xsection.config"
		# self._XsectionConfig = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-05-00/hh4b_v00-05-00_mttStudy_Xsection.config"
		self._XsectionConfig = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/hh4b_v00-05-00/hh4b_v00-05-00_JERStudy_Xsection.config"

		self._GRLXml = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/data/data15_13TeV.periodAllYear_DetStatus-v73-pro19-08_DQDefects-00-01-02_PHYS_StandardGRL_All_Good_25ns.xml"
		self._Lumi = 3.31668          # Number for hh4b-v00-v05-00 -- not taken from GRL, bu re-calculated again with available dataset
		                              # https://atlas-lumicalc.cern.ch/results/c1ca95/result.html
		                              # iLumiCalc.exe --lumitag=OflLumi-13TeV-001 --livetrigger=L1_EM12 --trigger=None --xml=/tmp/lumifiles/c1ca95/data15_13TeV.periodAllYear_DetStatus-v73-pro19-08_DQDefects-00-01-02_PHYS_StandardGRL_All_Good_25ns.xml --lar --lartag=LARBadChannelsOflEventVeto-RUN2-UPD4-04 -r 279932-280422,281130-281411,276073-276954,282625-284484,278727-279928,280423-281075

		self._ForceDataMC = None     # Force to run in either "Data" or "MC". This should be set as None most of the time.

		self._doMttStitch = False          # whether we do the mtt stitch
		self._MttStitchCut = 1100.        # the cut on inclusive ttbar sample of mtt value
		self._MttScale_allhad = 1.41910533173       # the scale factor applied on allhad mtt slices when doing stitching
		self._MttScale_nonallhad = 1.0355925095     # the scale factor applied on nonallhad mtt slices when doing stitching

		self._JetMassCut = 50.            # mass cut on calo-jet, BEFORE muon correction (because jet with mass < 50 GeV is not calibrated at all)

		self._Apply2bSBReweight = False           # apply additional re-weighting on the 2b-SB region
		self._Apply2bSBReweightFile = os.environ["Xhh4bPySelector_dir"]+"/miniNtupleProcessor/ReweightStorage.root"        # the file storing re-weighting functions
		self._Apply2bSBReweightAux = None         # auxiliary object storing all related objects

		self._doJERStudy = True          # turn on JERStudy --- basically the truth response stuffs

		#
		# PRW

		self._doPRW = False
		self._PRWConfigFile = ""
		self._PRWLumiCalcFile = ""

		# PMGCrossSectionTool
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

		#############################
		# Initialize the histograms #
		#############################

		self.histsvc = ROOT.Analysis_AutoHists(self.outputfile)

		self._EvtWeight = array.array('d', [1.])

		self.histsvc.Book("ChannelNumber_DiJetMass", "ChannelNumber", "DiJetMass", self._EvtWeight, 21, 301486.5, 301507.5, 100, 0, 5000)

		self.histsvc.Book("LeadCaloJetPt", "LeadCaloJetPt", self._EvtWeight, 60, 100, 1300)
		self.histsvc.Book("LeadCaloJetEta", "LeadCaloJetEta", self._EvtWeight, 24, -3.0, 3.0)
		self.histsvc.Book("LeadCaloJetPhi", "LeadCaloJetPhi", self._EvtWeight, 35, -3.5, 3.5)
		self.histsvc.Book("LeadCaloJetM", "LeadCaloJetM", self._EvtWeight, 100, 0, 1000)

		self.histsvc.Book("SubLeadCaloJetPt", "SubLeadCaloJetPt", self._EvtWeight, 60, 100, 1300)
		self.histsvc.Book("SubLeadCaloJetEta", "SubLeadCaloJetEta", self._EvtWeight, 24, -3.0, 3.0)
		self.histsvc.Book("SubLeadCaloJetPhi", "SubLeadCaloJetPhi", self._EvtWeight, 35, -3.5, 3.5)
		self.histsvc.Book("SubLeadCaloJetM", "SubLeadCaloJetM", self._EvtWeight, 100, 0, 1000)

		self.histsvc.Book("LeadCaloJetM_SubLeadCaloJetM", "LeadCaloJetM", "SubLeadCaloJetM", self._EvtWeight, 100, 0, 5000, 100, 0, 5000)
		self.histsvc.Book("LeadCaloJetM_SubLeadCaloJetM_fine", "LeadCaloJetM", "SubLeadCaloJetM", self._EvtWeight, 1000, 0, 1000, 1000, 0, 1000)

		self.histsvc.Book("DiJetDeltaPhi", "DiJetDeltaPhi", self._EvtWeight, 70, 0, 3.5)
		self.histsvc.Book("DiJetDeltaEta", "DiJetDeltaEta", self._EvtWeight, 80, -4, 4)
		self.histsvc.Book("DiJetDeltaR", "DiJetDeltaR", self._EvtWeight, 100, 0, 5)
		self.histsvc.Book("DiJetMass", "DiJetMass", self._EvtWeight, 100, 0, 5000)

		self.histsvc.Book("DiJetMassPrime", "DiJetMassPrime", self._EvtWeight, 100, 0, 5000)
		self.histsvc.Book("ChannelNumber_DiJetMassPrime", "ChannelNumber", "DiJetMassPrime", self._EvtWeight, 21, 301486.5, 301507.5, 100, 0, 5000)

		self.histsvc.Book("dRjj_LeadCaloJet", "dRjj_LeadCaloJet", self._EvtWeight, 75, 0, 1.5)
		self.histsvc.Book("dRjj_SubLeadCaloJet", "dRjj_SubLeadCaloJet", self._EvtWeight, 75, 0, 1.5)

		self.TrackJetNameList = [
		                         "LeadTrackJet_LeadCaloJet",
		                         "SubLeadTrackJet_LeadCaloJet",
		                         "LeadTrackJet_SubLeadCaloJet",
		                         "SubLeadTrackJet_SubLeadCaloJet",
		                        ]

		for TrackJetName in self.TrackJetNameList:
			self.histsvc.Book(TrackJetName + "_Pt", TrackJetName + "_Pt", self._EvtWeight, 50, 0, 500)
			self.histsvc.Book(TrackJetName + "_Eta", TrackJetName + "_Eta", self._EvtWeight, 24, -3.0, 3.0)
			self.histsvc.Book(TrackJetName + "_Phi", TrackJetName + "_Phi", self._EvtWeight, 35, -3.5, 3.5)
			self.histsvc.Book(TrackJetName + "_M", TrackJetName + "_M", self._EvtWeight, 100, 0, 1000)
			self.histsvc.Book(TrackJetName + "_E", TrackJetName + "_E", self._EvtWeight, 100, 0, 1000)
			self.histsvc.Book(TrackJetName + "_MV2c20", TrackJetName + "_MV2c20", self._EvtWeight, 220, -1.1, 1.1)

		##########################################
		# Initialize Output Tree for Reweighting #
		##########################################

		self.ntuplesvc = ROOT.Analysis_AutoTrees("Events")
		self.ntuplesvc.GetTree().SetDirectory(self.outputfile)

		EventVarListPython = [
		                       "EventWeight",

		                       "nbtag",
		                       "MassRegion",

		                       "DiJetDeltaPhi",
		                       "DiJetDeltaR",
		                       "LeadCaloJetEta",
		                       "LeadCaloJetPhi",
		                       "LeadTrackJet_LeadCaloJet_Pt",
		                       "SubLeadTrackJet_SubLeadCaloJet_Pt",
		                     ]
		EventVarList = ROOT.vector(ROOT.TString)()
		for EventVar in EventVarListPython:
			EventVarList.push_back( EventVar )

		self.ntuplesvc.SetEventVariableList(EventVarList)

		if not self.ntuplesvc.SetupBranches():
			print "ERROR! Unable to setup ntuple branches!"
			sys.exit(0)

		##########################################
		# Initialize 2bSB reweight function here #
		##########################################

		if self._Apply2bSBReweight:

			self._Apply2bSBReweightAux = {}

			ReweightFile = ROOT.TFile(self._Apply2bSBReweightFile)
			self._Apply2bSBReweightAux['File'] = ReweightFile

			self._Apply2bSBReweightAux['FunctionDict'] = {}
			KeyList = ReweightFile.GetListOfKeys()
			for i in range(KeyList.GetEntries()):

				functionName = KeyList.At(i).GetName()
				splitIndex = functionName.find('_Iter')
				varname = functionName[:splitIndex]

				tf1Obj = ReweightFile.Get(functionName)
				fitMin = ROOT.Double(0.)
				fitMax = ROOT.Double(0.)
				tf1Obj.GetRange(fitMin, fitMax)

				if varname not in self._Apply2bSBReweightAux['FunctionDict'].keys():
					self._Apply2bSBReweightAux['FunctionDict'][varname] = []

				self._Apply2bSBReweightAux['FunctionDict'][varname].append( (tf1Obj, fitMin, fitMax) )

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

		self.specialCount = 0

		#
		# PMGCrossSectionTool
		#

		self._PMGCrossSectionTool = ROOT.SampleInfo()
		PMGFileNameVector = ROOT.vector('string')()
		for fileName in self._PMGCrossSectionFiles:
			PMGFileNameVector.push_back( os.environ['Xhh4bPySelector_dir'] + '/External/PMGCrossSectionTool/data/' + fileName )
		if not self._PMGCrossSectionTool.readInfosFromFiles(PMGFileNameVector):
			print "WARNING! Problem in reading Xsection info!"


	def ProcessEntry(self, tree, entry):

		self.counter += 1

		#######################################
		# reset hist service at the beginning #
		#######################################

		self.histsvc.Reset()

		#########################################
		# reset ntuple service at the beginning #
		#########################################

		self.ntuplesvc.ResetBranches()

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

		#################################
		# Interlock on 2bSB reweighting #
		#################################

		# 2bSB reweighting is only applied on data
		if self._Apply2bSBReweight and _isMC:
			self._Apply2bSBReweight = False

		#########################
		# Interlock on JERStudy #
		#########################

		if self._doJERStudy and (not _isMC):
			self._doJERStudy = False

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

		########################
		# Mtt Stitching for MC #
		########################

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
				self.histsvc.AutoFill("GoodEvent", "_MttStudy", "truth_mtt_%s" % (tree.mcChannelNumber), tree.truth_mtt/1000., self._EvtWeight[0], 300, 0, 3000)


		############
		# Triggers #
		############

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
			if "OR" not in PassedTriggerList:
				return

		self.MakeCutflowPlot(tree, "PassTrigger", _isMC)

		#######
		# GRL #
		#######

		if not _isMC:
			if self.GRL is None:
				print "WARNING! GRL not setup for Data!"
			else:
				if not self.GRL.HasRunLumiBlock(tree.runNumber, tree.lumiBlock):
					return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassGRL", _isMC)
		self.MakeCutflowPlot(tree, "PassGRL", _isMC)

		#####################
		# Calo-jet Business #
		#####################

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

		SubLeadCaloJet = ROOT.TLorentzVector()
		SubLeadCaloJet.SetPtEtaPhiM(tree.hcand_boosted_pt[1]/1000., tree.hcand_boosted_eta[1], tree.hcand_boosted_phi[1], tree.hcand_boosted_m[1]/1000.)
		SubLeadCaloJet = ROOT.Particle(SubLeadCaloJet)

		CaloJetList = [LeadCaloJet, SubLeadCaloJet]

		#
		# calo-jet mass cut (BEFORE muon correction)
		#

		if LeadCaloJet.p.M() < self._JetMassCut: return
		if SubLeadCaloJet.p.M() < self._JetMassCut: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassCaloJetMassCut", _isMC)
		self.MakeCutflowPlot(tree, "PassCaloJetMassCut", _isMC)

		############################
		# Track-jet Reconstruction #
		############################

		# INFO: Starting from hh4b-v00-v01-01, track-jet selection has already been applied when producing miniNtuple. So it becomes redundant to do it here

		AssocTrackJets_LeadCaloJet = []
		for iTrackJet in range(tree.jet_ak2track_asso_pt[0].size()):
			TrackJet = ROOT.TLorentzVector()
			TrackJet.SetPtEtaPhiM(tree.jet_ak2track_asso_pt[0][iTrackJet]/1000., tree.jet_ak2track_asso_eta[0][iTrackJet], tree.jet_ak2track_asso_phi[0][iTrackJet], tree.jet_ak2track_asso_m[0][iTrackJet]/1000.)

			# if TrackJet.Pt() < self._TrackJetPtCut: continue
			# if abs(TrackJet.Eta()) > self._TrackJetEtaCut: continue

			TrackJet = ROOT.Particle(TrackJet)
			TrackJet.Set("MV2c20", tree.jet_ak2track_asso_MV2c20[0][iTrackJet])

			AssocTrackJets_LeadCaloJet.append( TrackJet )

		AssocTrackJets_SubLeadCaloJet = []
		for iTrackJet in range(tree.jet_ak2track_asso_pt[1].size()):
			TrackJet = ROOT.TLorentzVector()
			TrackJet.SetPtEtaPhiM(tree.jet_ak2track_asso_pt[1][iTrackJet]/1000., tree.jet_ak2track_asso_eta[1][iTrackJet], tree.jet_ak2track_asso_phi[1][iTrackJet], tree.jet_ak2track_asso_m[1][iTrackJet]/1000.)

			# if TrackJet.Pt() < self._TrackJetPtCut: continue
			# if abs(TrackJet.Eta()) > self._TrackJetEtaCut: continue

			TrackJet = ROOT.Particle(TrackJet)
			TrackJet.Set("MV2c20", tree.jet_ak2track_asso_MV2c20[1][iTrackJet])

			AssocTrackJets_SubLeadCaloJet.append( TrackJet )

		AssocTrackJetList = [ AssocTrackJets_LeadCaloJet, AssocTrackJets_SubLeadCaloJet  ]
		AssocTrackJetFlattenList = AssocTrackJets_LeadCaloJet + AssocTrackJets_SubLeadCaloJet

		#
		# Response (for MC Only)
		#

		if self._doJERStudy:
			CaloJetListInputForJER = [(iCaloJet, CaloJet) for iCaloJet, CaloJet in enumerate(CaloJetList)]

			self.MakeJERPlots(tree, CaloJetListInputForJER, "AfterCaloJetMassCut")
			self.MakeJERPlots2(tree, CaloJetListInputForJER, "AfterCaloJetMassCut")

			# if (len(AssocTrackJets_LeadCaloJet) == 2) and (len(AssocTrackJets_SubLeadCaloJet)) == 2:
			# 	self.MakeJERPlots(tree, CaloJetListInputForJER, "AfterTwoTrackJetCut")
			# 	self.MakeJERPlots2(tree, CaloJetListInputForJER, "AfterTwoTrackJetCut")

			# 	if self.GetDiJetMassWindow(CaloJetList[0], CaloJetList[1]) == 0:
			# 		self.MakeJERPlots(tree, CaloJetListInputForJER, "AfterHiggsMassWindowCut")
			# 		self.MakeJERPlots2(tree, CaloJetListInputForJER, "AfterHiggsMassWindowCut")

		##################
		# Add Back Muons #
		##################

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
				for TrackJet in AssocTrackJetFlattenList:
					dR = Muon.p.DeltaR(TrackJet.p)

					if dR > 0.2: continue
					if TrackJet.Double("MV2c20") < self._MV2c20CutDict[self._MuonAddBackBtagWP]: continue

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

		for iCaloJet, CaloJet in enumerate(CaloJetList):
			sumMuonCorr = ROOT.TLorentzVector()

			for TrackJet in AssocTrackJetList[iCaloJet]:
				if TrackJet.Exists("MuonAssocIndex"):
					sumMuonCorr += (Muons[TrackJet.Int("MuonAssocIndex")].p)

			CaloJet.p = CaloJet.p + sumMuonCorr

		# From now on, all calo-jet has muon correction

		##########################
		# Calo Jet Kinematic Cut #
		##########################

		# reminder: the baseline 250 GeV and 2.0 eta cut is on calo-jet with NO muon correction

		#
		# Re-apply kineamtics cut on corrected calo-jets
		#

		if LeadCaloJet.p.Pt() < 350.:      return
		if abs(LeadCaloJet.p.Eta()) > 2.0: return

		if SubLeadCaloJet.p.Pt() < 250.:      return
		if abs(SubLeadCaloJet.p.Eta()) > 2.0: return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassCaloKinematicsCut", _isMC)
		self.MakeCutflowPlot(tree, "PassCaloKinematicsCut", _isMC)

		#
		# calo-jet dEta cuts
		# 

		PassdEtaCut = (abs(LeadCaloJet.p.Eta() - SubLeadCaloJet.p.Eta()) < 1.7)

		if not PassdEtaCut:
			return

		for triggerName in PassedTriggerList: self.MakeTriggerPlot(tree, triggerName, "PassdEtaCut", _isMC)
		self.MakeCutflowPlot(tree, "PassdEtaCut", _isMC)

		####################################################################################################################

		###########################
		# Fill Calo-Jet Kinematic #
		###########################

		self.histsvc.Set("LeadCaloJetPt", LeadCaloJet.p.Pt())
		self.histsvc.Set("LeadCaloJetEta", LeadCaloJet.p.Eta())
		self.histsvc.Set("LeadCaloJetPhi", LeadCaloJet.p.Phi())
		self.histsvc.Set("LeadCaloJetM", LeadCaloJet.p.M())

		self.histsvc.Set("SubLeadCaloJetPt", SubLeadCaloJet.p.Pt())
		self.histsvc.Set("SubLeadCaloJetEta", SubLeadCaloJet.p.Eta())
		self.histsvc.Set("SubLeadCaloJetPhi", SubLeadCaloJet.p.Phi())
		self.histsvc.Set("SubLeadCaloJetM", SubLeadCaloJet.p.M())

		self.histsvc.Set("DiJetDeltaPhi", LeadCaloJet.p.DeltaPhi(SubLeadCaloJet.p))
		self.histsvc.Set("DiJetDeltaEta", LeadCaloJet.p.Eta() - SubLeadCaloJet.p.Eta())
		self.histsvc.Set("DiJetDeltaR", LeadCaloJet.p.DeltaR(SubLeadCaloJet.p))
		self.histsvc.Set("DiJetMass", (LeadCaloJet.p + SubLeadCaloJet.p).M())

		LeadCaloJet4pScaled = (LeadCaloJet.p) * (125./LeadCaloJet.p.M())
		SubLeadCaloJet4pScaled = (SubLeadCaloJet.p) * (125./SubLeadCaloJet.p.M())
		self.histsvc.Set("DiJetMassPrime", (LeadCaloJet4pScaled + SubLeadCaloJet4pScaled).M())

		#############################
		# Fill Track-Jet Kinematics #
		#############################

		if len(AssocTrackJets_LeadCaloJet) == 2:
			self.histsvc.Set("dRjj_LeadCaloJet", AssocTrackJets_LeadCaloJet[0].p.DeltaR(AssocTrackJets_LeadCaloJet[1].p))
		if len(AssocTrackJets_SubLeadCaloJet) == 2:
			self.histsvc.Set("dRjj_SubLeadCaloJet", AssocTrackJets_SubLeadCaloJet[0].p.DeltaR(AssocTrackJets_SubLeadCaloJet[1].p))

		#####################################################################################################################

		self.histsvc.MakeHists("GoodEvent", "_BeforeTrackJetMultiplicityCut")

		#####################################################################################################################

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

		#############################
		# Trackjet Multiplicity Cut #
		#############################

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

		#####################################################################################################################

		self.histsvc.MakeHists("GoodEvent", "_BeforeBTagging")

		#####################################################################################################################

		###########################
		# Now we play with b-tags #
		###########################

		numbtrackjet_WP = defaultdict(lambda: 0)
		numbtrackjet_WP_detail = defaultdict(lambda: [0,0])

		for iCaloJet in range(2):
			for iTrackJet in range( min(2, len(AssocTrackJets[iCaloJet])) ):
				TrackJet = AssocTrackJets[iCaloJet][iTrackJet]
				MV2c20 = TrackJet.Double("MV2c20")

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
			content['Pass211b'] = (numbtrackjet == 211)

			PassBtagDict[WP] = content

		# fill histogram for each ROI
		for WP, PassBtags in PassBtagDict.items():
			for PassBtagName, PassBtagDecision in PassBtags.items():
				if PassBtagDecision:
					self.MakeCutflowPlot(tree, PassBtagName+WP, _isMC)

					if Pass4GoodTrackJet:

						Reweight = 1.
						if self._Apply2bSBReweight and (PassBtagName == "Pass2b"):
							Reweight *= self.Get2bSBReweight()

						if PassSBMass:
							self.MakeCutflowPlot(tree, "Pass4GoodTrackJet"+PassBtagName+WP+"PassSBMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass4GoodTrackJet"+PassBtagName+WP+"PassSBMass", Reweight)
						if PassCRMass:
							self.MakeCutflowPlot(tree, "Pass4GoodTrackJet"+PassBtagName+WP+"PassCRMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass4GoodTrackJet"+PassBtagName+WP+"PassCRMass", Reweight)
						if PassSRMass:
							self.MakeCutflowPlot(tree, "Pass4GoodTrackJet"+PassBtagName+WP+"PassSRMass", _isMC)
							self.histsvc.MakeHists("GoodEvent", "_"+"Pass4GoodTrackJet"+PassBtagName+WP+"PassSRMass", Reweight)
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

		####################
		# Fill Ntuple Here #
		####################

		NominalBtagDecision = PassBtagDict[self._MuonAddBackBtagWP]

		# nbtag
		if NominalBtagDecision['Pass2b']:
			nbtag = 2
		elif NominalBtagDecision['Pass3b']:
			nbtag = 3
		elif NominalBtagDecision['Pass4b']:
			nbtag = 4
		else:
			nbtag = -1

		# Fill variables
		# 2/3/4-b, 4-trackjet, either SB or CR
		if (nbtag > 0) and (Pass4GoodTrackJet) and (PassSBMass or PassCRMass):
			self.ntuplesvc.SetEventValue("EventWeight", self._EvtWeight[0])

			self.ntuplesvc.SetEventValue("nbtag", nbtag)
			self.ntuplesvc.SetEventValue("MassRegion", MassRegion)

			self.ntuplesvc.SetEventValue("DiJetDeltaPhi", self.histsvc.Get("DiJetDeltaPhi"))
			self.ntuplesvc.SetEventValue("DiJetDeltaR", self.histsvc.Get("DiJetDeltaR"))
			self.ntuplesvc.SetEventValue("LeadCaloJetEta", self.histsvc.Get("LeadCaloJetEta"))
			self.ntuplesvc.SetEventValue("LeadCaloJetPhi", self.histsvc.Get("LeadCaloJetPhi"))
			self.ntuplesvc.SetEventValue("LeadTrackJet_LeadCaloJet_Pt", self.histsvc.Get("LeadTrackJet_LeadCaloJet_Pt"))
			self.ntuplesvc.SetEventValue("SubLeadTrackJet_SubLeadCaloJet_Pt", self.histsvc.Get("SubLeadTrackJet_SubLeadCaloJet_Pt"))

			self.ntuplesvc.AutoFill()

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

			# use the PMGCrossTool to figure out xsec, eff and k automatically
			# Unit conversion: pb -> fb

			return 1.0*self._Lumi*xsec*k*eff/n

		else:
			return 1.

	def GetDiJetMassWindow(self, j1, j2):
		Hlead = 124.
		HSubl = 115.

		mass_lead = j1.p.M()
		mass_sublead = j2.p.M()

		if (mass_lead <= 0) or (mass_sublead <= 0):
			print 'WARNING! How could you get non-positive mass? It will be assigned to side-band region',mass_lead,mass_sublead
			return 2

		Xhh = ROOT.TMath.Sqrt( pow( (mass_lead - Hlead)/(0.1*mass_lead), 2 ) + pow( (mass_sublead - HSubl)/(0.1*mass_sublead), 2 ) )
		CircleRadius = ROOT.TMath.Sqrt( pow(mass_lead - Hlead, 2) + pow(mass_sublead - HSubl, 2) )

		# always exclusive to each other
		# same as XhhCommon cutflow
		if Xhh < 1.6:
			return 0
		# elif ( (mass_lead > 95.) and (mass_lead < 160.) and (mass_sublead > 85.) and (mass_sublead < 155.) ):        # Run 1 setting
		# elif ( (mass_lead > 95.) and (mass_lead < 155.) and (mass_sublead > 80.) and (mass_sublead < 155.) ):        # Run 2 experiment: Box (95, 80, 60, 75)
		# elif ( (mass_lead > 95.) and (mass_lead < 155.) and (mass_sublead > 85.) and (mass_sublead < 155.) ):        # Run 2 experiment: Box (95, 85, 60, 70)
		elif ( CircleRadius < 35.8 ):                                                                                # Run 2 experiment: Circle r = 35.8 (default since v00-05-00)
		# elif ( CircleRadius < 32.4 ):                                                                                # Run 2 experiment: Circle r = 32.4
		# elif ( Xhh < 2.24 ):                                                                                         # Run 2 experiment: Xhh shape with r=2.24
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
			self.histsvc.Set(TrackJetName + "_MV2c20", TrackJet.Double("MV2c20"))

	def PassMuonQualityCut(self, tree, iMuon):
		if self._MuonQualityCut == "Tight":
			return tree.muon_isTight[iMuon] == 1
		elif self._MuonQualityCut == "Medium":
			return (tree.muon_isMedium[iMuon] == 1) or (tree.muon_isTight[iMuon] == 1)
		elif self._MuonQualityCut == "Loose":
			return (tree.muon_isLoose[iMuon] == 1) or (tree.muon_isMedium[iMuon] == 1) or (tree.muon_isTight[iMuon] == 1)
		else:
			print "Unrecognized muon quality cut",self._MuonQualityCut
			return False

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

	def Get2bSBReweight(self):
		# start = time.time()

		reweight = 1.

		FunctionDict = self._Apply2bSBReweightAux['FunctionDict']
		for varname, FunctionList in FunctionDict.items():
			value = self.histsvc.Get(varname)

			for (tf1Obj, fitMin, fitMax) in FunctionList:
				if (value > fitMin) and (value < fitMax):
					reweight *= tf1Obj(value)

		# end = time.time()

		# print reweight, end - start
		return reweight

	# CaloJetList should be a list of (index, calojet) where index is the index in tree structure
	def MakeJERPlots(self, tree, CaloJetList, CutName):
		for iCaloJet, CaloJet in CaloJetList:
			TruthMatched = tree.truth_hcand_boosted_match[iCaloJet]

			self.histsvc.AutoFill("GoodEvent", "_JERStudy", "CaloJetPt_CaloJetTruthMatch__"+CutName, CaloJet.p.Pt(), TruthMatched, self._EvtWeight[0], 40, 0, 2000, 2, -0.5, 1.5)

			if TruthMatched:
				MatchedTruthJet = ROOT.TLorentzVector()
				MatchedTruthJet.SetPtEtaPhiM(tree.truth_hcand_boosted_pt[iCaloJet]/1000., tree.truth_hcand_boosted_eta[iCaloJet], tree.truth_hcand_boosted_phi[iCaloJet], tree.truth_hcand_boosted_m[iCaloJet]/1000.)

				# Inclusive mass bin
				self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetPtResponse__"+CutName, MatchedTruthJet.Pt(), (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
				if MatchedTruthJet.E() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetEResponse__"+CutName, MatchedTruthJet.Pt(), (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
				if MatchedTruthJet.M() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetMResponse__"+CutName, MatchedTruthJet.Pt(), (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)

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
				self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetPtResponse_%s__%s" % (MassBin, CutName), MatchedTruthJet.Pt(), (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
				if MatchedTruthJet.E() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetEResponse_%s__%s" % (MassBin, CutName), MatchedTruthJet.Pt(), (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)
				if MatchedTruthJet.M() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthPt_CaloJetMResponse_%s__%s" % (MassBin, CutName), MatchedTruthJet.Pt(), (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 40, 0, 2000, 200, 0, 2)

	# measure the response as function of m/pT, in bins of pT
	def MakeJERPlots2(self, tree, CaloJetList, CutName):
		for iCaloJet, CaloJet in CaloJetList:
			TruthMatched = tree.truth_hcand_boosted_match[iCaloJet]

			if TruthMatched:
				MatchedTruthJet = ROOT.TLorentzVector()
				MatchedTruthJet.SetPtEtaPhiM(tree.truth_hcand_boosted_pt[iCaloJet]/1000., tree.truth_hcand_boosted_eta[iCaloJet], tree.truth_hcand_boosted_phi[iCaloJet], tree.truth_hcand_boosted_m[iCaloJet]/1000.)

				TruthBoost = MatchedTruthJet.M()/MatchedTruthJet.Pt()

				# Inclusive pt bin
				self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetPtResponse__"+CutName, TruthBoost, (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
				if MatchedTruthJet.E() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetEResponse__"+CutName, TruthBoost, (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
				if MatchedTruthJet.M() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetMResponse__"+CutName, TruthBoost, (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)

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
				self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetPtResponse_%s__%s" % (MassBin, CutName), TruthBoost, (CaloJet.p.Pt())/(MatchedTruthJet.Pt()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
				if MatchedTruthJet.E() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetEResponse_%s__%s" % (MassBin, CutName), TruthBoost, (CaloJet.p.E())/(MatchedTruthJet.E()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)
				if MatchedTruthJet.M() > 0:  self.histsvc.AutoFill("GoodEvent", "_JERStudy", "TruthBoost_CaloJetMResponse_%s__%s" % (MassBin, CutName), TruthBoost, (CaloJet.p.M())/(MatchedTruthJet.M()), self._EvtWeight[0], 10, 0, 1, 200, 0, 2)









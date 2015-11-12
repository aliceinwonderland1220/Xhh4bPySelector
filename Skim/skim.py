import ROOT
import sys
import os

# f = ROOT.TFile("../../hh4b-v00-00-00.root")
# t = f.Get("XhhMiniNtuple")

def setInput(filename = ""):
	global f
	global t

	if filename == "":
		filename = "../../hh4b-v00-00-00.root"

	f = ROOT.TFile(filename)
	t = f.Get("XhhMiniNtuple")

	print "Setting input to be %s ..." % (filename)

def skim(selection, filename):
	print "Begin to skim wth selection: %s" % (selection)
	
	fnew = ROOT.TFile(filename, "RECREATE")
	tnew = t.CopyTree(selection)
	fnew.WriteTObject(tnew, tnew.GetName(), "Overwrite")

	print "Finish skimming. Output is in %s" % (filename)

def test():
	# setInput("../../RSG.root")
	# skim("PassBoosted == 1", "RSG_boosted.root")

	# setInput("RSG_boosted.root")
	# skim("(PassLeadJetPt == 1) && (PassSubLeadJetPt == 1)", "RSG_boosted_PassLeadSubLeadJetPt.root")

	# setInput("/atlas/local/zengq/XHHbbbb/miniNtuple/hh4b-v00-01-03/data15_13TeV/hh4b_v00-01-03_data.root")
	# skim("hcand_boosted_n == 2", "hh4b_boosted_v00-01-03_data.root")    # two fat-jet with at least 250 GeV

	setInput("hh4b_boosted_v00-01-03_data.root")
	skim("hcand_boosted_pt[0] >= 350000.", "hh4b_boosted_PassLeadSubLeadJetPt_v00-01-03_data.root")   # leading fat-jet needs to be at least 350 GeV
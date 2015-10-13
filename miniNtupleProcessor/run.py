import miniNtupleProcessor
import ROOT
import time
from os.path import dirname, abspath
import os

treename = "XhhMiniNtuple"
filename = os.environ["Xhh4bPySelector_dir"]+"/Skim/hh4b_boosted_PassLeadSubLeadJetPt.root"

# def runLocal():
# 	dataset = ROOT.TChain("XhhMiniNtuple")
# 	dataset.Add(filename)

# 	dataset.Process("TPySelector", "miniNtupleProcessor")

def runProofLite():
	dataset = ROOT.TDSet('TTree', 'XhhMiniNtuple')
	dataset.Add(filename)

	proof = ROOT.TProof.Open("lite://", "workers=4")
	proof.Exec('TPython::Exec("%s");' % ("import sys; sys.path.insert(0,'"+dirname(abspath("miniNtupleProcessor.py"))+"')"))

	time.sleep(1)

	dataset.Process("TPySelector", "miniNtupleProcessor")

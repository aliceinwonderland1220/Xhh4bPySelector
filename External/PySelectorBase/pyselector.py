# Selector module
import PySelectorBase
from math import pi
from ROOT import TH1F

class MyPySelector (PySelectorBase.PySelectorBase):
  def Setup (self):
    "Default option values. These can be changed with an options file created by ntProcess."
    self.variables= "EventNumber ph_pt ph_eta ph_phi jet_pt jet_eta jet_phi"

  def BookHistograms (self):
    "Histograms should be booked here. Names should not conflict with other attributes."
    self.RegisterHistograms ([
      TH1F("evnum",   "event numbers",              1000, 0, 30000),
      TH1F("ph_pt",   "photon p_{T};p_{T} (GeV/c)",  150, 0,   150),
      TH1F("ph_eta",  "photon #eta;#eta",             50,-5,     5),
      TH1F("ph_phi",  "photon #phi;#phi",             50, 0,  2*pi),
      TH1F("jet_pt",  "jet p_{T};p_{T} (GeV/c)",     150, 0,   150),
      TH1F("jet_eta", "jet #eta;#eta",                50,-5,     5),
      TH1F("jet_phi", "jet #phi;#phi",                50, 0,  2*pi),
    ])

  def ProcessEntry (self, tree, entry):
    "Process entry. tree attributes have already been loaded."
    self.evnum.Fill(tree.EventNumber)
    for pt  in tree.ph_pt:   self.ph_pt.Fill(pt/1000.)
    for eta in tree.ph_eta:  self.ph_eta.Fill(eta)
    for phi in tree.ph_phi:  self.ph_phi.Fill(phi)
    for pt  in tree.jet_pt:  self.jet_pt.Fill(pt/1000.)
    for eta in tree.jet_eta: self.jet_eta.Fill(eta)
    for phi in tree.jet_phi: self.jet_phi.Fill(phi)

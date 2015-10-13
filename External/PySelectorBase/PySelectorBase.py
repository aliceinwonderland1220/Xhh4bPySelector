# $Id: PySelectorBase.py,v 1.9 2011/06/10 20:40:57 adye Exp $
# Python Selector base class.
# To create a Selector, inherit from this class and override the
# following methods:
#   Setup():          self.variables= "x y z"
#   BookHistograms(): self.RegisterHistograms ([hist1, hist2])
#   ProcessEntry():   self.hist1.Fill(tree.x)
# Do not import PySelectorBase into your namespace (eg. from PySelectorBase import *)
# or else the selector might use that instead of your derived class (it uses the
# first class it finds in the dictionary that is a sub-class of TPySelector).

import os, re, array, ROOT

class PySelectorBase (ROOT.TPySelector):

#=======================================================================
# Standard Selector methods
#=======================================================================

  def __init__(self):
    print self.__class__.__module__+": init"

    # For some reason, the std.vector(float) and std.vector(long) bindings are
    # not fully loaded in ATLAS ROOT 5.26 proofserv. This may have something to
    # do with the ubiquitous warnings which refer to the same types:
    #   Warning in <TEnvRec::ChangeValue>: duplicate entry <Library.vector<float>=vector.dll> for level 0; ignored
    # This is not a problem with other types (vector(int) or list(float)) or
    # when not run in Proof.
    # The fix is to load the library manually, either with gSystem->Load("vector")
    # or the following #include CINT command.
    if not hasattr(ROOT.std.vector(float),"at"):
      self.Log ("for some reason, std.vector library is not loaded, so let's load it now")
      ROOT.gROOT.ProcessLineSync ("#include <vector>")

    self.entryCount= 0
    self.TTreeClass= None
    self.branches= None

    # Default option values.
    # These can be changed in a sub-class __init__
    # or with an options file created by ntProcess.
    self.histfile= "hist.root"
    self.printInterval= 1000
    self.variables= None
    self.treeAccessor= 2   # 0=no accessor, 1=protect against unread vars, 2=also cache branch addresses
    self.useSetBranchStatus= 0
    self.Setup()

  def Setup (self): pass

  def Begin (self):
    self.name= self.GetOption()
    self.Log ("beginning")

  def Init (self, tree):
    self.Log ("init tree '%s'" % tree.GetName())
    self.SetupBranches   (tree)
    self.SetupTTreeClass (tree)

  def SlaveBegin (self, tree):
    self.name= self.GetOption()
    self.Log ("slave beginning")

    # need to create output file here, due to the usage of AutoHists
    # IMPORTANT: You need to do the merging yourself! Use TProofOutputFile
    self.proofoutputfile = ROOT.TProofOutputFile(self.histfile, "M")
    self.outputfile = self.proofoutputfile.OpenFile("RECREATE")

    self.BookHistograms()
    self.GetOutputList().ls()

  def Process (self, entry):
    if self.GetEntry(entry) <= 0: return 0
    if self.printInterval and self.entryCount % self.printInterval == 0:
      self.Log ("process entry", entry)
    self.ProcessEntry (self.GetTree(), entry)
    self.entryCount += 1
    return 1

  def ProcessEntry (self, tree, entry): pass

  def SlaveTerminate (self):
    self.Log ("slave terminating after %d entries" % self.entryCount)
    self.outputfile.Write()

    self.GetOutputList().Add(self.proofoutputfile)

  def Terminate (self):
    self.Log ("terminating")
    self.Log ("write output to",self.histfile)
    # f= ROOT.TFile(self.histfile,"recreate")
    # for o in self.GetOutputList():
    #   self.Log ("write",o.__class__.__name__+"::"+o.GetName())
    #   f.WriteTObject(o)

#=======================================================================
# Public utility methods
#=======================================================================

  def Log (self, *msgs):
    print self.name+":", " ".join([str(s) for s in msgs])

  def RegisterHistograms (self, histos):
    for h in histos:
      self.__dict__[h.GetName()]= h
      self.GetOutputList().Add(h)
    return

  def GetEntry (self, entry):
    if self.branches:
      ntot= 0
      for branch in self.branches:
        ok= branch.GetEntry(entry)
        if ok<=0: return ok
        ntot += ok
      return ntot
    else:
      return super(PySelectorBase,self).GetEntry (entry)

  def GetTree (self):
    tree= super(PySelectorBase,self).fChain
    if tree and self.TTreeClass: tree.__class__= self.TTreeClass
    return tree
  fChain= property (GetTree)

#=======================================================================
# Private methods
#=======================================================================

  def SetupBranches (self, tree):
    self.branches= []
    if not self.variables:
      self.variables= []
      return
    if type(self.variables) is str: self.variables= [self.variables]
    varlist= []
    for varspec in self.variables:
      for var in re.split (r"\s+", varspec):
        if not var: continue
        branch= tree.GetBranch(var) or tree.GetBranch(var+".")
        if not branch:
          leaf= tree.GetLeaf(var)
          if leaf:
            branch= leaf.GetBranch()
          else:
            self.Log ("variable '%s' is not in %s '%s'" % (var, tree.__class__.__name__, tree.GetName()))
            continue
        self.branches.append(branch)
        varlist.append(var)
    self.variables= varlist
    self.Log (("enable branches in %s '%s':" % (tree.__class__.__name__, tree.GetName())),
              " ".join([b.GetName() for b in self.branches]))
    if self.useSetBranchStatus:
      tree.SetBranchStatus ("*", 0)
      for var in varlist: tree.SetBranchStatus (var, 1)
      self.branches= []

  def SetupTTreeClass (self, tree):
    # Replace TTree's blanket attribute getter (__getattr__) with properties
    # just for the enabled attributes. This is done by replacing the tree
    # object's class with a private class that inherits from PyROOT's TTree.
    # There are three possibilities, selectable with self.treeAccessor:
    #   0: keep default PyROOT TTree class
    #   1: Protect against accessing any of the disabled branches,
    #      giving an AttributeError rather than 0.
    #   2: Also cache branch address for (50-100%) faster access.
    #      This has not been tested for all leaf types, but seems to work for
    #      ints, floats, and std::vectors.
    if not self.variables: return
    MakeAttributeValue= {
      1: self.MakeAttributeValue_Protect,
      2: self.MakeAttributeValue_CacheAddress,
    }.get (self.treeAccessor, None)
    if not MakeAttributeValue: return

    def getattr_error (self, name):   # used to override TTree's __getattr__
      raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))

    self.Log (("enable attributes  %s '%s':" % (tree.__class__.__name__, tree.GetName())), " ".join(self.variables))
    self.TTreeClass= type (tree.__class__.__name__, (tree.__class__,), {})
    self.TTreeClass.__getattr__= getattr_error
    for var in self.variables:
      setattr (self.TTreeClass, var, MakeAttributeValue (tree, tree.__class__.__getattr__, var))
    tree.__class__= self.TTreeClass

  def MakeAttributeValue_Protect (self, tree, PyROOT_getattr, var):
    def getf(self): return PyROOT_getattr (self, var)
    return property (getf)

  def MakeAttributeValue_CacheAddress (self, tree, PyROOT_getattr, var):
    def make_getf_array (valarray):
      def getf(self): return  valarray[0]
      return getf
    def make_getf_array_convert (valarray, conv):
      def getf(self): return conv (valarray[0])
      return getf
    arrayType= {
#     ROOT type:   (array type,converter)
      'Char_t':    ('b',chr),   # an 8 bit signed integer
      'UChar_t':   ('B',chr),   # an 8 bit unsigned integer
      'Short_t':   ('h',None),  # a 16 bit signed integer
      'UShort_t':  ('H',None),  # a 16 bit unsigned integer
      'Int_t':     ('i',None),  # a 32 bit signed integer
      'UInt_t':    ('I',None),  # a 32 bit unsigned integer
      'Float_t':   ('f',None),  # a 32 bit floating point
      'Double_t':  ('d',None),  # a 64 bit floating point
#     'Long64_t':  ('l',None),  # a 64 bit signed integer   [32-bit Linux has array("l").itemsize=4, not 8]
#     'ULong64_t': ('L',None),  # a 64 bit unsigned integer [32-bit Linux has array("L").itemsize=4, not 8]
      'Bool_t':    ('i',None),  # a boolean (return int, which is what TTree does)
    }

    branch= tree.GetBranch (var) or tree.GetBranch(var+".")
    if branch:
      leaf= branch.GetLeaf(var)
      if not leaf:
        leaves= branch.GetListOfLeaves()
        if leaves and len(leaves)==1: leaf= leaves[0]
        else:                         leaf= None
    else:
      leaf= tree.GetLeaf(var)
      branch= leaf.GetBranch()

    if leaf: typ= leaf.GetTypeName()
    else:    typ= ""
    if typ in arrayType:
      atyp, conv= arrayType[typ]
      ar= array.array(atyp,[0])
      branch.SetAddress (ar)
      if conv:
        return property (make_getf_array_convert (ar, conv))
      else:
        return property (make_getf_array         (ar))
    elif branch.GetEntry(0)>0:   # read first entry to ensure address is set up
      if typ=="Long64_t" or typ=="ULong64_t":
        return property (make_getf_array         (leaf.GetValuePointer()))
      else:
        return PyROOT_getattr (tree,var)
    else:
      return self.MakeAttributeValue_Protect (tree, PyROOT_getattr, var)

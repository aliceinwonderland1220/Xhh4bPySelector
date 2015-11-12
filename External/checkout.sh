# AutoHists
mkdir -p AutoHists
cd AutoHists
svn co svn+ssh://qzeng@svn.cern.ch/reps/atlasinst/Institutes/SLAC/AutoHists/trunk AutoHists
ln -s AutoHists/cmt/domake.sh
ln -s AutoHists/cmt/doclean.sh
cd ..

# ProofAnaCore
svn co svn+ssh://qzeng@svn.cern.ch/reps/atlasinst/Institutes/SLAC/ProofAnaCore/trunk ProofAnaCore

# PileupReweighting
svn co svn+ssh://qzeng@svn.cern.ch/reps/atlasoff/PhysicsAnalysis/AnalysisCommon/PileupReweighting/tags/PileupReweighting-00-03-11 PileupReweighting

# GRL
svn co svn+ssh://qzeng@svn.cern.ch/reps/atlasoff/DataQuality/GoodRunsLists/tags/GoodRunsLists-00-01-21 GoodRunsLists

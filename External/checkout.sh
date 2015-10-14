# AutoHists
mkdir -p AutoHists
cd AutoHists
svn co svn+ssh://qzeng@svn.cern.ch/reps/atlasinst/Institutes/SLAC/AutoHists/trunk AutoHists
ln -s AutoHists/cmt/domake.sh
ln -s AutoHists/cmt/doclean.sh
cd ..

# ProofAnaCore
svn co svn+ssh://qzeng@svn.cern.ch/reps/atlasinst/Institutes/SLAC/ProofAnaCore/trunk ProofAnaCore

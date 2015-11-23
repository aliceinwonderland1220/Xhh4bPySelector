#!/bin/bash

user=qzeng

while [ "$1" != "" ]; do
    case $1 in
        -u | --user )           shift
                                user=$1
                                ;;
        * )                     echo "usage: source checkout.sh [[-u | --user] USERNAME]"
                                exit 1
    esac
    shift
done




# AutoHists
mkdir -p AutoHists
cd AutoHists
svn co svn+ssh://$user@svn.cern.ch/reps/atlasinst/Institutes/SLAC/AutoHists/trunk AutoHists
ln -s AutoHists/cmt/domake.sh
ln -s AutoHists/cmt/doclean.sh
cd ..

# ProofAnaCore
svn co svn+ssh://$user@svn.cern.ch/reps/atlasinst/Institutes/SLAC/ProofAnaCore/trunk ProofAnaCore

# PileupReweighting
svn co svn+ssh://$user@svn.cern.ch/reps/atlasoff/PhysicsAnalysis/AnalysisCommon/PileupReweighting/tags/PileupReweighting-00-03-11 PileupReweighting

# GRL
svn co svn+ssh://$user@svn.cern.ch/reps/atlasoff/DataQuality/GoodRunsLists/tags/GoodRunsLists-00-01-21 GoodRunsLists

# PMGCrossSectionTool -- get Xsection information
svn co svn+ssh://$user@svn.cern.ch/reps/atlasphys-comm/Physics/Generators/PMGCrossSectionTool/trunk PMGCrossSectionTool

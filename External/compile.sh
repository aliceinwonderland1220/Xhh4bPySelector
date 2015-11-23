compile() {
  mkdir -p lib
  
  # AutoHists
  echo "-----> Compiling AutoHists"
  cd AutoHists
  sh domake.sh
  cd ..
  cd lib
  rm -f AutoHists
  ln -s ../AutoHists/lib AutoHists
  cd ..

  # ProofAnaCore
  echo "-----> Compiling ProofAnaCore"
  cd ProofAnaCore
  make
  cd ..
  cd lib
  rm -f ProofAnaCore
  ln -s ../ProofAnaCore/lib ProofAnaCore
  cd ..

  # PileupReweighting
  echo "-----> Compiling PileupReweighting"
  cd PileupReweighting/cmt
  make -f Makefile.Standalone
  cd ../StandAlone
  ln -sf ../Root/TPileupReweightingCint_rdict.pcm
  cd ../..
  cd lib
  rm -f PileupReweighting
  ln -s ../PileupReweighting/StandAlone PileupReweighting
  cd ..

  # GRL
  echo "-----> Compiling GRL"
  cd GoodRunsLists/cmt
  make -f Makefile.Standalone
  cd ../StandAlone
  ln -sf ../Root/TGoodRunsListsCint_rdict.pcm
  cd ../..
  cd lib
  rm -f GoodRunsLists
  ln -s ../GoodRunsLists/StandAlone GoodRunsLists
  cd ..

  # PMGCrossSectionTool
  echo "-----> Compiling PMGCrossSectionTool"
  cp Makefile.PMGCrossSectionTool PMGCrossSectionTool/cmt/Makefile.StandAlone
  cd PMGCrossSectionTool/cmt
  make -f Makefile.StandAlone
  cd ../StandAlone
  ln -sf ../Root/TPMGCrossSectionToolCint_rdict.pcm
  cd ../..
  cd lib
  rm -f PMGCrossSectionTool
  ln -s ../PMGCrossSectionTool/StandAlone PMGCrossSectionTool
  cd ..
}

clean() {
  rm -rf lib

  echo "-----> Cleaning AutoHists"
  cd AutoHists
  sh doclean.sh
  cd ..

  echo "-----> Cleaning ProofAnaCore"
  cd ProofAnaCore
  make clean
  cd ..
  
  echo "-----> Cleaning PileupReweighting"
  cd PileupReweighting/cmt
  make -f Makefile.Standalone clean
  cd ..
  rm -rf StandAlone
  cd ..

  echo "-----> Cleaning GRL"
  cd GoodRunsLists/cmt
  make -f Makefile.Standalone clean
  cd ..
  rm -rf StandAlone
  cd ..

  echo "-----> Cleaning PMGCrossSectionTool"
  cd PMGCrossSectionTool/cmt
  make -f Makefile.StandAlone clean
  cd ..
  rm -rf StandAlone
  cd ..
}

CMD=${1}

if [ "$CMD" == "make" ]; then
	compile
fi;

if [ "$CMD" == "clean" ]; then
	clean
fi;

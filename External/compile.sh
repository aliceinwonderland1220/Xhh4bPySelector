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
}

CMD=${1}

if [ "$CMD" == "make" ]; then
	compile
fi;

if [ "$CMD" == "clean" ]; then
	clean
fi;

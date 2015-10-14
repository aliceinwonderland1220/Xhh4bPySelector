compile() {
  mkdir -p lib
  
  # AutoHists
  echo "-----> Compiling AutoHists"
  cd AutoHists
  sh domake.sh
  cd ..
  cd lib
  ln -sf ../AutoHists/lib AutoHists
  cd ..

  # ProofAnaCore
  echo "-----> Compiling ProofAnaCore"
  cd ProofAnaCore
  make
  cd ..
  cd lib
  ln -sf ../ProofAnaCore/lib ProofAnaCore
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
}

CMD=${1}

if [ "$CMD" == "make" ]; then
	compile
fi;

if [ "$CMD" == "clean" ]; then
	clean
fi;

# Xhh4bPySelector
A event loop that run on skimmed Xhh min-ntuple

#################
# How to play ? #
#################

# a very quick start ...

source setup.sh
cd External
source checkout.sh
sh compile.sh
cd ..

# structure
External/ ---> where you put C++ code and underlying PySelector script
Skim/     ---> where you apply skimming on dataset
miniNtupleProcessor ---> where you run the PySelector and loop over skimmed dataset

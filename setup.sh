touch setup_fix.sh

# setup_fix.sh will be used for proof job
echo "export Xhh4bPySelector_dir=${PWD}" > setup_fix.sh
echo "export PYTHONPATH=${PWD}/External/PySelectorBase:${PYTHONPATH}" >> setup_fix.sh

source setup_fix.sh

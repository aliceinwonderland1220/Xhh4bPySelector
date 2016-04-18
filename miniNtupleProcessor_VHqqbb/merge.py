# Please use IP3D_RNN environment in order to have MPI working 
import ROOT
from mpi4py import MPI
import os
import subprocess
import random

_comm = MPI.COMM_WORLD

def Partition(inputList, n):
	def round(number):
		if number >= 0:
			low = int(number)
			up = int(number)+1
		if number < 0:
			low = int(number)-1
			up = int(number)

		if abs(number - low) < abs(number - up):
			return low
		else:
			return up

	random.shuffle(inputList)
	size = round(1.0*len(inputList)/n)

	output = []
	for i in range(0, n):
		if i != n-1:
			output.append(inputList[size*i : size*(i+1)])
		else:
			output.append(inputList[size*i : ])
	return output

# scan directory and distribute the merging job to cores
def GetDirList(dirname):
	rank = _comm.Get_rank()
	nCPU = _comm.Get_size()

	if rank == 0:
		dirList = subprocess.check_output(["ls", dirname]).split("\n")[:-1]
		dirListPartition = Partition(dirList, nCPU)

		print "====================="
		print "dir partition:"
		print dirListPartition
		print "====================="

		for iCPU in range(nCPU):
			_comm.send(dirListPartition[iCPU], dest=iCPU, tag=1)
	
	dirListToMerge = _comm.recv(source=0, tag=1)
	dirListToMerge = [dirname+"/"+item for item in dirListToMerge]
	return dirListToMerge

# input dirname here should be the output from GetDirList
# assuming outputDir has been well-prepared
def RunMerge(dirname, outputNameBase, outputDir):
	rank = _comm.Get_rank()

	sysName = dirname.split("/")[1][6:]   # skip beginning "output"

	if sysName == "":
		outputName = outputNameBase+".root"
	else:
		outputName = outputNameBase + "_" + sysName + ".root"

	cmd = "hadd -f %s/%s %s/0.*/*.root" % (outputDir, outputName, dirname)

	print "Processor %i: Running command %s" % (rank, cmd)
	os.system(cmd)

# dirname here should be the same as the one of GetDirList()
def main(dirname, outputNameBase, outputDir):
	rank = _comm.Get_rank()

	# clear and create new outputDir
	os.system("rm -rf "+outputDir)
	os.system("mkdir "+outputDir)

	dirListToMerge = GetDirList(dirname)
	print "Processor %i: dir to be processed: %s" % (rank, dirListToMerge)

	for item in dirListToMerge:
		RunMerge(item, outputNameBase, outputDir)

if __name__ == "__main__":
	sampleName = "ttbar"
	main("outputSys_"+sampleName, "hist_"+sampleName, "hist_%s_reduced" % (sampleName))

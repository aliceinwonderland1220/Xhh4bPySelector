import os
import subprocess

baseDir = "/u/gl/zengq/nfs2/Atlas/outputs/qqbbNtuple/v11-29-2016"

def GenerateFileList(configName):
	fileList = subprocess.check_output("ls %s/%s" % (baseDir, configName), shell=True).split("\n")[:-1]

	for fileName in fileList:
		sampleName = fileName.split(".root")[0].split("_")[1]

		fOutput = open("filelist_%s_%s.txt" % (sampleName, configName), "w")
		fOutput.write("%s/%s/%s\n" % (baseDir, configName, fileName))
		fOutput.close()

if __name__ == "__main__":
	GenerateFileList("reference")
	GenerateFileList("CombMassOnly")

	GenerateFileList("reference_sys")
	GenerateFileList("CombMassOnly_sys")

	GenerateFileList("CombMassNewVtag")

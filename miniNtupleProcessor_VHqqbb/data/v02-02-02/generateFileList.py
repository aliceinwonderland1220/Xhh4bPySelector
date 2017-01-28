import subprocess

dirName = "/atlas/local/zengq/VHqqbb/MiniNtuples/hh4b-02-02-02/ttbar/"

fList = subprocess.check_output("ls "+dirName, shell=True).split("\n")[:-1]
fOutput = open("filelist_ttbar.txt", "w")

for fName in fList:
	fOutput.write("root://atlprf01:11094/"+dirName+fName+"\n")

fOutput.close()

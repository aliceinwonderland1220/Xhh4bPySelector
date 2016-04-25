import os
import time

sampleList = ["WH", "ZH", "ttbar", "Wjets", "Zjets", "JZXW"]
for sampleName in sampleList:
	if sampleName == "JZXW":
		nworkers = 100
	else:
		nworkers = 50

	cmd = "python run.py -f %s -n %s" % (sampleName, nworkers)
	print cmd
	os.system(cmd)
	time.sleep(2)

	cmd = "hadd hist_%s.root outputSys/FT/output/0.*/*.root" % (sampleName)
	print cmd
	os.system(cmd)	
	time.sleep(2)

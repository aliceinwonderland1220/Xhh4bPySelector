import ROOT
import re

def SortVecIndex(inputlist, FromSmallToBig=False):
	list_index = [(inputlist[index], index) for index in range(len(inputlist))]
	list_index_sorted = sorted(list_index, key=lambda item: item[0], reverse=(not FromSmallToBig))

	output = {
	  "SortedVec": [item[0] for item in list_index_sorted],
	  "SortedIndex": [item[1] for item in list_index_sorted]
	}

	return output

# parsing the PySelector and figure out all branches that will actually be used
def GenerateVariableList(filename):
	f = open(filename, 'r')
	wholetxt = f.read()

	p = re.compile("tree\.[0-9a-zA-Z_]*")
	matchlist = p.findall(wholetxt)

	# remove those redundant
	matchlist_simp = list(set(matchlist))

	# remove "tree."
	return [item[5:] for item in matchlist_simp]
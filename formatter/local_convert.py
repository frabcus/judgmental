"""
Converts a local copy of the Bailii archive to our preferred format.
"""

import os
from bailii_to_judgmental import *


c = 0
start = 0


duds = set()
dudfile = open("dud-file-data.txt",'r')
for l in dudfile:
    l = l.strip()
    if len(l) == 0:
        continue
    if l[0] == '#':
        continue
    duds.add(l)
dudfile.close()
print "There are %d dud filenames"%len(duds)


for (path,dirs,files) in os.walk("../../bailii"):

    for f in files:

        if f in duds:
            continue

        if f[-5:] == ".html":
            c += 1

            if c>start:
                print "%6d: %s"%(c,f)
                BtoJ().read_and_restructure(path+"/"+f,"../../judgmental/"+f)



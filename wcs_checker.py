__author__ = 'pablogsal'

from astropy import wcs
from astropy.io import fits
import sys
import numpy as np
import os
import fnmatch
import time
import math



#Colors for the console output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



# update_progress() : Displays or updates a console progress bar
## Accepts a float between 0 and 1. Any int will be converted to a float.
## A value under 0 represents a 'halt'.
## A value at 1 or bigger represents 100%
def update_progress(progress, time):
    barLength = 30  # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength * progress))
    text = "\rPercent: [{0}] {1:.2f}% --- {3:.2f} s. remain. {2}".format(
        "=" * (block - 1) + ">" + " " * (barLength - (block - 1)-1), progress * 100, status, time)
    sys.stdout.write(text)
    sys.stdout.flush()

def distance(star1, star2):
    """ The angular distance, in degrees, between two Coordinates. """

    # Formula: cos(A) = sin(d1)sin(d2) + cos(d1)cos(d2)cos(ra1-ra2)
    # http://www.astronomycafe.net/qadir/q1890.html
    ra1  = math.radians(star1[0])
    dec1 = math.radians(star1[1])
    ra2  = math.radians(star2[0])
    dec2 = math.radians(star2[1])
    return math.degrees(math.acos(math.sin(dec1) * math.sin(dec2) +
                                  math.cos(dec1) * math.cos(dec2) *
                                  math.cos(ra1-ra2)))


###################################
#########     PROGRAM    ##########
###################################


work_dir=sys.argv[1]
ra=float(sys.argv[2])
dec=float(sys.argv[3])

matches = []

for root, dir, files in os.walk(work_dir):
    for items in fnmatch.filter(files, "*.fits"):
        matches.append(os.path.join(root, items))



wcs_data=[]
meantime=[]


for i in matches:
        try:
            start = time.time()
            hdulist = fits.open(i)
            w = wcs.WCS(hdulist[0].header)
            wcs_data.append([i,np.round(w.wcs_world2pix([[ra,dec]], 1))[0].astype(int),w.wcs_pix2world([[512,
                                                                                                                 512]], 1)[0]])
            end = time.time()
            meantime.append(end - start)
    #print(float(len(info))/len(matches)*100)
            update_progress(float(len(wcs_data)) / len(matches), np.mean(meantime) * (len(matches)-len(wcs_data)))
        except IOError:
            print("Empty file", i)


print('\n')

centers=np.array([[i[2][0],i[2][1]] for i in wcs_data]).transpose()
mcenters=[np.mean(centers[0]),np.mean(centers[1])]

distances=[[entry[0],distance([ra,dec],entry[2])] for entry in wcs_data]
meandis=np.median([i[1] for i in distances])
sigmadis=np.std([i[1] for i in distances])
blist=[i[0] for i in distances if i[1]>meandis+sigmadis]
len(blist)
[blist.append(i[0]) for i in wcs_data if i[1][0]>512+256 or i[1][1]>512+256 ]
blacklist=list(set(blist))



print('The mean center is '+str(mcenters)+'\n')
print('The mean distance is '+str(meandis)+'\n')
print('The stdv of the distance is '+str(sigmadis)+'\n')

for i in blacklist:
    #print('I will delete file '+i)
    os.remove(i)

print('I have deleted a total of '+str(len(blacklist))+' files'+'\n')
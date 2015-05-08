__author__ = 'pablogsal'

import glob
import ccdproc
from ccdproc import CCDData
import numpy as np
from astropy import units as u
import pyfits as fits
import sys
import time
import os
import argparse
import fnmatch
import subprocess
import utilities
import ConfigParser

#Set the .INi file
Config = ConfigParser.ConfigParser()
Config.read('conf.INI')


Type_conf= Config.get('STANDARD_KEYS',"Type")
ExpTime_conf=Config.get('STANDARD_KEYS',"ExpTime")
Filter_conf=Config.get('STANDARD_KEYS',"Filter")
Date_Obs_conf=Config.get('STANDARD_KEYS',"Date_Obs")
Average_conf=Config.get('STANDARD_KEYS',"Average")
Stdev_conf=Config.get('STANDARD_KEYS',"Stdev")
Airmass_conf=Config.get('STANDARD_KEYS',"Airmass")
ObjRa_conf=Config.get('STANDARD_KEYS',"ObjRa")
ObjDec_conf=Config.get('STANDARD_KEYS',"OBJDEC")





parser = argparse.ArgumentParser(description='Reduce science frames with darks and flats.')

parser.add_argument('dir', metavar='dir', type=str, nargs=1,
                   help='The work directory containing flats, darks an data folders.')
parser.add_argument('--verbose', dest='verbose_flag', action='store_const',
                   const=True, default=False,
                   help='Prints more info (default: False)')
parser.add_argument('--cosmic', dest='cosmic_flag', action='store_const',
                   const=True, default=False,
                   help='Clean cosmic rays (default: False)')
parser.add_argument('--stats', dest='stats_flag', action='store_const',
                   const=True, default=False,
                   help='Process statistics of files (default: False)')

args = parser.parse_args()





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

import warnings

if args.verbose_flag == False:
                warnings.filterwarnings('ignore')



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


def give_time(obj):
      return [obj[0:4],obj[5:7],obj[8:10],obj[11:13],obj[14:16],obj[17:19]]

############################################################



work_dir=args.dir[0]
os.system('mkdir '+work_dir+'/calibrated')


print('\n'+bcolors.OKGREEN +"Wellcome to the calibration module (soon better name)" + bcolors.ENDC)



matches=[]
for root, dir, files in os.walk(work_dir):
    for items in fnmatch.filter(files, "*.fits"):
        matches.append(os.path.join(root, items))

work_dir=args.dir[0]

########################
#    MODIFY HERE       #
########################

print('\n'+bcolors.OKBLUE +"I will look up for data images" + bcolors.ENDC)

files=[i for i in matches if fits.getheader(i)[Type_conf]=='object']

print('\n'+bcolors.OKBLUE +"I will look up for dark images" + bcolors.ENDC)

darks=[i for i in matches if fits.getheader(i)[Type_conf]=='dark']

print('\n'+bcolors.OKBLUE +"I will look up for flat images" + bcolors.ENDC)

flats=[i for i in matches if fits.getheader(i)[Type_conf]=='flat']

print('\n'+bcolors.OKBLUE +"All images categorized ^_^" + bcolors.ENDC)



datadates=list(set(["".join(give_time(fits.getheader(i)[Date_Obs_conf])[0:3])      for i in files]))
darkdates=list(set(["".join(give_time(fits.getheader(i)[Date_Obs_conf])[0:3])      for i in darks]))
flatdates=list(set(["".join(give_time(fits.getheader(i)[Date_Obs_conf])[0:3])      for i in flats]))

########################
#                      #
########################



def reduce_night(darkdates_RE,flatdates_RE,datadates_RE,number_night,total_night):


    print('\n'+bcolors.WARNING +"Reducing night "+str(number_night)+' of '+str(total_night) + bcolors.ENDC)


    #Create master dark
    dark_list = []
    #read in each of the data files
    print(bcolors.OKBLUE +"Creating masterdark"+ bcolors.ENDC)
    for img in fnmatch.filter(darks, '*'+ darkdates_RE+'*.fits'):
        ccd = CCDData.read(img, unit="electron")
        dark_list.append(ccd)
        if args.verbose_flag == True:
            print('{0} mean={1:5.3f} std={2:4.3f}'.format(img, ccd.data.mean(), ccd.data.std()))


    #median combine the data
    cb = ccdproc.Combiner(dark_list)
    master_dark = cb.median_combine(median_func=np.median)
    #write out to save the file





    #Create master flat

    rflat_list = []
    iflat_list = []
    #read in each of the data files
    print(bcolors.OKBLUE +"Creating masterflat"+ bcolors.ENDC)
    for img in fnmatch.filter(flats, '*'+ flatdates_RE+'*.fits'):
        ccd = CCDData.read(img, unit=u.adu)
        if ccd.header['FILTER']=='r':
            rflat_list.append(ccd)
            if args.verbose_flag == True:
                print('{0} mean={1:5.3f} std={2:4.3f}'.format(img, ccd.data.mean(), ccd.data.std()))
        elif ccd.header['FILTER']=='i':
            iflat_list.append(ccd)
            if args.verbose_flag == True:
                print('{0} mean={1:5.3f} std={2:4.3f}'.format(img, ccd.data.mean(), ccd.data.std()))



    if len(iflat_list)==0:
        iflat_list=rflat_list

    if len(rflat_list)==0:
        rflat_list=iflat_list

    #median combine the flats after scaling each by its mean
    cb = ccdproc.Combiner(rflat_list)
    cb.scaling= lambda x: 1.0/np.mean(x)
    master_rflat = cb.median_combine(median_func=np.median)
    #master_rflat.write(dir+'/'+'MASTER_rFLAT.fits', clobber=True)
    #median combine the flats after scaling each by its mean
    cb = ccdproc.Combiner(iflat_list)
    cb.scaling= lambda x: 1.0/np.mean(x)
    master_iflat = cb.median_combine(median_func=np.median)
    #master_iflat.write(dir+'/'+'MASTER_iFLAT.fits', clobber=True)



    #Process science stuff

    meantime=[]
    cont=1
    total_len=len(fnmatch.filter(files, '*'+ datadates_RE+'*.fits'))
    print(bcolors.OKBLUE +"Calibrating science files" + bcolors.ENDC)
    for img in fnmatch.filter(files, '*'+ datadates_RE+'*.fits'):
        if args.verbose_flag == True:
            print(bcolors.OKGREEN+'{0} mean={1:5.3f} std={2:4.3f}'.format(img, ccd.data.mean(), ccd.data.std())+bcolors.ENDC)
        else:
            sys.stdout = open(os.devnull, "w")
        start = time.time()
        ccd = CCDData.read(img, unit="electron", wcs=None)
        master_dark._wcs=ccd._wcs #currently needed due to bug
        #subtract the master bias
        ccd = ccdproc.subtract_dark(ccd, master_dark,dark_exposure=60*u.second,data_exposure=20*u.second)

         #flat field the data
        if ccd.header['FILTER']=='r':
            master_rflat._wcs=ccd._wcs #currently needed due to bug
            ccd = ccdproc.flat_correct(ccd, master_rflat)
        elif ccd.header['FILTER']=='i':
            master_iflat._wcs=ccd._wcs #currently needed due to bug
            ccd = ccdproc.flat_correct(ccd, master_iflat)


        sys.stdout = sys.__stdout__

        if args.cosmic_flag == True:
            if args.verbose_flag == True:
                print(bcolors.OKGREEN+'Cleaning cosmic rays for '+str(img.split('/')[-1])+bcolors.ENDC)

            ccd = ccdproc.cosmicray_lacosmic(ccd, error_image=None,thresh=5, mbox=11, rbox=11,gbox=5)




        #ccd.write(img, clobber=True)
        ccd.write(work_dir+'/'+'calibrated/'+(img.split('/')[-1]), clobber=True)
        end = time.time()
        meantime.append(end - start)

        if args.verbose_flag == False:
            update_progress(float(cont) / total_len, np.mean(meantime) * (total_len-cont))
        cont=cont+1














if len(darkdates)<len(datadates):
    for i in range(len(datadates)-len(darkdates)):
        darkdates.append(darkdates[-1])

if len(flatdates)<len(datadates):
    for i in range(len(datadates)-len(flatdates)):
        flatdates.append(flatdates[-1])



for night in range(len(datadates)):
    reduce_night(darkdates[night],flatdates[night],datadates[night],night,len(datadates))

if args.stats_flag:
    subprocess.call("python fits_analize.py "+args.dir[0]+' --nodata', shell=True)

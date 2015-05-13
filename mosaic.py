# !/usr/bin/python
# -*- coding: utf8 -*-
#                         -.
#                  ,,,,,,    `²╗,
#             ╓▄▌█▀▀▀▀▀▀▀█▓▓▓▓▌▄  ╙@╕
#          ▄█▀Γ,╓╤╗Q╣╣╣Q@╤═ Γ▀▓▓▓▓▄ "▒╦
#        ▄▀,╤╣▒▒▒▒▒▒ÅÅ╨╨╨ÅÅ▒▒▒╤▐▓▓▓▓▄ ╙▒╕ └
#      4Γ,╣▒▒ÅÖ▄▓▓▓▓▓█%─     `Å▒Q█▓▓▓▓ └▒╦ ▐╕
#       ╩▒▒`╓▓▓▓▓▀Γ             ╙▒▀▓▓▓▓ ╚▒╕ █
#      ▒▒ ,▓▓▓▓Γ ,                ì▀▓▓▓▌ ▒▒  ▓
#     ▒▒ ╓▓▓▓▀,Q▒                   ▓▓▓▓ ▒▒⌐ ▓
#    ╓▒ ╒▓▓▓▌╣▒▒                    ▓▓▓▓║▒▒⌐ ▓─
#    ╫Γ ▓▓▓█▒▒▒∩                    ▓▓▓▌▒▒▒ ]▓
#    ╫⌐ ▓▓▓]▒▒▒                    ▓▓▓Θ▒▒▒O ▓▓
#    ║µ ▓▓▌ ▒▒▒╕                 ,█▀Γ╒▒▒▒┘ ▓▓`
#     Θ ▀▓▓ ▒▒▒▒⌐▄                 ,╣▒▒Å ▄▓▓Γ
#     ╚  ▓▓ '▒▒▒▒▓▓▄           ,═Q▒▒▒Ö,▄▓▓█ .
#      ╙  ▓▓ "▒▒▒▒╬█▓▓▄▄     `╙╨╢▄▓▓▓▓▓▓█Γ╒┘
#          ▀▓▄ Å▒▒▒▒ç▀█▓▓▓▓▓▓▓▓▓▓▓▓▓▓█▀,d┘
#            ▀▓▄ ╙▒▒▒▒╗, Γ▀▀▀▀▀▀▀Γ ,╓ê╜
#              ▀█▄▄  ╙ÅÅ▒▒▒╣QQQ╩ÅÅ╙
#                  ▀▀m▄
#
#

import os
import fnmatch
import sys
import montage_wrapper as montage
import pyfits as fits
import argparse
import mosaic_utils
import ConfigParser
import time
import numpy as np
import fnmatch
import os.path



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

#Config parsing


#Set the .INi file
Config = ConfigParser.ConfigParser()
Config.read(os.path.dirname(os.path.realpath(__file__))+'/conf.INI')


Type_conf= Config.get('STANDARD_KEYS',"Type")
ExpTime_conf=Config.get('STANDARD_KEYS',"ExpTime")
Filter_conf=Config.get('STANDARD_KEYS',"Filter")
Date_Obs_conf=Config.get('STANDARD_KEYS',"Date_Obs")
Average_conf=Config.get('STANDARD_KEYS',"Average")
Stdev_conf=Config.get('STANDARD_KEYS',"Stdev")
Airmass_conf=Config.get('STANDARD_KEYS',"Airmass")
ObjRa_conf=Config.get('STANDARD_KEYS',"ObjRa")
ObjDec_conf=Config.get('STANDARD_KEYS',"OBJDEC")
date_format=Config.get('STANDARD_KEYS',"Dateformat")



#Argument parsing




parser = argparse.ArgumentParser(description='Reduce science frames with darks and flats.')

parser.add_argument('dir', metavar='dir', type=str, nargs=1,
                   help='The work directory containing flats, darks an data folders.')
parser.add_argument('--verbose', dest='verbose_flag', action='store_const',
                   const=True, default=False,
                   help='Prints more info (default: False)')

args = parser.parse_args()


work_dir=os.path.abspath(args.dir[0])+'/'



matches=[]
for root, dir, files in os.walk(work_dir):
    for items in fnmatch.filter(files, "*.fits"):
        matches.append(os.path.join(root, items))




#Construct file list

fits_list=[]
meantime=[]

print('\n'+mosaic_utils.bcolors.OKBLUE+'Constructing the data '
                                    'index:'+'\n'+'---------------------------------------'+mosaic_utils.bcolors.ENDC+'\n')

#Get the files

########################
#    MODIFY HERE       #
########################

for i in matches:
    start = time.time()
    head=fits.getheader(i)
    fits_list.append(  mosaic_utils.fits_image(i,
                             head[Type_conf],
                             head[ExpTime_conf],
                             head[Filter_conf],
                             head[Date_Obs_conf],
                             date_format,
                             head[Average_conf],
                             head[Stdev_conf],
                             head[Airmass_conf],
                             head[ObjRa_conf],
                             head[ObjDec_conf]
                             )   )
    end =time.time()
    meantime.append(end - start)
    mosaic_utils.update_progress(float(len(fits_list)) / len(matches), np.mean(meantime) * (len(matches)-len(
        fits_list)))


########################
#                      #
########################


#Construct filter folders

filters=list(sorted(set([i.filter for i in fits_list])))

filter_fits=[]

for filt in filters:
    filter_fits.append([i for i in fits_list if i.filter == filt])

filter_count=0
for filt in filter_fits:
    if not os.path.exists(work_dir+'/'+filters[filter_count]):
        os.makedirs(work_dir+'/'+filters[filter_count])

    for file_id in filt:
        os.system('mv '+file_id.direction+' '+work_dir+'/'+filters[filter_count])

    filter_count= filter_count +1


#Mosaic each filter

for filt in filters:
    print ('\n')
    print(bcolors.OKGREEN+"Stacking filter "+filt+bcolors.ENDC+'\n')
    mosaic_utils.montage_filter(work_dir+filt+'/',filt,args.verbose_flag)


os.system('rm -Rf '+work_dir+'*/')
print ('\n')



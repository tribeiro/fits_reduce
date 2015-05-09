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
__author__ = 'pablogsal'

import os
import sys
import fnmatch
import pyfits as fits
import argparse
import utilities
import time
import numpy as np
import tabulate
import del_func
import ConfigParser

#Set the .INi file
Config = ConfigParser.ConfigParser()



parser = argparse.ArgumentParser(description='Analize fits images.')

parser.add_argument('dir', metavar='dir', type=str, nargs=1,
                   help='The work directory containing the images.')
parser.add_argument('--verbose', dest='verbose_flag', action='store_const',
                   const=True, default=False,
                   help='Prints more info (default: False)')
parser.add_argument('--r_night', dest='night_flag', action='store_const',
                   const=True, default=False,
                   help='Remove the night if the night has been detectes as outlier in general (default: False)')
parser.add_argument('--r_internight', dest='internight_flag', action='store_const',
                   const=True, default=False,
                   help=' Remove the INTER-outliers if the night has been detectes as outlier in general(default: '
                        'False)')
parser.add_argument('--r_out', dest='out_flag', action='store_const',
                   const=True, default=False,
                   help='Remove all outlayers (default: False)')
parser.add_argument('--r_bad-nights', dest='badnights_flag', action='store_const',
                   const=True, default=False,
                   help='Remove all nights with less than 3 objects (default: False)')
parser.add_argument('--r_cloud_mea', dest='clouds_flag', action='store_const',
                   const=True, default=False,
                   help='Remove images with clouds using average values(default: False)')
parser.add_argument('--r_cloud_std', dest='clouds_sigma_flag', action='store_const',
                   const=True, default=False,
                   help='Remove images with clouds using sigma values(default: False)')
parser.add_argument('--nodata', dest='data_flag', action='store_const',
                   const=False, default=True,
                   help='Do not remove data outlayers (default: False)')
parser.add_argument('--darks', dest='dark_flag', action='store_const',
                   const=True, default=False,
                   help='Remove dark outlayers (default: False)')
parser.add_argument('--flats', dest='flat_flag', action='store_const',
                   const=True, default=False,
                   help='Remove flat outlayers (default: False)')


args = parser.parse_args()

work_dir=args.dir[0]

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
date_format=Config.get('STANDARD_KEYS',"Dateformat")









#Construct a list of files

matches=[]
for root, dir, files in os.walk(work_dir):
    for items in fnmatch.filter(files, "*.fits"):
        matches.append(os.path.join(root, items))





#Construct file list

fits_list=[]
meantime=[]

print('\n'+utilities.bcolors.OKBLUE+'Constructing the data '
                                    'index:'+'\n'+'---------------------------------------'+utilities.bcolors.ENDC+'\n')

#Get the files

########################
#    MODIFY HERE       #
########################

for i in matches:
    start = time.time()
    fits_list.append(  utilities.fits_image(i,
                             fits.getheader(i)[Type_conf],
                             fits.getheader(i)[ExpTime_conf],
                             fits.getheader(i)[Filter_conf],
                             fits.getheader(i)[Date_Obs_conf],
                             date_format,
                             fits.getheader(i)[Average_conf],
                             fits.getheader(i)[Stdev_conf],
                             fits.getheader(i)[Airmass_conf],
                             fits.getheader(i)[ObjRa_conf],
                             fits.getheader(i)[ObjDec_conf]
                             )   )
    end =time.time()
    meantime.append(end - start)
    utilities.update_progress(float(len(fits_list)) / len(matches), np.mean(meantime) * (len(matches)-len(
        fits_list)))


########################
#                      #
########################


#Classify the files for dates

images=[i for i in fits_list if i.type=='object']
darks=[i for i in fits_list if i.type=='dark']
flats=[i for i in fits_list if i.type=='flat']

if len(images) == 0:
    sys.exit("We have found some errors. \n There is no image files. :(")

datadates=list(sorted(set(["".join(i.give_time()[0:3]) for i in images])))
darkdates=list(sorted(set(["".join(i.give_time()[0:3]) for i in darks])))
flatdates=list(sorted(set(["".join(i.give_time()[0:3]) for i in flats])))


image_classified=[]
for date_i in datadates:
    image_classified.append( [i for i in images if "".join(i.give_time()[0:3]) == date_i ])

dark_classified=[]
for date_i in darkdates:
    dark_classified.append( [i for i in darks if "".join(i.give_time()[0:3]) == date_i ])

flat_classified=[]
for date_i in flatdates:
    flat_classified.append( [i for i in flats if "".join(i.give_time()[0:3]) == date_i ])


#Calculate number of files


n_images=len(datadates)
n_darks=len(darkdates)
n_flats=len(flatdates)

print( 'I found '+str(n_images)+' images, '+str(n_darks)+' darks and '+str(n_flats)+' flats.'+'\n')

#Print data if verbose flag is active
if args.verbose_flag == True:
    print('\n'+utilities.bcolors.OKGREEN+'Found data:'+'\n')

printdata=[]

means=utilities.night_stats(image_classified).mean()
medians=utilities.night_stats(image_classified).median()
stdss=utilities.night_stats(image_classified).std()
mean_stdss=utilities.night_stats(image_classified).mean_std()




for i in range(len(datadates)):
    printdata.append([datadates[i],medians[i],means[i],stdss[i],mean_stdss[i], len(image_classified[i])]  )

if args.verbose_flag == True:
    print (tabulate.tabulate(printdata, headers=['Night', 'Medians','Means',"Std(means)","Mean std","#"],
                             tablefmt='orgtbl') )
    print ('\n'+"-----End data--------"+utilities.bcolors.ENDC+'\n')

file=open(work_dir+'/stats.txt', 'w')
file.write(tabulate.tabulate(printdata, headers=['Night', 'Medians','Means',"Std(means)","Mean std","#"],
                             tablefmt='orgtbl'))
file.write('\n'+'\n'+'\n'+'\n')



#Print the outlayers



utilities.print_outlayers(image_classified,"data",file)
utilities.print_outlayers(dark_classified,"darks",file)
utilities.print_outlayers(flat_classified,"flats",file)


#Kill outlayers if flags are active


if args.night_flag or args.internight_flag or args.out_flag:

    if args.night_flag:
        if args.data_flag:
            del_func.remove_night(image_classified)
        if args.dark_flag:
            del_func.remove_night(dark_classified)
        if args.flat_flag:
            del_func.remove_night(flat_classified)

    elif args.internight_flag:
        if args.data_flag:
            del_func.del_func.remove_internight(image_classified)
        if args.dark_flag:
            del_func.del_func.remove_internight(dark_classified)
        if args.flat_flag:
            del_func.del_func.remove_internight(flat_classified)

    elif args.out_flag:
        if args.data_flag:
            del_func.remove_interall(image_classified)
        if args.dark_flag:
            del_func.remove_interall(dark_classified)
        if args.flat_flag:
            del_func.remove_interall(flat_classified)

    else:
        print(utilities.bcolors.WARNING+'No files deleted'+utilities.bcolors.ENDC+'\n')

else:
    print(utilities.bcolors.WARNING+'No files deleted'+utilities.bcolors.ENDC+'\n')



#Statistics about the number of files

number_files=[]
for i in range(len(datadates)):
    number_files.append( len(image_classified[i])  )

file_mean=np.mean(number_files)
file_median=np.median(number_files)
file_std=np.std(number_files)


print('\n')
file.write('\n' )

print(tabulate.tabulate([[file_mean,file_median,file_std]], headers=['File mean', 'File median','File sigma'],\
                                                                   tablefmt='orgtbl') )
file.write(tabulate.tabulate([[file_mean,file_median,file_std]], headers=['File mean', 'File median','File sigma'],\
                                                                        tablefmt='orgtbl') )
print('\n')
file.write('\n' )


if len([i for i in image_classified if len(i)<3 ]) > len( image_classified )/2:
    print(utilities.bcolors.FAIL+'A LOT OF BAD NIGHTS!! - Consider cleaning those.  :('+utilities.bcolors.ENDC+'\n')

#Remove bad nights if flag is active

if args.badnights_flag:
    del_func.remove_badnight(image_classified)

if args.clouds_flag:
    del_func.remove_cludy(image_classified)

if args.clouds_sigma_flag:
    del_func.remove_cludy_std(image_classified)


file.close()




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
import montage_wrapper as montage
import pyfits as fits
import fnmatch
import datetime
import time
import numpy as np
import os.path
import warnings


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





class fits_image(object):

   def __init__(self, direction="",type="",exptime=0,filter="",date="",date_format='%Y-%m-%dT%H:%M:%S.%f',average=0,stdev=0,airmass=0,ra=0,
                dec=0):
      self.direction = direction
      self.type=type
      self.exptime = exptime
      self.filter = filter
      self.rawdate = datetime.datetime.strptime(date, date_format)
      self.date = self.rawdate.strftime('%Y-%m-%dT%H:%M:%S.%f')
      self.average = average
      self.stdev = stdev
      self.airmass = airmass
      self.ra = ra
      self.dec = dec
   def give_time(self):
      return [self.date[0:4],self.date[5:7],self.date[8:10],self.date[11:13],self.date[14:16],self.date[17:19]]
   def give_filename(self):
      return self.direction.split('/')[-1]





def montage_filter(filter_dir,filter_str,verbose_flag):



    if verbose_flag == False:
        warnings.filterwarnings('ignore')

    matches=[]

    for root, dir, files in os.walk(filter_dir):
        for items in fnmatch.filter(files, "*.fits"):
            matches.append(os.path.join(root, items))


    dates=list(sorted(set([i.split('/')[-1][0:8] for i in matches])))

    sets=[]
    for i in dates:
        sets.append(fnmatch.filter(matches,filter_dir+i+'*.fits'))

    cont=0
    folders=[]
    for i in dates:
        os.system('mkdir '+filter_dir+i)
        folders.append(filter_dir+i)
        for files in sets[cont]:
           os.system('mv '+files+' '+filter_dir+i)
        cont=cont+1

    cont=0
    meantime=[0]


    for dir in folders:
        start = time.time()
        matches=[]
        for root, dire, files in os.walk(dir):
            for items in fnmatch.filter(files, "*.fits"):
              matches.append(os.path.join(root, items))

        # print('Matches: '+str(len(matches)))
        if len(matches) >= 1:
            update_progress(float(cont) / len(folders), np.mean(meantime) * (len(folders)-cont))
            if verbose_flag == False:
                sys.stdout = open(os.devnull, "w")
            else:
                print('Stacking night '+dates[cont])

            montage.mosaic(dir,filter_dir+'out_'+dates[cont], mpi=True, n_proc=16)
            matches=[]
            for root, dir, files in os.walk(dir):
                for items in fnmatch.filter(files, "*.fits"):
                  matches.append(os.path.join(root, items))

            h = fits.getheader(matches[0])
            a = fits.open(filter_dir+'out_'+dates[cont]+'/mosaic.fits', mode='update')
            aa = a[0]
            aa.header.update(h)
            a.close()
            cont=cont+1
        # else:
        #     os.system('mkdir '+filter_dir+'out_'+dates[cont])
        #     os.system('mv '+dir+'/*.fits '+filter_dir+'out_'+dates[cont]+'/mosaic.fits')


        sys.stdout = sys.__stdout__

        end =time.time()
        meantime.append(end - start)






    cont=0
    for dir in folders:
          os.system('mv '+filter_dir+'out_'+dates[cont]+'/mosaic.fits '+filter_dir+'mosaic'+dates[
              cont]+filter_str+'.fits')
          cont=cont+1

    os.system('rm -Rf '+filter_dir+'*/')
    os.system('mv '+filter_dir+'*.fits '+filter_dir+'/../')



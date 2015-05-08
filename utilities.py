__author__ = 'pablogsal'

import sys
import numpy as np
import tabulate


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

   def __init__(self, direction="",type="",exptime=0,filter="",date="",average=0,stdev=0,airmass=0,ra=0,dec=0):
      self.direction = direction
      self.type=type
      self.exptime = exptime
      self.filter = filter
      self.date= date
      self.average = average
      self.stdev = stdev
      self.airmass = airmass
      self.ra = ra
      self.dec = dec
   def give_time(self):
      return [self.date[0:4],self.date[5:7],self.date[8:10],self.date[11:13],self.date[14:16],self.date[17:19]]
   def give_filename(self):
      return self.direction.split('/')[-1]





class night_stats(object):

   def __init__(self, objects=""):
      self.objects = objects
   def mean(self):
      return [ np.mean( [a.average for a in nighty ])  for nighty in self.objects  ]
   def median(self):
      return [ np.median( [a.average for a in nighty ])  for nighty in self.objects  ]
   def std(self):
      return [ np.std( [a.average for a in nighty ])  for nighty in self.objects  ]
   def mean_std(self):
      return [ np.mean( [a.stdev for a in nighty ])  for nighty in self.objects  ]




#Outliers threshold !!!!
def find_outlayers(data_in):
    return [i for i,x in enumerate(data_in) if x> np.median(data_in)+2*np.std(data_in)]





def multi_delete(list_, *args):
    indexes = sorted(list(args), reverse=True)
    for index in indexes:
        del list_[index]
    return list_





def print_outlayers(data_list,name_list,file):
    outlayers=[]
    for out in find_outlayers(night_stats(data_list).median()):
        mean_dat=np.mean([ a.average for a in data_list[out] ])
        vals_dat=[ str(a.average) for a in data_list[out] if a.average >=mean_dat]
        percent=float(len(vals_dat))/len(data_list[out])

        if len(vals_dat) == len( data_list[out] ):
            vals_dat="All"
        elif len(vals_dat) > len( data_list[out] )/2:
            vals_dat="More than 50%"
        else:
            vals_dat=" / ".join(vals_dat)

        outlayers.append(["/".join(data_list[out][0].give_time()[0:3]),vals_dat,mean_dat,percent])





    if len(outlayers)>0:
        print(bcolors.FAIL+'Found some outliers in '+ name_list+':'+bcolors.ENDC+'\n')
        file.write('Found some outliers in '+ name_list+':'+'\n')
        print (tabulate.tabulate(outlayers, headers=['Night', 'Values','Mean','% files'], tablefmt='orgtbl') )
        file.write(tabulate.tabulate(outlayers, headers=['Night', 'Values','Mean','% files'],
                                     tablefmt='orgtbl'))
        print ('\n')
        file.write('\n'+'\n')
    else:
        print(bcolors.OKGREEN+'Not found outliers in '+ name_list+'.'+bcolors.ENDC+'\n')
        file.write('Not found outliers in '+ name_list+'.')
        file.write('\n'+'\n')


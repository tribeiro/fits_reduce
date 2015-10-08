__author__ = 'pablogsal'

import ConfigParser
import os
import sys
import fnmatch
import datetime
from astropy.io import fits
import time
import numpy as np


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


def filter_collection_and(collection,filter_tuples):

    print filter_tuples

    for filter_tuple in filter_tuples:

        collection = collection[  collection[filter_tuple[0]] == filter_tuple[1]   ]

    return collection




def FitsLookup(raw_filenames, config_values):
    """
    To be written
    """
    # TODO: Write this docstring

    filelist = list()
    meantime = list()

    total_len = len(raw_filenames)

    for cont,filename in enumerate(raw_filenames):

        start = time.time()

        header = fits.getheader(filename)
        typestr = header[config_values['type']]

        if typestr == config_values['science_flag']:
            type = 0
        elif typestr == config_values['dark_flag']:
            type = 1
        elif typestr == config_values['flat_flag']:
            type = 2
        else:
            type = 3

        filter = header[config_values['filter']]
        night = datetime.datetime.strptime(header[config_values['date_obs']],config_values['dateformat'])

        if night.hour < 12:
            night = night.date() - datetime.timedelta(days=1)

        filelist.append(( filename, type, filter, str(night), header))

        end = time.time()
        meantime.append(end - start)
        update_progress(float(cont) / total_len, np.mean(meantime) * (total_len-cont))

    dtype = np.dtype([('filename', 'S80'),('type', int), ('filter', 'S10'), ('night', 'S10'),('header',np.object)])

    return np.array(filelist,dtype = dtype)







def get_file_list(work_dir,match_flag='*.*'):
    """
    This function crawls into "wordk_dir" and get the absolute path of all files matching match_flag.
    :param work_dir: String - The directory to index.
    :param flag:  String - fnmatch regex to use for filename matching
    :return: List - A list of strings representing the file AbsPaths in work_dor
    """

    matches=[]
    for root, dir, files in os.walk(work_dir):
        for items in fnmatch.filter(files, match_flag):
            matches.append(os.path.realpath( os.path.join(root, items)))

    return matches



def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")



def get_config_dict(config_file=os.path.dirname(os.path.realpath(__file__))+'/conf.INI',keys='STANDARD_KEYS'):
    """
    This function read the configuration file in config_file and returns the dictionary.

    :param config_file: String - The path of the config file. (Default: Look in the main directory).
    :param keys: String - The Keys section in the config file. (Default: STANDARD_KEYS ).
    :return: Dictionary - A dictionary with the configuration values.
    """

    # Instantiate the configparser
    Config = ConfigParser.ConfigParser()

    # Read the provide config file
    Config.read(config_file)

    #Initialize the dictionary

    config_dictionary=dict(Config.items(keys))

    # Return the dictionary

    return config_dictionary


class bcolors:
    """
    Colors for stdout coloring
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
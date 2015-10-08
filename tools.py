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

def FitsLookup(raw_filenames,header_field,target_flag,verbose_flag):
    """
    Utility function for search among a list of filepaths for certain .fits files that have certain values in the header
    field. When a file is found, then is deleted from the original list.

    :param raw_filenames: List - A list of strings representing the filepaths of the .fits files.
    :param header_field: String - The header field in which the search will be performed.
    :param target_flag: String - The target value of the sarch.
    :return: List - A list of filepaths that match the condition. (Original file is reduced by this elements).
    """
    matches = []
    meantime = []
    total_len = len(raw_filenames)
    cont = 0
    for index,path in enumerate(raw_filenames):
        total_len = len(raw_filenames)
        start = time.time()
        if fits.getheader(path)[header_field]==target_flag:
            matches.append(raw_filenames.pop(index))
        end = time.time()
        meantime.append(end - start)
        if verbose_flag:
            update_progress(float(cont) / total_len, np.mean(meantime) * (total_len-cont))
        cont = cont+1
    print()
    return matches

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

def give_time(obj,date_format):
    """
    Reads the date of string given a proper format and transforms to the standard %Y-%m-%dT%H:%M:%S.%f format.
    :param obj:
    :return:
    """
    rawdate = datetime.datetime.strptime(obj, date_format)
    date = rawdate.strftime('%Y-%m-%dT%H:%M:%S.%f')
    return [date[0:4],date[5:7],date[8:10],date[11:13],date[14:16],date[17:19]]



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
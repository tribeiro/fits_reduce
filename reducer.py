__author__ = 'pablogsal'

import reducer_tools
import os
import sys
import logging
import ccdproc
from ccdproc import CCDData
import numpy as np
from astropy import units as u
from astropy.io import fits
from collections import defaultdict
import time

if __name__ == '__main__':

    # --------------  Start of Parser set up  ----------------

    # Configure the parser values with argparse. Note that this section is here to avoid problems when importing
    # this module.

    import argparse

    parser = argparse.ArgumentParser(description='Reduce science frames with darks and flats.')

    parser.add_argument('dir', metavar='dir', type=str, nargs=1,
                       help='The work directory containing flats, darks an data folders.')
    parser.add_argument('--v', dest='verbose_flag', action='store_const',
                       const=True, default=False,
                       help='Prints more info (default: False)')
    parser.add_argument('--cosmic', dest='cosmic_flag', action='store_const',
                       const=True, default=False,
                       help='Clean cosmic rays (default: False)')
    parser.add_argument('--stats', dest='stats_flag', action='store_const',
                       const=True, default=False,
                       help='Process statistics of files (default: False)')

    args = parser.parse_args()

    # --------------  End of Parser set up  ------------------

    # Renaming some parameters to easy acess

    work_dir=args.dir[0]


    # --------------  Start of Logger set up  ----------------


    # create logger with 'spam_application'
    logger = logging.getLogger('reducer')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(os.path.dirname(work_dir + '/logs/Main.log'))
    fh.setLevel(logging.DEBUG)
    # create console handler
    ch = logging.StreamHandler()

    if args.verbose_flag:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.WARNING)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    # --------------  End of Logger set up  ----------------

    # Get the configuration values fron the conf.INi file

    config_values = reducer_tools.get_config_dict()

    # Create output directory if needed

    if not os.path.exists(work_dir+'/calibrated'):
        os.makedirs(work_dir+'/calibrated')
        logger.warning('Directory created at: {0}'.format(work_dir+'/calibrated'))
    else:
        if not reducer_tools.query_yes_no('Directory already exists! Do you want to continue?'):
            logger.warning('System exit because the output directory already exists')
            sys.exit(0)
        logger.warning('Directory already exists but program continues')


    logger.info('Starting data classification')

    raw_filenames = reducer_tools.get_file_list(work_dir,'*.fits')



    file_collection = reducer_tools.FitsLookup(raw_filenames, config_values)

    night_collection = list(set(file_collection['night']))
    filter_collection = list(set(file_collection['filter']))

    # Get list for fast access

    science_collection = file_collection[file_collection['type'] == 0]
    dark_collection = file_collection[file_collection['type'] == 1]
    flat_collection = file_collection[file_collection['type'] == 2]
    unknown_collection = file_collection[file_collection['type'] == 3]

    print reducer_tools.filter_collection_and(file_collection,[('type',0),('filter','r')])['type']





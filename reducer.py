__author__ = 'pablogsal'

import tools
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

    config_values = tools.get_config_dict()

    # Create output directory if needed

    if not os.path.exists(work_dir+'/calibrated'):
        os.makedirs(work_dir+'/calibrated')
        logger.warning('Directory created at: {0}'.format(work_dir+'/calibrated'))
    else:
        if not tools.query_yes_no('Directory already exists! Do you want to continue?'):
            logger.warning('System exit because the output directory already exists')
            sys.exit(0)
        logger.warning('Directory already exists but program continues')


    logger.info('Starting data classification')

    raw_filenames = tools.get_file_list(work_dir,'*.fits')

    # Look for science files

    logger.info("Looking up for data images")

    # ----------- SCIENCE LOOKUP -----------

    # Initializate science list and search for dark files in remaining elements of raw_filenames

    science_files = tools.FitsLookup(raw_filenames= raw_filenames,
                                     header_field=config_values["type"],
                                     target_flag= config_values["science_flag"],
                                     verbose_flag= args.verbose_flag)

    # Categorize filters among science files
    science_files_categorized = defaultdict(lambda: [])

    for science_file in science_files:

        filter = fits.getheader(science_file)[config_values["filter"]]
        science_files_categorized[filter].append(science_file)

    logger.info("Found {0} filter(s) among science images".format(len(science_files_categorized)))

     # ----------- DARK LOOKUP -----------

    logger.info("Looking up for dark images")

    # Initializate dark_files list and search for dark files in remaining elements of raw_filenames
    dark_files = science_files = tools.FitsLookup(raw_filenames= raw_filenames,
                                     header_field=config_values["type"],
                                     target_flag= config_values["dark_flag"],
                                     verbose_flag= args.verbose_flag)


    # ----------- FLAT LOOKUP -----------

    logger.info("Looking up for flat images")

    # Initializate flat_files list and search for dark files in remaining elements of raw_filenames

    flat_files = science_files = tools.FitsLookup(raw_filenames= raw_filenames,
                                     header_field=config_values["type"],
                                     target_flag= config_values["flat_flag"],
                                     verbose_flag= args.verbose_flag)


    flat_files_categorized = defaultdict(lambda: [])

    for flat_file in flat_files:

        filter = fits.getheader(flat_file)[config_values["filter"]]
        flat_files_categorized[filter].append(flat_file)

    logger.info("Found {0} filter(s) among flat images".format(len(flat_files_categorized)))






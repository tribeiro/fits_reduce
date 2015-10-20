import os
import sys
import shutil
import logging
from argparse import RawTextHelpFormatter
import reducer_tools
from colorlog import ColoredFormatter
__author__ = 'pablogsal'


if __name__ == '__main__':

    # --------------  Start of Parser set up  ----------------

    # Configure the parser values with argparse. Note that this section is here to avoid problems when importing
    # this module.

    import argparse

    parser = argparse.ArgumentParser(
        description=""" Reduction pipeline to calibrate science images.

        The pipeline needs the following in the "dir" folder:

            - Science images
            - Dark / Bias images
            - Flat images

            Notice that the program will use ALL files under the indicated folder,
            using the fits header to classify, so there is no need for special names or grouping.

        The pipeline does the following:

            - Automatic recognition of image cathegory.
            - Automatic date/time classification.
            - Automatic filter and exposure time classification.
            - Automatic reduction of images using these cathegories.
            - Clean cosmic rays.
            - Logging the process.

        The pipeline does NOT do the following:

            - Reduce data using other classification methods that involve
              other variables than exposure time and filters.
            - Pre-procesing routines over data / callibration images.
            - Quality control of provided images and callibrators.
            - Magic.

        The pipeline must be configured for your data using a conf.INi file that must
        be placed in the program folder (standard) or provided using the --conf flag.

        Notes:

        - If the pipeline found more filters for the science images than for the flat
          callibrators it will raise a exception, so be aware of this.

        - The "night" for the pipeline starts at 12:00 PM and ends at 11:59 AM. This
          is because if you take the callibration images after 00:00 and your science
          images after 00:00 then technically you have "two" separate nights if you measure
          nights by the date. By the use of this convention callibration images in the
          same night (real night) will be used together. Beware of this when chechking
          dates in the logger.

        - All the comparisions are performed literal. That means that 'r' and 'R' are different
          filters, and therefore if you have 3 science images with 'r' filter but only flats
          with 'R' filter, this will raise an error (or skip the night).

        """, formatter_class=RawTextHelpFormatter)

    parser.add_argument('dir', metavar='dir', type=str, nargs=1,
                        help='The work directory containing flats, darks an data folders.')
    parser.add_argument('-v', dest='verbose_flag', action='store_const',
                        const=True, default=False,
                        help='Prints more info (default: False)')
    parser.add_argument('-cosmic', dest='cosmic_flag', action='store_const',
                        const=True, default=False,
                        help='Clean cosmic rays (default: False)')
    parser.add_argument('-no-interaction', dest='no_interaction', action='store_const',
                        const=True, default=False,
                        help='Supress all console output and interaction. This overwrites the -v flag')
    parser.add_argument(
        '--conf',
        dest='conf_path',
        default=None,
        help='The path of the conf.INI file (default: None)')

    args = parser.parse_args()

    # --------------  End of Parser set up  ------------------

    # Renaming some parameters to easy acess

    work_dir = os.path.realpath(args.dir[0])

    # --------------  Start of Logger set up  ----------------

    # create logger with 'spam_application'
    logger = logging.getLogger('reducer')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(os.path.dirname(work_dir + '/logs/Main.log'))
    fh.setLevel(logging.DEBUG)
    # create console handler
    ch = logging.StreamHandler()

    if args.no_interaction:
        ch.setLevel(logging.ERROR)
    elif args.verbose_flag:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.WARNING)

    # create formatter and add it to the handlers
    fileformatter = logging.Formatter(
        '%(levelname)s - %(asctime)s - %(name)s - %(message)s')
    consoleformatter = ColoredFormatter(
        "%(log_color)s %(levelname)s - %(asctime)s - %(name)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'reset',
            'WARNING':  'yellow,bg_black',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_black',
        },
        secondary_log_colors={},
        style='%'
    )
    fh.setFormatter(fileformatter)
    ch.setFormatter(consoleformatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    # --------------  End of Logger set up  ----------------

    # Get the configuration values from the conf.INi file. If the file is not found,
    # ask the user if the flag is not on.

    if args.conf_path:
        # Assert that the configuration file provided exists
        config_path = os.path.realpath(args.conf_path)
        if os.path.exists(config_path):
            config_values = reducer_tools.get_config_dict(args.conf_path, keys='keywords')
            path_values = reducer_tools.get_config_dict(args.conf_path, keys='paths')
            overscan_config_values = reducer_tools.get_config_dict(args.conf_path, keys='overscan')
        else:
            if args.no_interaction or not reducer_tools.query_yes_no('Config file cannot be found. Use standard instead?'):
                logger.error('System exit because the config file cannot be found')
                sys.exit(0)
            logger.warning('Config file cannot be found but using standard conf.INI instead.')
            config_values = reducer_tools.get_config_dict(keys='keywords')
            path_values = reducer_tools.get_config_dict(keys='paths')
            overscan_config_values = reducer_tools.get_config_dict(keys='overscan')
    else:
        config_values = reducer_tools.get_config_dict(keys='keywords')
        path_values = reducer_tools.get_config_dict(keys='paths')
        overscan_config_values = reducer_tools.get_config_dict(keys='overscan')

    # Merge all config values into a unique dictionary

    config_values.update(overscan_config_values)

    # Create output directory if needed. If directory already exists, ask the user if the
    # no interaction flag is not on.

    if not os.path.exists(work_dir + '/calibrated'):
        os.makedirs(work_dir + '/calibrated')
        logger.warning('Directory created at: {0}'.format(
            work_dir + '/calibrated'))
    else:
        if args.no_interaction or not reducer_tools.query_yes_no('Directory already exists! Do you want to continue?\nNote: This will erase all dir contents.'):
            logger.error(
                'System exit because the output directory already exists')
            sys.exit(0)
        shutil.rmtree(work_dir + '/calibrated')
        os.makedirs(work_dir + '/calibrated')
        logger.warning('Directory already exists but program continues')

    logger.info('Starting data classification')

    # Get the raw filenames crawling the directory. This step only will find the files with
    # path_values['input_extension'], without attending to their nature.

    raw_filenames = reducer_tools.get_file_list(work_dir, path_values['input_extension'])

    # With the raw filenames, classify them. The classification gives a numpy array with personalized dtype. The
    # structure is as follows:
    #
    #   [('filename', 'S150'),('type', int), ('filter', 'S10'),('exptime',int), ('night', 'S10'),('header',np.object)])
    #
    #  Note: This is the standard dtype. You can create your own modifiying the reducer_tools.py FitsLookup.
    #        To do this, you only have to follow the instructions in the comments of FitsLookup.
    #
    # The use of a numpy array with personalized dtype is for convenience. For example, array slicing,
    # masking, broadcasting...etc. A convenience function called "filter_collection" is provided in
    # the reducer_tools module to search in this array.

    file_collection = reducer_tools.FitsLookup(raw_filenames, config_values, args)

    # Get the unique values of the nights as python set.

    night_collection = list(set(file_collection['night']))

    logger.info('We have found {0} nights to process.'.format(
        len(night_collection)))

    # Get list of different types for fast access. Remember the type convention:
    #
    #       0 = Science file
    #       1 = Dark/Bias file
    #       2 = Flat file
    #       3 = Unknown file
    #

    science_collection = file_collection[file_collection['type'] == 0]
    dark_collection = file_collection[file_collection['type'] == 1]
    flat_collection = file_collection[file_collection['type'] == 2]
    unknown_collection = file_collection[file_collection['type'] == 3]

    # Warn the user if we found images that we could not classify

    if unknown_collection.size:
        logger.warning('We have found {0} images that we cannot classify.'.format(
            len(unknown_collection)))

    # Inform the user of the classification found.

    logger.info('We have found {0} science images'.format(
        len(science_collection)))
    logger.info(
        'We have found {0} dark/bias callibrators'.format(len(dark_collection)))
    logger.info('We have found {0} flat callibrators'.format(
        len(flat_collection)))
    # Start data reduction night by night

    logger.info('Starting data reduction')

    # In this variable we can measure the number of nights that we can
    # callibrated

    num_of_callibrate_nights = 0

    for night_number, night in enumerate(night_collection):

        logger.info('Starting the reduction of night {0} of {1} : {2}'.format(
            night_number + 1, len(night_collection), night))

        night_science_images = reducer_tools.filter_collection(
            science_collection, [('night', night)])
        night_dark_images = reducer_tools.filter_collection(
            dark_collection, [('night', night)])
        night_flat_images = reducer_tools.filter_collection(
            flat_collection, [('night', night)])

        # Suppose that we can run the night
        can_run_night = True

        # Check if we can run the night and warn the user
        if not night_science_images.size:
            logger.warning(
                'Science images cannot be found for night: {0}'.format(night))
            can_run_night = False
        if not night_dark_images.size:
            logger.warning(
                'Dark callibrators cannot be found for night: {0}'.format(night))
            can_run_night = False
        if not night_flat_images.size:
            logger.warning(
                'Flat callibrators cannot be found for night: {0}'.format(night))
            can_run_night = False

        if can_run_night:
            execution_code = reducer_tools.reduce_night(night_science_images, night_dark_images,
                                                        night_flat_images, config_values, args)
            if execution_code == 0:
                num_of_callibrate_nights += 1
        else:
            logger.warning(
                'Aborting the callibration of the night: {0}'.format(night))

    logger.info('{0} nights of {1} correctly callibrated! :)'.format(
        num_of_callibrate_nights, len(night_collection)))

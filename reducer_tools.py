__author__ = 'pablogsal'

import ConfigParser
import os
import sys
import fnmatch
import datetime
from astropy.io import fits
from astropy import units as u
import time
import numpy as np
import logging
import ccdproc
from ccdproc import CCDData
import warnings
# Create logger for module
module_logger = logging.getLogger('reducer.reducer_tools')


def reduce_night(science_collection, dark_collection, flat_collection, config_values, config_arguments):
    """
    This function writes a progressbar to stdout given the progress percent and the remaining time.


    :param science_collection: Numpy array - A numpy array with the science collection data produced by FitsLookup.
    :param dark_collection: Numpy array - A numpy array with the dark collection data produced by FitsLookup.
    :param flat_collection: Numpy array - A numpy array with the flat collection data produced by FitsLookup.
    :param config_values: Dictionary - Dictionary - A dictionary provided by the function get_config_dict that
                            contains the configuration of the fits files ( readed from conf.INI ).
    :param config_arguments: Dictionary - A dictionary provided by argparse initialization that contain the current flags.
    :return: None - Print to stdout the progressbar.
    """

    # Supress astropy warnings

    warnings.filterwarnings('ignore')

    # Renaming some config_arguments for easy acess

    work_dir = config_arguments.dir[0]

    # Get the filter collection of science and flat images

    science_filter_collection = set(science_collection['filter'])
    science_exposures_collection = set(science_collection['exptime'])
    dark_exposures_collection = set(dark_collection['exptime'])
    flat_filter_collection = set(flat_collection['filter'])

    # Check if we have the same filters in flats and science

    assert science_filter_collection.issubset(flat_filter_collection), "There are more filters in the science images" \
        " than in the flat calibrators."

    # Warn the user if we found science images of 0 seconds

    if 0 in science_exposures_collection:
        number_of_null_images = len(filter_collection(science_collection, [('exptime',0)]))
        module_logger.warning("We have found {0} science images with 0 seconds of exposure time.".format(number_of_null_images))

    # ------- MASTER DARK CREATION --------

    module_logger.info("Starting the creation of the master dark")

    # Create a list of CCDData images with the provider darks
    master_dark_collection = dict()

    for dark_exposure_item in dark_exposures_collection:

        exposure_dark_list = list()

        for dark_image_data in filter_collection(dark_collection, [('exptime', dark_exposure_item)]):
            # Open the images and append to the dark list
            dark_image = dark_image_data['filename']
            ccd = CCDData.read(dark_image, unit="electron")
            exposure_dark_list.append(ccd)

        # median combine the data
        cb = ccdproc.Combiner(exposure_dark_list)
        master_dark = cb.median_combine(median_func=np.median)

        # Add the masterdark to the master_flat collection
        master_dark_collection.update({dark_exposure_item: master_dark})

    # ------- MASTER FLAT CREATION --------

    module_logger.info("Starting the creation of the master flats")

    master_flat_collection = dict()

    # Go thought the different filters in the collection

    for flat_filter in flat_filter_collection:

        # Initializate the list that will carry the flat images of the actual
        # filter

        filter_flat_list = list()

        for flat_image_data in filter_collection(flat_collection, [('filter', flat_filter)]):

            # Open the images and append to the filter's flat list
            flat_image = flat_image_data['filename']
            ccd = CCDData.read(flat_image, unit=u.adu)
            filter_flat_list.append(ccd)

        # median combine the flats after scaling each by its mean
        cb = ccdproc.Combiner(filter_flat_list)
        cb.scaling = lambda x: 1.0 / np.mean(x)
        master_flat = cb.median_combine(median_func=np.median)

        # Add the masterflat to the master_flat collection

        master_flat_collection.update({flat_filter: master_flat})

    # ------- REDUCE SCIENCE DATA --------

    module_logger.info("Starting the calibration of the science images")

    # Go thought the different files in the collection

    for image_filter in science_filter_collection:

        module_logger.info("Now calibrating filter: {0}".format(image_filter))

        # Iterate thought each different exposure. This is because the dark files
        # can have different exposures and the callibration must be performed with
        # the masterdark with the nearest exposure time.
        for science_exposure in science_exposures_collection:

            # Science subsubcollection is a really bad name, but is descriptive. Remember that this subcollection
            # are the images with the current filter that has the current
            # exposure time. E.g. ('r' and 20', 'r' and 30).
            science_subcollection = filter_collection(
                science_collection, [('filter', image_filter),
                                        ('exptime', science_exposure)])
            if science_subcollection.size:

                module_logger.info("Now calibrating exposure: {0}".format(science_exposure))

                # Initialize the progress bar variables

                total_len = len(science_subcollection)
                meantime = []

                # Determine if we have a masterdark with the science exposure file.
                #
                #   - If we have a exposure matching masterdark, use it.
                #   - If we do not have a exposure matching masterdark, use the nearest.
                try:
                    selected_masterdark = master_dark_collection[
                        science_exposure]
                    nearest_exposure = 0, science_exposure
                except KeyError:
                    # Get the nearest exoposure in the dark collection.
                    nearest_exposure = min(enumerate(master_dark_collection.keys()),
                                           key=lambda x: abs(x[1] - science_exposure))
                    # Notice that nearest_exposure is a tuple of the form (index,exposure).
                    selected_masterdark = master_dark_collection[nearest_exposure[1]]


                for contador,science_image_data_with_current_exposure in enumerate(science_subcollection):

                    sys.stdout = open(os.devnull, "w")  # To supress astropy warnings.

                    # Notice that until sys stdout is reasigned, no printing
                    # will be allowed in the following lines.

                    # Start timing
                    start = time.time()
                    # Extract the filename from the image data
                    science_image = science_image_data_with_current_exposure['filename']
                    # Read the image
                    ccd = CCDData.read(
                        science_image, unit="electron", wcs=None)
                    # Master dark substraction
                    selected_masterdark._wcs = ccd._wcs  # currently needed due to bug
                    ccd = ccdproc.subtract_dark(
                        ccd, selected_masterdark,
                        dark_exposure=nearest_exposure[1] * u.second, data_exposure=science_exposure * u.second)

                    # flat field the data
                    current_master_flat = master_flat_collection[image_filter]
                    current_master_flat._wcs = ccd._wcs  # currently needed due to bug
                    ccd = ccdproc.flat_correct(ccd, current_master_flat)

                    # If we need to clean cosmic rays, do it.

                    if config_arguments.cosmic_flag:

                        ccd = ccdproc.cosmicray_lacosmic(
                            ccd, error_image=None, thresh=5, mbox=11, rbox=11, gbox=5)

                    # Save the callibrated image to a file
                    #ccd.write(img, clobber=True)
                    ccd.write(work_dir + '/' + 'calibrated/' +
                              (science_image.split('/')[-1]), clobber=True)


                    end = time.time()
                    meantime.append(end - start)

                    sys.stdout = sys.__stdout__ # Restart stdout printing
                    if config_arguments.verbose_flag:
                        update_progress(float(contador + 1) / total_len,
                                        np.mean(meantime) * (total_len - (contador + 1)))



def update_progress(progress, time):
    """
    This function writes a progressbar to stdout given the progress percent and the remaining time.

    :param progress: Float - A number between 0 and 1 representing the percent of the progress.
    :param time: Float - The remaining time of the calculation
    :return: None - Print to stdout the progressbar.
    """
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
        "=" * (block - 1) + ">" + " " * (barLength - (block - 1) - 1), progress * 100, status, time)
    sys.stdout.write(text)
    sys.stdout.flush()


def filter_collection(collection, filter_tuples):
    """
    A utility function to filter a numpy array obtained by FitsLookup.
    :param collection: Numpy array - A numpy array obtained by the use of FitsLookup.
    :param filter_tuples: List of tuples - A list of tuples of the form (field_to_be_filter, field_value)
    :return: Numpy array - A subcollection that matches the filter provided.

    Example:
    >>>filter_collection(  file_collection, [('type', 0), ('filter', 'r')]  )

    This will filter the files with type 0 (science files) and filter 'r'.
    """

    for filter_tuple in filter_tuples:

        collection = collection[collection[filter_tuple[0]] == filter_tuple[1]]

    return collection


def FitsLookup(raw_filenames, config_values, config_arguments):
    """
    Utility function to categorize the fit files. The categorization is done by means of
    a numpy array of personalized dtype:

    np.dtype([('filename', 'S80'),('type', int), ('filter', 'S10'), ('night', 'S10'),('header',np.object)])

    This is for convenience. Notice that in this way we can use numpy's slicing, broadcasting and masking over
    the fields

        -filename
        -type
        -filter
        -night

    in order to make subgroups of this array.


    :param raw_filenames: List - A list of strings with the paths of the files to be categorised.
    :param config_values: Dictionary - A dictionary provided by the function get_config_dict.
    :return: Numpy array of dtype np.dtype([('filename', 'S150'),
            ('type', int), ('filter', 'S10'),('exptime',int), ('night', 'S10'),('header',np.object)])
    """

    warnings.filterwarnings('ignore')

    filelist = list()
    meantime = list()

    total_len = len(raw_filenames)

    for cont, filename in enumerate(raw_filenames):

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
        night = datetime.datetime.strptime(
            header[config_values['date_obs']], config_values['dateformat'])

        if night.hour < 12:
            night = night.date() - datetime.timedelta(days=1)

        exptime = header[config_values['exptime']]

        filelist.append((filename, type, filter, exptime, str(night), header))

        # Update progress bar

        end = time.time()
        meantime.append(end - start)

        if config_arguments.verbose_flag:
            update_progress(float(cont + 1) / total_len,
                            np.mean(meantime) * (total_len - (cont + 1)))

    dtype = np.dtype([('filename', 'S150'), ('type', int),
                      ('filter', 'S10'), ('exptime', int), ('night', 'S10'), ('header', np.object)])

    return np.array(filelist, dtype=dtype)


def get_file_list(work_dir, match_flag='*.*'):
    """
    This function crawls into "wordk_dir" and get the absolute path of all files matching match_flag.
    :param work_dir: String - The directory to index.
    :param flag:  String - fnmatch regex to use for filename matching
    :return: List - A list of strings representing the file AbsPaths in work_dor
    """

    matches = []
    for root, dir, files in os.walk(work_dir):
        for items in fnmatch.filter(files, match_flag):
            matches.append(os.path.realpath(os.path.join(root, items)))

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


def get_config_dict(config_file=os.path.dirname(os.path.realpath(__file__)) + '/conf.INI', keys='STANDARD_KEYS'):
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

    # Initialize the dictionary

    config_dictionary = dict(Config.items(keys))

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

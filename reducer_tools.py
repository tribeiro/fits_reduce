import ConfigParser
import os
import sys
import fnmatch
import logging
import warnings
import datetime
import time
from astropy.io import fits
from astropy import units as u
import numpy as np
import ccdproc
from ccdproc import CCDData

"""This module contains utility functions to use in astronomical data reduction."""
__author__ = 'pablogsal'

# Create logger for module
module_logger = logging.getLogger('reducer.reducer_tools')



# ----------------------  UTILITY FUNCTIONS ---------------------------------- #

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


def get_config_dict(config_file=os.path.dirname(os.path.realpath(__file__)) + '/conf.INI', keys='keywords'):
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

# -------------------  DATA REDUCTION FUNCTIONS ------------------------------ #


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

    # Initialize the filelist and the progressbar variable smeantime and
    # total_len

    filelist = list()
    meantime = list()

    total_len = len(raw_filenames)

    # Loop over each file in raw_filenames getting the desired information

    for cont, filename in enumerate(raw_filenames):

        # Start the time measure
        start = time.time()

        # Get the file header
        header = fits.getheader(filename)

        # Extract the filetipe and classify it
        typestr = header[config_values['exposure_type']]

        if typestr == config_values['science_type_id']:
            img_type = 0
        elif typestr == config_values['dark_type_id'] or typestr == config_values['bias_type_id']:
            img_type = 1
        elif typestr == config_values['flat_type_id']:
            img_type = 2
        else:
            img_type = 3

        # Extract the filter

        filter = header[config_values['filter']]

        # Extract the date and correct it with the time convention (night ->
        # 12:00 to 11:59)
        night = datetime.datetime.strptime(
            header[config_values['observed_date']], config_values['date_format'])

        if night.hour < 12:
            night = night.date() - datetime.timedelta(days=1)

        # Extract the exposure time

        exptime = header[config_values['expousure_time']]

        # ---- HOW TO ADD MORE CLASSIFIERS TO THE RESULTING NUMPY ARRAY ------
        #
        # Using the header variable and the config_values dictionary you can
        # extract all the values from the file. For example, to extract the temp:
        #
        # >>> temp = header[config_values['temp']]
        #
        # Once you have your new variable, you have to add this to the filelist in
        # the code after this comment. For example, to add the temp in the previous-to-last
        # entry:
        #
        # >>> filelist.append((filename, type, filter, exptime, str(night), temp, header))
        #
        # Finally, you have to modify the numpy dtype. Following with our example, as the temp
        # is a float value, we can modify the dtype as:
        #
        # >>> dtype = np.dtype([('filename', 'S150'), ('type', int),
        #                  ('filter', 'S10'), ('exptime', int), ('night', 'S10'),
        #                  ('temp',float),('header', np.object)])
        #
        # Notice that the position of the new type in the dtype variable MUST match the position
        # in which you added your new variable to the filelist. As we added "temp" previous-to-last,
        # we have to add ('temp',float) in the position previous-to-last in the dtype.
        #
        # Now, you can use 'temp' for slicing, broadcasting and perform cool numpy stuff in the resulting
        # array. Also, this value will work in the filter_collection function.
        # Yay!

        # Append all the information to the filelist. MODIFY HERE IF NEEDED!

        filelist.append((filename, img_type, filter,
                         exptime, str(night), header))

        # Update progress bar

        end = time.time()
        meantime.append(end - start)

        if config_arguments.verbose_flag and not config_arguments.no_interaction:
            update_progress(float(cont + 1) / total_len,
                            np.mean(meantime) * (total_len - (cont + 1)))

    # Create the personalized dtype of the numpy array. MODIFY HERE IF NEEDED!

    dtype = np.dtype([('filename', 'S150'), ('type', int),
                      ('filter', 'S10'), ('exptime', int), ('night', 'S10'), ('header', np.object)])

    return np.array(filelist, dtype=dtype)


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


def reduce_night(science_collection, dark_collection, flat_collection, config_values, config_arguments):
    """
    This function reduce science data of one night and save the results to a folder named "reduced". The reduction
    is performed as follows:

        - Create a list of masterdarks (each masterdark has a different value of the exposure time) ^1
        - Create a list of masterflats (each masterflat has a different value of the filter) ^1

        - Reduce the science data as follows:

            *For each filter:
                *For each exposure time with that filter:

                    -- Look for the masterdark with the nearest exposure time
                    -- Look for the masterflat with the current filter.
                    -- Substract masterdark
                    -- Flat field correct the data
                    -- Clean cosmic rays (if requested)
                    -- Save image to ./Calibrated folder

    (1) The master(flat/dark)s are created using mean combine.

    :param science_collection: Numpy array - A numpy array with the science collection data produced by FitsLookup.
    :param dark_collection: Numpy array - A numpy array with the dark collection data produced by FitsLookup.
    :param flat_collection: Numpy array - A numpy array with the flat collection data produced by FitsLookup.
    :param config_values: Dictionary - Dictionary - A dictionary provided by the function get_config_dict that
                            contains the configuration of the fits files ( readed from conf.INI ).
    :param config_arguments: Dictionary - A dictionary provided by argparse initialization that contain the current flags.
    :return: Integer - 0 if no errors raised 1 if errors raised.
    """

    # Supress astropy warnings

    warnings.filterwarnings('ignore')

    # Renaming some config_arguments for easy acess

    work_dir = config_arguments.dir[0]

    # Get the filter and exposure collection of science and flat images

    science_filter_collection = set(science_collection['filter'])
    science_exposures_collection = set(science_collection['exptime'])
    dark_exposures_collection = set(dark_collection['exptime'])
    flat_filter_collection = set(flat_collection['filter'])

    # Inform the user of the filter / exptime found.
    science_exp_times_as_string = ", ".join(
        [str(x) for x in science_exposures_collection])
    dark_exp_times_as_string = ", ".join(
        [str(x) for x in dark_exposures_collection])
    module_logger.info("We have found {0} filters in the science images: {1}".format(
        len(science_filter_collection), ", ".join(science_filter_collection)))
    module_logger.info("We have found {0} exposure times science images: {1}".format(
        len(science_exposures_collection), science_exp_times_as_string))
    module_logger.info("We have found {0} exposure times dark calibrators: {1}".format(
        len(dark_exposures_collection), dark_exp_times_as_string))
    module_logger.info("We have found {0} filters in the flat calibrators {1}".format(
        len(flat_filter_collection), ", ".join(flat_filter_collection)))

    # Check if we have the same filters in flats and science, if not, get the
    # intersection

    if not science_filter_collection.issubset(flat_filter_collection):

        module_logger.warning(
            "There are more filters in the science images than in the flat calibrators")

        science_filter_collection = science_filter_collection.intersection(
            flat_filter_collection)

        module_logger.warning("Triying to work with common filters.")
        module_logger.info("We have found {0} common filters in the science images: {1}".format(
            len(science_filter_collection), ", ".join(science_filter_collection)))

        if not science_filter_collection:

            module_logger.warning(
                "There are no common filters between science images and flat calibrators")
            module_logger.warning("This night will be skiped.")
            return 1

    # Warn the user if we found science images of 0 seconds

    if 0 in science_exposures_collection:
        number_of_null_images = len(filter_collection(
            science_collection, [('exptime', 0)]))
        module_logger.warning(
            "We have found {0} science images with 0 seconds of exposure time.".format(number_of_null_images))
        science_exposures_collection.discard(0)
        module_logger.warning("Discarding images with 0 seconds of exposure time for this night: {0} exposure(s) remain.".format(
            len(science_exposures_collection)))

    # ------- MASTER DARK CREATION --------

    module_logger.info("Starting the creation of the master dark")
    module_logger.info("{0} different exposures for masterdarks are founded".format(
        len(dark_exposures_collection)))

    master_dark_collection = dict()

    # Loop over each exposure time.
    for dark_exposure_item in dark_exposures_collection:
        module_logger.info(
            "Creating masterdark with exposure {0}".format(dark_exposure_item))
        # Initializate dark list for current collection.
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
    module_logger.info("{0} different filters for masterflats are founded".format(
        len(flat_filter_collection)))

    master_flat_collection = dict()

    # Go thought the different filters in the collection

    for flat_filter in flat_filter_collection:

        module_logger.info(
            "Creating masterflat with filter {0}".format(flat_filter))

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
        # can have different exposures and the calibration must be performed with
        # the masterdark with the nearest exposure time.
        for science_exposure in science_exposures_collection:

            # Important!! If you have more classifiers in the numpy dtype and you want
            # to use them, you must modify the code here. For example, if you want to
            # use a 'temp' value as classifier, after modify the dtype following the
            # instructions in FitsLookup, you must add a loop here and modify the sub_collection.
            # Once you have the 'temp' in the dtype, you must add a loop here as:
            #
            # >>>for temp_value in  set(science_collection['temp']):
            #        module_logger.info("Now calibrating temp: {0}".format(temp_value))
            #
            # After this, you MUST indent all the following code (of this function) four spaces to
            # the right, of course. Then, you only have to modify the science_subcollection as follows:
            #
            # >>> science_subcollection = filter_collection(
            #    science_collection, [('filter', image_filter),
            #                            ('exptime', science_exposure),
            #                             ('temp', temp_value) ])
            #
            # Follow this steps for every classifier you want to add. Yay!
            # --------------------------------------------------------------

            # Science subcollection is a really bad name, but is descriptive. Remember that this subcollection
            # are the images with the current filter that has the current
            # exposure time. E.g. ('r' and 20', 'r' and 30).
            science_subcollection = filter_collection(
                science_collection, [('filter', image_filter),
                                     ('exptime', science_exposure)])

            # Continue if we have files to process. This will check if for some filter
            # there are not enought images with the actual exposure time.
            if science_subcollection.size:

                module_logger.info(
                    "Now calibrating exposure: {0}".format(science_exposure))

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
                    # Notice that nearest_exposure is a tuple of the form
                    # (index,exposure).
                    selected_masterdark = master_dark_collection[
                        nearest_exposure[1]]

                # Initialize the progress bar variables

                total_len = len(science_subcollection)
                meantime = []

                # Loop for each image with current (filter,exptime).
                for contador, science_image_data_with_current_exposure in enumerate(science_subcollection):

                    # To supress astropy warnings.
                    sys.stdout = open(os.devnull, "w")

                    # Notice that until sys stdout is reasigned, no printing
                    # will be allowed in the following lines.

                    # Start timing
                    start = time.time()
                    # Extract the filename from the image data
                    science_image = science_image_data_with_current_exposure[
                        'filename']
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

                    # Save the calibrated image to a file
                    #ccd.write(img, clobber=True)
                    ccd.write(work_dir + '/' + 'calibrated/' +
                              (science_image.split('/')[-1]), clobber=True)

                    end = time.time()
                    meantime.append(end - start)

                    sys.stdout = sys.__stdout__  # Restart stdout printing
                    if config_arguments.verbose_flag and not config_arguments.no_interaction:
                        update_progress(float(contador + 1) / total_len,
                                        np.mean(meantime) * (total_len - (contador + 1)))

    return 0

import os
from astropy import units

import numpy as np

from fits_reduce.util.slices import slices_config

__author__ = 'william'

from ConfigParser import RawConfigParser, NoOptionError


class ConfigError(Exception):
    """
    Exception for the config file error
    """


class FitsReduceConfig(object, RawConfigParser):
    """
    This class abstracts the config files and checks for the fits_reduce scripts.
    """

    def __init__(self, config_file, config_type=None):
        """
        Init a fits_reduce config instance.

        Parameters
        ----------
        config_file : string
            Path to the config file

        config_type : string
            Means which script is calling this object.

        See Also
        --------
        ConfigParser.RawConfigParser
        """
        RawConfigParser.__init__(self)

        # Permitted units for the images
        self._permitted_image_units = ['adu', 'electron', 'photon', '1', '']

        # Check if file exists
        if not os.path.exists(config_file):
            raise IOError('File %s does not exists.' % config_file)
        # Load configfile
        self.read(config_file)
        if config_type == 'reducer':
            self.ret = self._load_reducer_vars()
        else:
            print 'Error! Invalid config_type %s.' % config_type

    def _load_reducer_vars(self):
        """
        Reads config file to the reducer script.
        """
        # [paths] - MANDATORY
        # strings
        self.input_extension = self.get('paths', 'input_extension')
        # booleans
        for name in ['save_masterdark', 'save_masterflat']:
            self.__setattr__(name, self.getboolean('paths', name))
        # [keywords] - MANDATORY (except for units)
        # strings
        for name in ['exposure_type', 'expousure_time', 'filter', 'observed_date', 'date_format', 'dark_type_id',
                     'bias_type_id', 'flat_type_id', 'science_type_id']:
            self.__setattr__(name, self.get('keywords', name))
        # units
        # If not defined, Unit will be dimensionless.
        # Images units: 'adu', 'electron', 'photon' and 'dimensionless_unscaled' (if unknown)
        try:
            unit = self.get('keywords', 'image_units')
            if unit not in self._permitted_image_units:
                raise ConfigError('image_units must be one of these: {0}'.format(self._permitted_image_units))
            self.image_units = unit
        except NoOptionError:
            self.image_units = units.dimensionless_unscaled
        # [overscan] - OPTIONAL
        if 'overscan' in self.sections():
            self.subtract_overscan = True
            self.overscan_regions = slices_config(self.get('overscan', 'overscan_regions'))
            self.science_regions = slices_config(self.get('overscan', 'science_regions'))
            self.overscan_axis = self.getint('overscan', 'overscan_axis')

            # Sanity check if number overscan and science regions is the same.
            if len(self.science_regions) != len(self.overscan_regions):
                raise ConfigError('science_regions and overscan_regions must have the same shape!')  # TODO: test

            # Convert the science regions to arrays with index numbers.
            self.science_trim = np.array([], dtype=int)
            for science_slice in self.science_regions:
                self.science_trim = np.append(self.science_trim, np.r_[science_slice])
            self.science_trim = np.sort(self.science_trim)
            if self.science_trim.shape != np.unique(self.science_trim).shape:
                raise ConfigError('There are two science regions that intersect each other.')  # TODO: test
        else:
            self.subtract_overscan = False

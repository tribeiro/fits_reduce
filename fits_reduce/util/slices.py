import re

from ccdproc.utils.slices import slice_from_string

inside_brackets = re.compile('\[(.*?)\]')


def slices_config(config):
    """
    From a string of the configuration file containing slices, returns a list with the slices to calculate, for example,
    the overscan, or trim image.
    :param config: string containing the slices
    :return: slices
    """
    return [slice_from_string(match.group()) for match in inside_brackets.finditer(config)]


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


def test_slices():
    assert slices_config('[0:10, 20:30], [30, 40:50], [13::], [::-1]') == [(slice(0, 10, None), slice(20, 30, None)),
                                                                           (slice(None, 30, None), slice(40, 50, None)),
                                                                           (slice(13, None, None),),
                                                                           (slice(None, None, -1),)]

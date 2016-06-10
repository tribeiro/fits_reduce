
import ccdproc
from ccdproc.utils.slices import slice_from_string
import logging

log = logging.getLogger(__name__)

class CCDSection(object):

    def __init__(self):
        self.serial_index = 0
        self.parallel_index = 0

        self.serial_size = 0
        self.parallel_size= 0

        self.sec = None

        self.gain = 1.0
        self.ron = 0.0

        self.serial_scans = []
        self.serial_scans_correct = []

        self.parallel_scans = []
        self.parallel_scans_correct = []

    def get_section(self):
        return self.sec

    def set_section(self, value):
        if type(value) != str:
            raise TypeError('Input type must be string. Got %s' % type(value))

        self.sec = slice_from_string(value)
        self.serial_size = self.sec[1].stop - self.sec[1].start
        self.parallel_size = self.sec[0].stop - self.sec[0].start

    section = property(get_section, set_section)

    def configOverScanRegions(self):

        def parse_scan(scan):
            # print scan
            # Try to parse it to integer
            try:
                reg_len = int(scan[1])
                if scan[0] == 'serial_pre':
                    log.debug('Serial pre-scan with %i length.' % reg_len)
                    return self.section[0], slice(self.section[1].start-reg_len,self.section[1].start)
                elif scan[0] == 'serial_pos':
                    log.debug('Serial pos-scan with %i length.' % reg_len)
                    return self.section[0], slice(self.section[1].stop,self.section[1].stop+reg_len)
                elif scan[0] == 'parallel_pre':
                    log.debug('Parallel pre-scan with %i length.' % reg_len)
                    return slice(self.section[0].start-reg_len,self.section[0].start), self.section[1]
                elif scan[0] == 'parallel_pos':
                    log.debug('Parallel pos-scan with %i length.' % reg_len)
                    return slice(self.section[0].stop,self.section[0].stop+reg_len), self.section[1]
                else:
                    raise KeyError('%s is not a valid key. Should be one of serial_pre, serial_pos, '
                                   'parallel_pre or parallel_pos' % (scan[0]))
            except ValueError, e:
                log.debug('Region is not convertible to int. Falling back to slice mode.')
                return slice_from_string(scan[1])

        for i_serial in range(len(self.serial_scans)):
            self.serial_scans[i_serial] = parse_scan(self.serial_scans[i_serial])

        for i_parallel in range(len(self.parallel_scans)):
            self.parallel_scans[i_parallel] = parse_scan(self.parallel_scans[i_parallel])

    def __str__(self):
        return 'CCDSection: %s has %i serial and %i parallel overscans' % (self.section,
                                                                           len(self.serial_scans),
                                                                           len(self.parallel_scans))

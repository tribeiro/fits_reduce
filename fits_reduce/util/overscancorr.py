
import numpy as np
from scipy import interpolate
import ccdproc
from ccdproc.utils.slices import slice_from_string
from ccdsection import CCDSection

import ConfigParser

import logging

log = logging.getLogger(__name__)


class OverscanCorr():

    def __init__(self,*args,**kwargs):

        self.ccd = None

        self._serialports = 1
        self._parallelports = 1

        self._ccdsections = []

        self._serial_prescan_correct = []
        self._serial_posscan_correct = []
        self._parallel_prescan_correct = []
        self._parallel_posscan_correct = []

        if 'config' in kwargs.keys():
            self.loadConfiguration(kwargs['config'])

    def read(self,filename):
        try:
            self.ccd = ccdproc.CCDData.read(filename)
        except ValueError, e:
            self.ccd = ccdproc.CCDData.read(filename,unit='adu')

    def loadConfiguration(self,configfile):
        '''
        Sample configuration file.

        [ccdconfig]
        serialports: 1
        parallelports: 1

        [section_1_1]
        region: [6:506,6:506]
        serialprescan: 6        # if int will consider overscan as comming for 1st pixel
        serialprescancorr: True
        serialposscan: [506:512,6:506] # define as a image slice
        serialposcancorr: True
        parallelprescan: [6:506,0:6] # Again with image slice
        parallelprescancorr: True
        parallelposscan: 6 # again with number of pixels, but now postscan. Start at the last pixel in the science region
        parallelposcancorr: True

        :param configfile:
        :return:
        '''

        config = ConfigParser.RawConfigParser()

        config.read(configfile)

        if config.has_section('ccdconfig'):
            self._serialports = int(config.get('ccdconfig', 'serialports'))
            self._parallelports = int(config.get('ccdconfig', 'parallelports'))

        for serial in range(self._serialports):
            for parallel in range(self._parallelports):

                ccdsec = CCDSection()
                ccdsec.serial_index = serial
                ccdsec.parallel_index = parallel
                ccdsec.section = config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                    'region')
                ccdsec.serial_scans.append(('serial_pre', config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                          'serialprescan')))
                ccdsec.serial_scans_correct.append(bool(config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                                    'serialprescancorr')=='True'))
                ccdsec.serial_scans.append(('serial_pos', config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                          'serialposscan')))
                ccdsec.serial_scans_correct.append(bool(config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                                    'serialposscancorr')=='True'))
                ccdsec.parallel_scans.append(('parallel_pre', config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                          'parallelprescan')))
                ccdsec.parallel_scans_correct.append(bool(config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                                    'parallelprescancorr')=='True'))
                ccdsec.parallel_scans.append(('parallel_pos', config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                          'parallelposscan')))
                ccdsec.parallel_scans_correct.append(bool(config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                                    'parallelposscancorr')=='True'))
                if config.has_option('section_%i_%i' % ( serial+1, parallel+1),
                                     'gain'):
                    ccdsec.gain = float(config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                  'gain'))

                if config.has_option('section_%i_%i' % ( serial+1, parallel+1),
                                     'ron'):
                    ccdsec.ron = float(config.get('section_%i_%i' % ( serial+1, parallel+1),
                                                  'ron'))

                # print ccdsec.section, ccdsec.parallel_size, ccdsec.serial_size
                ccdsec.configOverScanRegions()

                self._ccdsections.append(ccdsec)

        # self.configOverScanRegions()

    # Todo: Check that ccdsections actually makes sense.
    # Do they follow the serial/parallel order?
    # Do they overlap with each other?


    # def configOverScanRegions(self):
    #     '''
    #     Parse overscan regions to build image slices. If they where gives as slices, test they are ok.
    #     :return:
    #     '''
    #
    #     for i_scan in range(len(self.scans)):
    #         scan = self.scans[i_scan]
    #         for i_region in range(len(scan[1])):
    #             # Try to parse it to integer
    #             region = None
    #             try:
    #                 reg_len = int(scan[1][i_region])
    #                 if scan[0] == 'serial_pre':
    #                     log.debug('Serial pre-scan with %i length.' % reg_len)
    #                     region = (slice(None,None),slice(None,reg_len))
    #                 elif scan[0] == 'serial_pos':
    #                     log.debug('Serial pos-scan with %i length.' % reg_len)
    #                     region = (slice(None,None),slice(-reg_len,None))
    #                 elif scan[0] == 'parallel_pre':
    #                     log.debug('Parallel pre-scan with %i length.' % reg_len)
    #                     region = (slice(None,reg_len),slice(None,None))
    #                 elif scan[0] == 'parallel_pos':
    #                     log.debug('Parallel pos-scan with %i length.' % reg_len)
    #                     region = (slice(-reg_len,None),slice(None,None))
    #                 else:
    #                     raise KeyError('%s is not a valid key. Should be one of serial_pre, serial_pos, '
    #                                    'parallel_pre or parallel_pos' % (scan[0]))
    #             except ValueError, e:
    #                 log.debug('Region is not convertible to int. Falling back to slice mode.')
    #                 region = slice_from_string(region)
    #                 pass
    #             self.scans[i_scan][1][i_region] = region
    #
    #     # Todo: Check that overscan region actually makes sense, i.e. do not overlaps with science array.

    def show(self):
        '''
        Display image of the CCD data with overplotted regions.

        :return:
        '''
        import pyds9 as ds9

        d = ds9.ds9()

        # print self._ccdsections[0].parallel_scans[1]

        d.set_np2arr(self.ccd.data[self._ccdsections[0].parallel_scans[1]])

    def overscan(self,niter=1):
        '''
        Subtract overscan from current CCDData image.

        :return: Nothing.
        '''

        overscan_img = np.zeros_like(self.ccd.data,dtype=np.float)
        serial_overscan_img = np.zeros_like(self.ccd.data,dtype=np.float)
        parallel_overscan_img = np.zeros_like(self.ccd.data,dtype=np.float)

        # import pyds9 as ds9
        #
        # d = ds9.ds9()

        # print self._ccdsections[0].parallel_scans[1]
        # d.set_np2arr(newdata)
        # d.set_np2arr(overscan_img)

        import pylab as py

        for subarr in self._ccdsections:
            # log.debug(subarr.serial_scans)

            scan_level = np.zeros(len(subarr.serial_scans)+len(subarr.parallel_scans))
            scan_mask  = np.zeros(len(subarr.serial_scans)+len(subarr.parallel_scans)) == 0
            for i,serial in enumerate(subarr.serial_scans):
                if subarr.serial_scans_correct[i]:
                    overscan_img[subarr.section] += np.mean(self.ccd.data[serial])
                    break

            # for i,serial in enumerate(subarr.serial_scans):
            #     log.debug("Apply serial %i correction: %s" % (i, subarr.serial_scans_correct[i]))
            #     mask = np.zeros_like(self.ccd.data[serial]) == 0
            #     if subarr.serial_scans_correct[i]:
            #         for iter in range(niter):
            #             mean = np.mean(self.ccd.data[serial][mask])
            #             std = np.std(self.ccd.data[serial][mask])
            #             mask = np.bitwise_and(self.ccd.data[serial] > mean-3.*std,
            #                                   self.ccd.data[serial] < mean+3.*std)
            #             log.debug('[iter %03i]: nreject = %i mean = %.2f std = %.2f' % (iter,
            #                                                                             int(np.sum(np.bitwise_not(mask))),
            #                                                                             mean,
            #                                                                             std))
            #         overscan = np.zeros(self.ccd.data[serial].shape[0])
            #         for iii in range(self.ccd.data[serial].shape[0]):
            #             mask = np.zeros_like(self.ccd.data[serial][iii]) == 0
            #             mean = np.mean(self.ccd.data[serial][iii])
            #             std = np.std(self.ccd.data[serial][iii])
            #
            #             for iter in range(niter):
            #                 mean = np.mean(self.ccd.data[serial][iii][mask])
            #                 std = np.std(self.ccd.data[serial][iii][mask])
            #                 mask = np.bitwise_and(self.ccd.data[serial][iii] > mean-1.5*std,
            #                                   self.ccd.data[serial][iii] < mean+1.5*std)
            #
            #             row = self.ccd.data[serial][iii]
            #             row.sort()
            #
            #             # overscan[iii]+=np.mean(self.ccd.data[serial][iii])
            #             overscan[iii]+=np.mean(row[8:-8])
            #
            #         py.plot(overscan,'-')
            #
            #         # for iii in range(len(overscan)):
            #         #     overscan[iii]=np.mean(overscan[iii:iii+11])
            #         # py.plot(overscan)
            #         # z = np.polyfit(np.arange(len(overscan)),overscan,8)
            #         # p = np.poly1d(z)
            #         # py.plot(overscan)
            #         # py.plot(p(np.arange(len(overscan))))
            #         # log.info('Std: %.3f' % (np.std(overscan - p(np.arange(len(overscan))))))
            #         # py.show()
            #     scan_level[i] = np.mean(self.ccd.data[serial][mask])
            #     scan_mask[i] = subarr.serial_scans_correct[i]
            #     if subarr.serial_scans_correct[i]:
            #         overscan_img[serial] += scan_level[i] #self.ccd.data[serial]
            #         # overscan/=np.mean(overscan)
            #     #     for iii in range(len(overscan)):
            #     #         serial_overscan_img[subarr.section][iii] += (overscan[iii]-np.mean(overscan[iii]))
            #     # break
            # py.show()
            # for i,parallel in enumerate(subarr.parallel_scans):
            #     log.debug("Apply parallel %i correction: %s" % (i, subarr.parallel_scans_correct[i]))
            #     mask = np.zeros_like(self.ccd.data[parallel]) == 0
            #     if subarr.parallel_scans_correct[i]:
            #         for iter in range(niter):
            #             mean = np.mean(self.ccd.data[parallel][mask])
            #             std = np.std(self.ccd.data[parallel][mask])
            #             mask = np.bitwise_and(self.ccd.data[parallel] > mean-3.*std,
            #                                   self.ccd.data[parallel] < mean+3.*std)
            #             log.debug('[iter %03i]: nreject = %i mean = %.2f std = %.2f' % (iter,
            #                                                                             len(mask)-int(np.sum(mask)),
            #                                                                             mean,
            #                                                                             std))
            #         overscan = np.zeros(self.ccd.data[parallel].shape[1])
            #         for iii in range(self.ccd.data[parallel].shape[1]):
            #             overscan[iii]+=np.mean(self.ccd.data[parallel][:,iii])
            #         # # py.plot(overscan)
            #         # for iii in range(len(overscan)):
            #         #     overscan[iii]=np.mean(overscan[iii:iii+11])
            #         tck = interpolate.splrep(np.arange(len(overscan)),overscan,
            #                                  s = 20)
            #         ynew = interpolate.splev(np.arange(len(overscan)), tck)
            #         # z = np.polyfit(np.arange(len(overscan)),overscan,11)
            #         # p = np.poly1d(z)
            #         # py.plot(overscan)
            #         # py.plot(ynew)
            #         # py.show()
            #
            #     scan_level[len(subarr.serial_scans)+i] = np.median(self.ccd.data[parallel][mask])
            #     scan_mask[len(subarr.serial_scans)+i] = subarr.parallel_scans_correct[i]
            #
            #     if subarr.parallel_scans_correct[i]:
            #         overscan_img[parallel] += scan_level[len(subarr.serial_scans)+i] # self.ccd.data[parallel]
            #         # for iii in range(len(overscan)):
            #         #     parallel_overscan_img[subarr.section][:,iii] += overscan[iii]
            #
            # # print scan_level
            # overscan_img[subarr.section] += np.mean(np.ma.masked_invalid(scan_level[scan_mask]))

        newdata = np.zeros_like(self.ccd.data,dtype=np.float) + self.ccd.data
        # overscan_img = parallel_overscan_img
        newdata -= overscan_img
        self.ccd.data = newdata

    def trim(self):
        '''
        Return trimmed CCDData object.

        :return: CCDData object with trimmed array.
        '''

        log.debug('CCD has %i subarrays in a %i x %i matrix.' % (self._parallelports*self._serialports,
                                                                 self._parallelports,self._serialports))

        subarraysize = [0,0]
        for subarr in self._ccdsections:
            subarraysize[0] = max(subarraysize[0],subarr.parallel_size)
            subarraysize[1] = max(subarraysize[1],subarr.serial_size)
        log.debug('Trimmed CCD will be %i x %i' % (subarraysize[0]*self._parallelports,
                                                   subarraysize[1]*self._serialports))
        newdata = np.zeros((subarraysize[0]*self._parallelports,
                                                   subarraysize[1]*self._serialports))

        for subarr in self._ccdsections:
            newdata[subarraysize[0]*subarr.parallel_index:
                    subarraysize[0]*(subarr.parallel_index+1),
                    subarraysize[1]*subarr.serial_index:
                    subarraysize[1]*(subarr.serial_index+1)] += self.ccd.data[subarr.section]
        newccd = self.ccd
        newccd.data = newdata

        return newccd

if __name__ == '__main__':

    import sys
    from optparse import OptionParser

    parser = OptionParser()

    parser.add_option('-f','--filename',
                      help = 'Input image name.',
                      type='string')

    parser.add_option('-c','--config',
                      help = 'Configuration file.',
                      type='string')

    parser.add_option('-o','--output',
                      help = 'Output name.',
                      type='string')

    opt, args = parser.parse_args(sys.argv)

    logging.basicConfig(format='%(levelname)s:%(asctime)s::%(message)s',
                        level=logging.DEBUG)

    logging.info('Reading in %s' % opt.filename)

    overcorr = OverscanCorr()

    overcorr.read('%s' % opt.filename)

    logging.info('Loading configuration from %s' % opt.config)

    overcorr.loadConfiguration(opt.config)

    # overcorr.show()

    logging.info('Applying overscan...')

    overcorr.overscan()

    logging.info('Trimming...')

    ccdout = overcorr.trim()

    if opt.output is not None:
        logging.info('Saving result to %s...' % opt.output)

        ccdout.write(opt.output)


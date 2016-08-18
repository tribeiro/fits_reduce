#! /usr/bin/env python

'''
Compute image statistics (min,max,mean,std) using numpy.
'''

import sys,os
import numpy as np
from astropy.io import fits as pyfits
import logging
from fits_reduce.util.overscancorr import OverscanCorr

import time

class T80SPreProc(OverscanCorr):

    def __init__(self,*args,**kwargs):
        OverscanCorr.__init__(self,*args,**kwargs)
        self.log = logging.getLogger("t80s_preproc")

    def gain(self):
        gain_img = np.zeros_like(self.ccd.data,dtype=np.float)

        for subarr in self._ccdsections:
            # print scan_level
            gain_img[subarr.section] += subarr.gain

        newdata = np.zeros_like(self.ccd.data,dtype=np.float) + self.ccd.data
        newdata /= gain_img
        self.ccd.data = newdata

    def norm(self):
        newdata = np.zeros_like(self.ccd.data,dtype=np.float) + self.ccd.data
        newdata /= np.median(self.ccd.data)
        self.ccd.data = newdata

    def get_avg(self, filename):
        level = np.zeros((self._parallelports,self._serialports))
        for subarr in self._ccdsections:
            level[subarr.parallel_index][subarr.serial_index] = np.median(self.ccd.data[subarr.section])
        np.save(level,filename)
        return

    def linearize(self,coeffs, saturation = 60e3):
        lin_corr_img = np.zeros_like(self.ccd.data,dtype=np.float64)
        for i in range(0,len(self._ccdsections)):
            subarr = self._ccdsections[i]
            self.log.info('Linearizing region %i x %i...' % (subarr.parallel_index,subarr.serial_index))
            ppol = np.poly1d(coeffs[subarr.parallel_index][subarr.serial_index])
            lin_corr_img[subarr.section] = ppol(self.ccd.data[subarr.section]/32767.)

        mask = np.bitwise_and(lin_corr_img > 0.,
                              self.ccd.data < saturation)

        lin_corr_img[np.bitwise_not(mask)] = 1.

        newdata = self.ccd.data / lin_corr_img

        self.ccd.data = newdata


def main(argv):

    import argparse

    parser = argparse.ArgumentParser(description='Perform basic preprocessing routines on images. This is NOT a '
                                                 'general purpose script, but rather designed to be used with T80CamS '
                                                 'images alone. This script will apply overscan correction, trimm '
                                                 'and linearize images.'
                                                 '\n\n WARNING: Overscan correction still not '
                                                 'optimized! Use it with great care!'
                                                 '\n\n WARNING: Apply bias correction on your images before '
                                                 'preprocessing.')

    parser.add_argument('-f','--filename',
                      help = 'Input image name.',
                      type=str)

    parser.add_argument('-c','--overscan_config',
                      help = 'Configuration file.',
                      type=str)

    parser.add_argument('-l','--linearity_coefficients',
                      help = 'Configuration file.',
                      type=str)

    parser.add_argument('-o','--output',
                      help = 'Output name.',
                      type=str)

    parser.add_argument('--verbose', '-v', action='count')

    args = parser.parse_args(argv[1:])

    logging.basicConfig(format='%(levelname)s:%(asctime)s::%(message)s',
                        level=args.verbose)

    overcorr = T80SPreProc()

    logging.info('Reading in %s' % args.filename)
    overcorr.read('%s' % args.filename)

    logging.info('Loading configuration from %s' % args.overscan_config)
    overcorr.loadConfiguration(args.overscan_config)

    # overcorr.show()

    logging.warning('No overscan corretion will be performed...')
    #
    # overcorr.overscan()

    # logging.info('Gain...')
    #
    # overcorr.gain()

    # logging.info('Normalizing...')
    #
    # overcorr.norm()
    if args.linearity_coefficients is not None:
        logging.info('Linearizing...')
        overcorr.linearize(np.load(os.path.expanduser(args.linearity_coefficients)))

    logging.info('Trimming...')
    ccdout = overcorr.trim()

    if args.output is not None:
        logging.info('Saving result to %s...' % args.output)

        ccdout.write(args.output)
        # overcorr.get_avg(opt.output.replace('.fits','.npy'))

if __name__ == '__main__':
    main(sys.argv)
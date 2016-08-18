#! /usr/bin/env python

'''
Combine a set of input images with median algorithm using numpy
'''

import sys,os
import numpy as np
from astropy.io import fits as pyfits
import logging
import datetime as dt

def main(argv):

    import argparse

    parser = argparse.ArgumentParser(description='Combine images with a median algorith. This is NOT a general '
                                                 'purpose script, but rather designed to be used with T80CamS '
                                                 'images alone.')
    parser.add_argument('files', metavar='F', type=str, nargs='+',
                        help='Input files to combine.')
    parser.add_argument('-o','--output',
                        help = 'Output name.',
                        type=str)
    parser.add_argument('--verbose', '-v', action='count')

    args = parser.parse_args(argv)

    logging.basicConfig(format='%(levelname)s:%(asctime)s::%(message)s',
                        level=args.verbose)

    nimages = len(args.files[1:])
    hdu = pyfits.open(args.files[1])
    sizex, sizey = hdu[0].data.shape
    img_stack = np.zeros((nimages,sizex,sizey),dtype=hdu[0].data.dtype)

    header_comments = ["IMCOMBINE: %s"%dt.datetime.now(),
                       "IMCOMBINE: Combining %i images with median algorithm"%nimages,
                       "IMCOMBINE: IMAGE    MEAN    MIN    MAX    STD"]

    for i in range(nimages):
        logging.info('Reading in %s'%args.files[i+1])
        img_stack[i] += pyfits.getdata(args.files[i+1])
        header_comments.append("IMCOMBINE: %s  %.2f  %.2f  %.sf  %.2f"%(args.files[i+1],
                                                                        np.mean(img_stack[i]),
                                                                        np.min(img_stack[i]),
                                                                        np.max(img_stack[i]),
                                                                        np.std(img_stack[i])))

    logging.info("Processing...")
    output_hdu = pyfits.PrimaryHDU(np.median(img_stack,axis=0))

    for comment in header_comments:
        output_hdu.header["COMMENT"] = comment
    output_hdulist = pyfits.HDUList([output_hdu])
    #hdu[0].data = np.median(img_stack,axis=0)

    logging.info('Saving output to %s'%args.output)
    output_hdulist.writeto(args.output)

    return 0

if __name__ == '__main__':

    main(sys.argv)
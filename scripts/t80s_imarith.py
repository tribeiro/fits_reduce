#! /usr/bin/env python

'''
Perform arithmetics on input images using numpy
'''

import sys,os
import numpy as np
from astropy.io import fits as pyfits
import logging
import datetime as dt
from collections import namedtuple

logging.basicConfig(format='%(levelname)s:%(asctime)s::%(message)s',
                    level=logging.DEBUG)


def main(argv):

    import argparse

    parser = argparse.ArgumentParser(description='Perform arithmetics on images. This is NOT a general '
                                                 'purpose script, but rather designed to be used with T80CamS '
                                                 'images alone.')

    parser.add_argument('--im1',
                      help = 'First image.',
                      type=str)

    parser.add_argument('--im2',
                      help = 'Second image or number.',
                      type=str)

    parser.add_argument('--operator',
                      help = 'A math operator. One of +, -, * or /. Avoid parsing from command line by '
                             'wrapping it with ""',
                      type=str)

    parser.add_argument('-o','--output',
                      help = 'Output name.',
                      type=str)

    args = parser.parse_args(argv[1:])

    logging.debug("Reading image 1: %s" % args.im1)
    img1 = pyfits.open(args.im1)
    if os.path.exists(args.im2):
        logging.debug("Reading image 2: %s" % args.im2)
        img2 = pyfits.open(args.im2)
    else:

        value = namedtuple("value",["data"])
        img2 = [None]
        try:
            img2[0] = value(np.float(args.im2))
            logging.debug("Value: %s" % args.im2)
        except ValueError:
            logging.error("Could not read input image or convert input to float.")
            return -1
        except Exception,e:
            logging.exception(e)
            return -1

    if not args.operator in '+-*/':
        logging.error("Unrecognized operator '%s'. Must be one of +, -, * or /"%(opt.operator))
        return -1
    elif args.operator == '+':
        output_data = img1[0].data + img2[0].data
    elif args.operator == '-':
        output_data = img1[0].data - img2[0].data
    elif args.operator == '*':
        output_data = img1[0].data * img2[0].data
    elif args.operator == '/':
        output_data = img1[0].data / img2[0].data
    else:
        logging.error("Unrecognized operator '%s'. Must be one of +, -, * or /"%(args.operator))
        return -1

    output_hdu = pyfits.PrimaryHDU(header=img1[0].header,
                                   data=output_data)
    header_comments = ["IMARITH: %s"%dt.datetime.now(),
                       "IMARITH: %s %s %s"%(args.im1,args.operator,args.im2)]

    for comment in header_comments:
        output_hdu.header["COMMENT"] = comment
    output_hdulist = pyfits.HDUList([output_hdu])

    logging.info('Saving output to %s'%args.output)
    output_hdulist.writeto(args.output)

    return 0

if __name__ == '__main__':

    main(sys.argv)
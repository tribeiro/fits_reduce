# fits_reduce
This is a python module to reduce astronomical data before doing science stuff with it. If you are wondering what "reduce" mean, maybe this will not be your favorite program, but you can learn it in [Notes on the Essentials of Astronomy Data].

Instalation
===============
 Currently we have not created a cool installation package so, in order to install the module just copy all the files (or "clone" them - in the git mumbo-jumbo) wherever you want (/$HOME/Applications or something like that). It would be useful to add this direction to your $PATH in order to call the program directly from the terminal.

Disclaimer
===============
 This project is under development and despite all things should work, there are incomplete things, such this README file. Visit the project to receive updates and better instructions.
 
CI Status by Travis-CI
===============
[![Build Status](https://travis-ci.org/pablogsal/fits_reduce.svg?branch=master)](https://travis-ci.org/pablogsal/fits_reduce)

Usage
===============

There are two main files that you can use:

1. reducer.py
2. fits_analize.py (Under developing)

If you want to know how to use each file, just call them as:

```python
  python reducer.py -h
```
Which will print the following help:
```python
usage: reducer.py [-h] [-v] [-cosmic] [-no-interaction] [--keys INI_KEYS]
                  [--conf CONF_PATH]
                  dir

 Reduction pipeline to calibrate science images.

        The pipeline needs the following under the "dir":

            - Science images
            - Dark / Bias images
            - Flat images

        The pipeline does the following:

            - Automatic recognition of image cathegory.
            - Automatic date/time classification.
            - Automatic filter and exposure time classification.
            - Automatic reduction of images using these cathegories.
            - Clean cosmic rays.
            - Logging the process.

        The pipeline does NOT do the following:

            - Reduce data using other classification methods that involve
              other variables than exposure time and filters.
            - Pre-procesing routines over data / callibration images.
            - Quality control of provided images and callibrators.
            - Magic.

        The pipeline must be configured for your data using a conf.INi file that must
        be placed in the program folder (standard) or provided using the --conf flag.

        Notes:

        - If the pipeline found more filters for the science images than for the flat
          callibrators it will raise a exception, so be aware of this.

        - The "night" for the pipeline starts at 12:00 PM and ends at 11:59 AM. This
          is because if you take the callibration images after 00:00 and your science
          images after 00:00 then technically you have "two" separate nights if you measure
          nights by the date. By the use of this convention callibration images in the
          same night (real night) will be used together. Beware of this when chechking
          dates in the logger.

        - All the comparisions are performed literal. That means that 'r' and 'R' are different
          filters, and therefore if you have 3 science images with 'r' filter but only flats
          with 'R' filter, this will raise an error (or skip the night).



positional arguments:
  dir               The work directory containing flats, darks an data folders.

optional arguments:
  -h, --help        show this help message and exit
  -v                Prints more info (default: False)
  -cosmic           Clean cosmic rays (default: False)
  -no-interaction   Supress all console output and interaction. This overwrites the -v flag
  --keys INI_KEYS   Use the keys in the conf.INI file (default: STANDARD_KEYS)
  --conf CONF_PATH  The path of the conf.INI file (default: None)
```

Both helps files are auto-explicative, but if you do not understand something, you can ask me anything.

[Notes on the Essentials of Astronomy Data]:http://home.fnal.gov/~neilsen/notebook/astroImagingDataReduction/astroImagingDataReduction.html

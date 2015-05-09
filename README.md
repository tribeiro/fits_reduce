# fits_reduce
This is a python module to reduce astronomical data before doing science stuff with it. If you are wondering what "reduce" mean, maybe this will not be your favourite program, but you can learn it in [Notes on the Essentials of Astronomy Data].

Instalation
===============
 Currently we have not created a cool installation package so, in order to install the module just copy all the files (or "clone" them - in the git mumbo-jumbo) wherever you want (/$HOME/Applications or something like that). It would be usefull to add this direction to your $PATH in order to call the program directly from the terminal.

Usage
===============

Disclaimer: This proyect is under development and despite all things should work, there are incomplete things, such this README file. Visit the proyect to recieve updates and better instructions.

There are two main files that you can use:

1. reduce_data.py
2. fits_analize.py

If you want to know how to use each file, just call them as:

```python
  python fits_analize.py -h
```
Which will print the following help:
```python
usage: reduce_data.py [-h] [--verbose] [--cosmic] [--stats] dir

Reduce science frames with darks and flats.

positional arguments:
  dir         The work directory containing flats, darks an data folders.

optional arguments:
  -h, --help  show this help message and exit
  --verbose   Prints more info (default: False)
  --cosmic    Clean cosmic rays (default: False)
  --stats     Process statistics of files (default: False)
```

In the case of fits_analyze.py, after use

```python
  python fits_analize.py -h
```

you will have the following help text

```python
usage: fits_analize.py [-h] [--verbose] [--r_night] [--r_internight] [--r_out]
                       [--r_bad-nights] [--r_cloud_mea] [--r_cloud_std]
                       [--nodata] [--darks] [--flats]
                       dir

Analize fits images.

positional arguments:
  dir             The work directory containing the images.

optional arguments:
  -h, --help      show this help message and exit
  --verbose       Prints more info (default: False)
  --r_night       Remove the night if the night has been detectes as outlier
                  in general (default: False)
  --r_internight  Remove the INTER-outliers if the night has been detectes as
                  outlier in general(default: False)
  --r_out         Remove all outlayers (default: False)
  --r_bad-nights  Remove all nights with less than 3 objects (default: False)
  --r_cloud_mea   Remove images with clouds using average values(default:
                  False)
  --r_cloud_std   Remove images with clouds using sigma values(default: False)
  --nodata        Do not remove data outlayers (default: False)
  --darks         Remove dark outlayers (default: False)
  --flats         Remove flat outlayers (default: False)

```


Both helps files are auto-explicative, but if you do not understand something, you can ask me anything.

[Notes on the Essentials of Astronomy Data]:http://home.fnal.gov/~neilsen/notebook/astroImagingDataReduction/astroImagingDataReduction.html

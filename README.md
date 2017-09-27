SO2Eval
=======

Very simple command line driven so2 evaluation scripts.

`so2eval.py`
------------

Process so2 image sets (onband/offband) into ppm*m numpy files.
For processing, some things are needed beforehand:

- the calibration constant
- a glob to find clear sky images
- a glob to find dark images
- a glob to find the actual images
- the angle and shift between the two image files in each data set -> `find_alignment.py`
- optional: a region of clear sky in the data files

These can be supplied in the script, as command line options or in
separate config files.

To see all the command line options:

    python so2eval.py --help

To generate a sample config file:

    python so2eval.py --saveconfig sample.conf

To use a config file:

    python so2eval.py --configfile ./path/to/config.conf


`find_alignment.py`
-------------------

Try to find the translation and rotation between two images. Be very
careful with the result; ideally, use images with no or very little so2
and a lot of unmovable background objects (eg. the volcano).

Usage:

    python find_alignment.py --help

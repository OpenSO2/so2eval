# coding: utf-8
from __future__ import print_function
#
# Very simple so2 imagery evaluation script to process "raw" images
# into something useful without requiring manual intervention and
# tweaking.
#
# Background correction (dividing the plume by its background) is
# optional. In the case that both images are of (very) similar exposure,
# background correction is essentially a no-op and can be omited. This
# saves a bit of time and avoids having to fiend a plume-free field in
# the plume images. If you want to be on the save side, use background
# correction.
#
# Beware: it is assumed that the dark images are taken with the same
# exposure time as the payload images.
#
#
# Timestamps
# ----------
# Determining the exact timestamp for the measurements is implemented by
# parsing the filenames using grouped regular expressions containing
# year, month, day, hour, second and millisecond, assuming the these
# values would usually appear in the filename.
#
# Examples:
#
# datepattern = .*(?P<year>\w{4})_(?P<month>\w{2})_(?P<day>\w{2})-(?P<hour>\w{2})_(?P<minute>\w{2})_(?P<second>\w{2})_(?P<millisecond>\w{3})
# testing_2017_06_08-12_19_44_091_cam_bot.png
#
# datepattern = .*(?P<year>\w{4})(?P<month>\w{2})(?P<day>\w{2})_(?P<hour>\w{2})(?P<minute>\w{2})(?P<second>\w{2})_(?P<millisecond>\w{3})
# 20170920_170218_232_M_B.tif
#
#
# Configuration
# -------------
# Configuration will be read in three steps (overriding order)
# - from internal presets in this file
# - from config file if found
# - from command line options
#
# Run with --help to get a description of all config values. Command
# line options can be directly used in a INI style config file. Run
# with --saveconfig to generate a configfile with default values.
#
import numpy as np
from scipy.misc import imread
import matplotlib.pyplot as plt
import glob
import cv2
import argparse
from localconfig import config
import sys
import os
import ast
from modules.strtodate import strtodate

# define all config options
configurations = {
	'configfile': {"default": None, "type": str,
		"help": 'Specify config file.'},
	"use_bg_correction": {"default": True, "type": str,
		"help": "Flag if background correction should be done. If set, plume_free_field must also be set."},
	"roi": {"default": '[0, -1, 0, -1]', "type": str,
		"help": "The region of interest in which the files are evaluated. The rest will be cropped. Form: [top, bot, left, right] in px.",},
	"plume_free_field": {"default": '[340, 620, 1088, 1300]', "type": str,
		"help": "If background correction is used, this part of the images will be used for evaluation. Relative to the roi. Form [top, bot, left, right] in px."},
	"calib": {"default": 1, "type": float,
		"help": "Calibration constant to convert apparent absorption to ppm*m"},
	"glob_dark_onband": {"default": "", "type": str,
		"help": "Pattern to find dark onband images."},
	"glob_dark_offband": {"default": "", "type": str,
		"help": "Pattern to find dark offband images."},
	"glob_files_onband": {"default": "", "type": str,
		"help": "Pattern to find onband images."},
	"glob_files_offband": {"default": "", "type": str,
		"help": "Pattern to find dark offband images."},
	"glob_bg_onband": {"default": "", "type": str,
		"help": "Pattern to find background onband images."},
	"glob_bg_offband": {"default": "", "type": str,
		"help": "Pattern to find background onband images."},
	"outdir": {"default": "out/", "type": str,
		"help": "Folder where output files will be saved. Will be created if necessary."},
	"angle": {"default": 0, "type": float,
		"help": "Rotation between the two images in px."},
	"moveleft": {"default": 0, "type": int,
		"help": "Left offset between the two images in px."},
	"movetop": {"default": 0, "type": int,
		"help": "Right offset between the two images in px."},
	"datepattern": {"default": "(?P<year>\w{4})(?P<month>\w{2})(?P<day>\w{2})_(?P<hour>\w{2})(?P<minute>\w{2})(?P<second>\w{2})_(?P<millisecond>\w{3})", "type": str,
		"help": "Grouped Regexp to parse the timestamp from the filenames."},
	"rotate": {"default": 0, "type": str,
		"help": "More often than not, images in the field are rotated or upside down. This will correct that (in degrees)."},
	"saveconfig": {"default": False, "type": str,
		"help": "Save the current config to a file, eg. to get started."},
}
defaults = {k for k in configurations}
defaults = {k: configurations[k]["default"] for k in defaults}

# parse configfile and overwrite defaults
# do a quick and dirty scan to find the command line option configfile
configfile = configurations["configfile"]["default"]
try:
	i = sys.argv.index("--configfile")
	if i != -1:
		configfile = sys.argv[i + 1]
except ValueError:
	# not found; never mind, just use the defaults
	pass

if configfile:
	config.read(configfile)
	defaults.update(dict(config.items("Defaults")))

# parse command line options and override defaults and configfile
parser = argparse.ArgumentParser(description='Preprocess SO2 images to ppm*m numpy files')
parser.set_defaults(**defaults)

for arg in defaults:
	parser.add_argument('--' + arg, dest=arg, help=configurations[arg]["help"] + " Default: " + str(configurations[arg]["default"]), type=configurations[arg]["type"])

conf = parser.parse_args()

# fix lists
conf.plume_free_field = ast.literal_eval(conf.plume_free_field)
conf.roi = ast.literal_eval(conf.roi)

#
# Special option: save a new config file (for example, to get started)
#
if conf.saveconfig:
	for c in vars(conf):
		if(c != "saveconfig" and c != "configfile"):
			config.set("Defaults", c, repr(getattr(conf, c)), comment=configurations[c]["help"])
	config.save(conf.saveconfig)
	exit(0)

# try to create the output folder
if not os.path.exists(conf.outdir):
	os.makedirs(conf.outdir)
	os.makedirs(conf.outdir + "/figures")
	os.makedirs(conf.outdir + "/data")


#
# start the actual work
#

#
# get dark image (mean images if more than one)
#
darkonband = glob.glob(conf.glob_dark_onband)
darkoffband = glob.glob(conf.glob_dark_offband)
darkonband = [imread(f) for f in darkonband]
darkoffband = [imread(f) for f in darkoffband]
darkonband = np.mean(darkonband, axis=0)
darkoffband = np.mean(darkoffband, axis=0)

#
# get scaled background image to correct image vignette effect
#
bgonband = glob.glob(conf.glob_bg_onband)
bgoffband = glob.glob(conf.glob_bg_offband)
bgoffband = [imread(f) - darkoffband for f in bgoffband]
bgonband = [imread(f) - darkonband for f in bgonband]
meanbgoffband = np.mean(bgoffband, axis=0)
meanbgonband = np.mean(bgonband, axis=0)
scaledbgonband = meanbgonband / np.max(meanbgonband)
scaledbgoffband = meanbgoffband / np.max(meanbgoffband)

#
# get all payload files and correct for dark image
#
filesonband = sorted(glob.glob(conf.glob_files_onband))
filesoffband = sorted(glob.glob(conf.glob_files_offband))

#
# process all payload images
#
fig, ax = plt.subplots()
for f in zip(filesonband, filesoffband):
	print("process", " and ".join(f))

	# get timestamp from file set
	timestamp = strtodate(conf.datepattern, f[0])
	conf.timestamp = timestamp

	# read image
	onband = np.array(imread(f[0]), dtype=np.float64)
	offband = np.array(imread(f[1]), dtype=np.float64)

	# remove dark image
	onband -= darkonband
	offband -= darkoffband

	# scale by background -> remove vignette
	onband /= scaledbgonband
	offband /= scaledbgoffband

	#
	# correct light dilution
	#
	pass  # todo

	#
	# align images
	#
	h, w = onband.shape
	# rotate
	rot_matrix = cv2.getRotationMatrix2D((h / 2, w / 2), conf.angle, 1)
	onband = cv2.warpAffine(onband, rot_matrix, (w, h))
	# translate
	translation_matrix = np.float32([[1, 0, conf.moveleft], [0, 1, conf.movetop]])
	onband = cv2.warpAffine(onband, translation_matrix, (w, h))

	#
	# calculate the absorbance
	#
	if conf.use_bg_correction:
		pf = conf.plume_free_field
		bgonband = np.mean(onband[pf[0]:pf[1], pf[2]:pf[3]])
		bgoffband = np.mean(offband[pf[0]:pf[1], pf[2]:pf[3]])
		A = - np.log10(onband / bgonband) + np.log10(offband / bgoffband)
	else:
		A = - np.log10(onband / offband)
	A[A > 2000] = 0  # remove inf due to warping where the images don't overlap
	# A[A < .05] = 0  # remove noise in output

	#
	# apply calibration
	#
	calibrated = A / conf.calib
	roi = conf.roi
	# remove edges for display (very high false signal fucks with color bar)
	calibrated = calibrated[roi[0]: roi[1], roi[2]:roi[3]]

	# rotate
	rot_matrix = cv2.getRotationMatrix2D((h / 2, w / 2), conf.rotate, 1)
	calibrated = cv2.warpAffine(calibrated, rot_matrix, (w, h))

	#
	# save to new output file
	#
	plt.clf()
	plt.cla()
	fig.suptitle('SO2 path concentration (ppm m)')
	cax = plt.imshow(calibrated, cmap=plt.get_cmap("hot"))
	fig.colorbar(cax)

	filename = "{:%Y-%m-%d_%H-%M-%S-%f}".format(timestamp)
	fig.savefig(conf.outdir + "/figures/" + filename + ".png", dpi=100)
	# np.save(conf.outdir + "/data/"  + filename, calibrated)
	f = conf.outdir + "/data/" + filename
	np.savez_compressed(f, data=calibrated, config=conf)
	print("saved", filename)

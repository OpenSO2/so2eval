# coding: utf-8
from __future__ import print_function
#
# Very simple so2 imagery evaluation script
#
# TODO: compensate for light dillution
# TODO: substract background (cite!)
# TODO: check exposure time
# TODO: create out folder
#
import numpy as np
from scipy.misc import imread
import matplotlib.pyplot as plt
import glob
import cv2
import argparse
from localconfig import config
import sys
import ast

#
# Configuration will be read in three steps (overriding order)
# - from internal presets in this file
# - from config file if found
# - from command line options
#

# define all config options
configurations = {
	'configfile': { "default": "config.config", "help": 'Specify config file', "type": str},
	"use_bg_correction": { "default": True, "help": "", "type": str},
	"roi": { "default": '[0, 940, 100, 1300]', "help": "", "type": str}, # top, bot, left, right
	"plume_free_field": { "default": '[340, 620, 1088, 1300]', "help": "", "type": str}, # top, bot, left, right
	"calib": { "default": 0.171371/730, "help": "", "type": float},
	"glob_dark_onband": { "default": "", "help": "", "type": str},
	"glob_dark_offband": { "default": "", "help": "", "type": str},
	"glob_files_onband": { "default": "", "help": "", "type": str},
	"glob_files_offband": { "default": "", "help": "", "type": str},
	"glob_bg_onband": { "default": "", "help": "", "type": str},
	"glob_bg_offband": { "default": "", "help": "", "type": str},
	"outdir": { "default": "out/", "help": "", "type": str},
	"angle": { "default": -1, "help": "rotation between the two images", "type": float},
	"moveleft": { "default": -1, "help": "left offset between the two images", "type": int},
	"movetop": { "default": -35, "help": "right offset between the two images", "type": int},
	"saveconfig": { "default": False, "help": "", "type": str},
}
defaults = {k for k in configurations}
defaults = {k: configurations[k]["default"] for k in defaults}

# parse configfile and overwrite defaults
# do a quick and dirty scan to find the command line option configfile
configfile = configurations["configfile"]["default"]
try:
	i = sys.argv.index("--configfile")
	if i != -1:
		configfile =  sys.argv[i+1]
except ValueError:
	pass

if configfile:
	config.read(configfile)
	defaults.update( dict(config.items("Defaults")) )

# parse command line options and override defaults and configfile
parser = argparse.ArgumentParser(description='Preprocess SO2 images to ppm*m numpy files')
parser.set_defaults(**defaults)

for arg in defaults:
	parser.add_argument('--'+arg, dest=arg, help=configurations[arg]["help"], type=configurations[arg]["type"])

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



#
# start the actual work
#



#
# get dark image (mean images if more than one)
#
darkonband = glob.glob(conf.glob_dark_onband)
darkoffband = glob.glob(conf.glob_dark_offband)
darkonband = [ imread(f) for f in darkonband ]
darkoffband = [ imread(f) for f in darkoffband ]
darkonband = np.mean(darkonband, axis=0)
darkoffband = np.mean(darkoffband, axis=0)

#
# get scaled background image to correct image vignette effect
#
bgonband = glob.glob(conf.glob_bg_onband)
bgoffband = glob.glob(conf.glob_bg_offband)
bgoffband = [ imread(f) - darkoffband for f in bgoffband ]
bgonband = [ imread(f) - darkonband for f in bgonband ]
meanbgoffband = np.mean(bgoffband, axis=0)
meanbgonband = np.mean(bgonband, axis=0)
scaledbgonband = meanbgonband / np.max(meanbgonband)
scaledbgoffband = meanbgoffband / np.max(meanbgoffband)

#
# get all payload files and correct for dark image
#
filesonband = sorted( glob.glob(conf.glob_files_onband) )
filesoffband = sorted( glob.glob(conf.glob_files_offband) )

#
# process all payload images
#
fig, ax = plt.subplots()
for f in zip(filesonband, filesoffband):
	print("process", " and ".join(f))

	# read image
	onband = np.array( imread(f[0]), dtype=np.float64 )
	offband = np.array( imread(f[1]), dtype=np.float64 )

	# remove dark image
	onband -= darkonband
	offband -= darkoffband

	# scale by background -> remove vignette
	onband /= scaledbgonband
	offband /= scaledbgoffband

	#
	# correct light dilution
	#
	pass # todo

	#
	# align images
	#
	h, w = onband.shape
	# rotate
	rot_matrix = cv2.getRotationMatrix2D((h/2, w/2), conf.angle, 1)
	onband = cv2.warpAffine(onband, rot_matrix, (w, h));
	# translate
	translation_matrix = np.float32([ [1, 0, conf.moveleft], [0, 1, conf.movetop] ])
	onband = cv2.warpAffine(onband, translation_matrix, (w, h))

	#
	# calculate the absorbance
	#
	if conf.use_bg_correction:
		plume_free_field = conf.plume_free_field
		bgonband = np.mean( onband[plume_free_field[0]:plume_free_field[1], plume_free_field[2]:plume_free_field[3]] )
		bgoffband = np.mean( offband[plume_free_field[0]:plume_free_field[1], plume_free_field[2]:plume_free_field[3]] )
		A = - np.log10(onband / bgonband) + np.log10(offband / bgoffband)
	else:
		A = - np.log10( onband / offband )
	A[A > 2000] = 0 # remove inf due to warping where the images don't overlap
	A[A < .05] = 0 # remove noise in output

	#
	# apply calibration
	#
	calibrated = A / conf.calib
	roi = conf.roi
	calibrated = calibrated[roi[0]: roi[1], roi[2]:roi[3]] # remove edges for display (very high false signal fucks with color bar)

	#
	# save to new output file
	#
	plt.clf()
	plt.cla()
	fig.suptitle('SO2 path concentration (ppm m)')
	cax = plt.imshow(calibrated, cmap=plt.get_cmap("hot"))
	fig.colorbar(cax)
	#~ plt.show()
	# fixup
	filename = f[0].replace("images/", "").replace("_top", "").replace(".png", "")
	fig.savefig(conf.outdir + "/figures/" + filename + ".png", dpi=100)
	np.save(conf.outdir + "/data/"  + filename +  ".npy", calibrated)

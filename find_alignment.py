# coding: utf-8
from __future__ import print_function
#
# Try to find the alignment factors (translation, rotation) between two images
#

import numpy as np
import matplotlib
from scipy.misc import imread
import matplotlib.pyplot as plt
import glob
import cv2
import argparse
import sys
from alignimages import alignimages

parser = argparse.ArgumentParser(description='Find translation and rotation between two images')
parser.add_argument('im1', help="image 1")
parser.add_argument('im2', help="image 2")
conf = parser.parse_args()

im1 = imread(conf.im1, -1)
im2 = imread(conf.im2, -1)

im2, matrix = alignimages(im1, im2)

print("dx: {}px, dy: {}px, alpha: {}°".format(matrix[0,2], matrix[1,2], np.rad2deg(np.arccos(matrix[0,0]))))

fig = plt.figure()
ax1 = plt.imshow(im1, cmap='gray')
ax2 = plt.imshow(im2, cmap='gray', alpha=.5)
plt.show()

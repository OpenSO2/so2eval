# coding: utf-8
"""Align two images.

Try to automatically calculate the warp matrix between two images and align
those images accordingly.
"""
import cv2
import numpy as np


def alignimages(im1, im2):
	"""Automatically align two images."""
	# Find size of image1
	sz = im1.shape

	# Define the motion model
	# warp_mode = cv2.MOTION_TRANSLATION  # translation
	warp_mode = cv2.MOTION_EUCLIDEAN  # translation + rotation
	# warp_mode = cv2.MOTION_AFFINE # translation + rotation + skew

	# Define 2x3 matrix and initialize the matrix to identity
	warp_matrix = np.eye(2, 3, dtype=np.float32)

	# Specify the number of iterations.
	number_of_iterations = 200

	# Specify the threshold of the increment
	# in the correlation coefficient between two iterations
	termination_eps = 1e-10

	# Define termination criteria
	criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
		number_of_iterations, termination_eps)

	# Run the ECC algorithm. The results are stored in warp_matrix.
	# FIXME: use image depth to calc the scaling factor (this assumes 16bit)
	im1_8 = (im1 / 256).astype('uint8')
	im2_8 = (im2 / 256).astype('uint8')
	(_, warp_matrix) = cv2.findTransformECC(im1_8, im2_8, warp_matrix,
		warp_mode, criteria)

	# Use warpAffine for Translation, Euclidean and Affine
	im2_aligned = cv2.warpAffine(im2, warp_matrix, (sz[1], sz[0]),
		flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)

	return im2_aligned, warp_matrix

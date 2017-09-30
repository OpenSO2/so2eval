import numpy
from scipy import interpolate
def interpolate_line_from_img(point_a, point_b, img):
	x1, x2 = point_a
	y1, y2 = point_b

	# construct interpolation function
	x = numpy.arange(img.shape[1])
	y = numpy.arange(img.shape[0])
	f = interpolate.interp2d(x, y, img)

	# extract values on line
	num_points = 100
	xvalues = numpy.linspace(x1, x2, num_points)
	yvalues = numpy.linspace(y1, y2, num_points)
	zvalues = f(xvalues, yvalues)
	return zvalues

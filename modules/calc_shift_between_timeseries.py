"""Calculate the x shift between two series."""
import scipy
import numpy


def calc_shift_between_timeseries(series1, series2):
	"""Calculate the x shift between two series."""
	# compare ffts
	af = scipy.fft(series1)
	bf = scipy.fft(series2)
	c = scipy.ifft(af * scipy.conj(bf))
	timeshift = numpy.argmax(c)
	return timeshift

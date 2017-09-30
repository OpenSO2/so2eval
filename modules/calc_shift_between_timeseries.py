import scipy
def calc_shift_between_timeseries(series1, series2):
	# compare ffts
	af = scipy.fft(series1)
	bf = scipy.fft(series2)
	c = scipy.ifft(af * scipy.conj(bf))
	timeshift = numpy.argmax(c)
	return timeshift

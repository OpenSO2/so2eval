# coding: utf-8
from __future__ import print_function


import datetime
import re
def strtodate(pattern, s):
	regexp = re.compile(pattern)
	r = re.match(regexp, s)
	d = r.groupdict()
	date = datetime.datetime(
		year = int(d["year"]),
		month = int(d["month"]),
		day = int(d["day"]),
		hour = int(d["hour"]),
		minute = int(d["minute"]),
		second = int(d["second"]),
		microsecond = int(d["millisecond"])*1000
	)

	return date


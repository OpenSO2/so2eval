# coding: utf-8
import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from strtodate import strtodate


def test_strtodate():
	pattern = ".*(?P<year>\w{4})_(?P<month>\w{2})_(?P<day>\w{2})-(?P<hour>\w{2})_(?P<minute>\w{2})_(?P<second>\w{2})_(?P<millisecond>\w{3})"
	string = "testing_2017_06_08-12_19_44_091_cam_bot.png"
	date = strtodate(pattern, string)
	assert(date)
	assert(date.year == 2017)
	assert(date.month == 6)
	assert(date.day == 8)
	assert(date.hour == 12)
	assert(date.minute == 19)
	assert(date.second == 44)
	assert(date.microsecond == 91000)

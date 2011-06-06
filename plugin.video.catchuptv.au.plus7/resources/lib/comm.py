import urllib2
import config
import classes
import utils
import re
import datetime
import time

from BeautifulSoup import BeautifulStoneSoup
import simplejson as json

try:
	import xbmc, xbmcgui, xbmcplugin, xbmcaddon
except ImportError:
	pass # for PC debugging

cache = False

def fetch_url(url):
	"""	Simple function that fetches a URL using urllib2.
		An exception is raised if an error (e.g. 404) occurs.
	"""
	print "[Plus7] Fetching URL: %s" % url
	http = urllib2.urlopen(urllib2.Request(url, None))
	return http.read()


def get_index():
	"""	This function pulls in the index, which contains the TV series
	"""
	series_list = []
	data = fetch_url(config.index_url)
	data = data.replace('\n','')
	token = re.findall(r"<!-- Body Content  -->(.*)<!-- //Body Content -->", data)[0]
	token2 = re.findall(r'<div class="bd" id="atoz">(.*)</div>', token)[0]

	urls = re.findall(r'<a href="(.*?)"', token2)
	titles = re.findall(r'alt="(.*?)"', token2)
	imgs = re.findall(r'src="(.*?)\?', token2)

	for i in xrange(len(urls)):
		series = classes.Series()
		series.title = titles[i]
		series.thumbnail = imgs[i]
		series.url = urls[i]
		series_list.append(series)

	return series_list

def get_series(series_id):
	""" 
	"""
	program_list = []
	url = config.series_url % series_id

	data = fetch_url(url)	
	data = data.replace('\n','')

	#title = re.findall(r'<h2>(.*?)</h2>', data)[0]
	programs_data = re.findall(r'<ul id="related-episodes" class="featlist">(.*?)</ul>', data)[0]

	# ['John Safran's Race Relations', 'John Safran's Race Relations']
	titles = re.findall(r'<span class="title">(.*?)</span>', programs_data)
	print "Titles: %s" % titles

	# ['Episode desc', 'Episode desc']
	descs = re.findall(r'<p>(.*?)</p>', programs_data)
	#print "Episode Desc: %s" % descs

	# [' Wed 14 July, series 4 episode 2', ' Wed 14 July, series 4 episode 1']
	subtitles = re.findall(r'<span class="subtitle">(.*?)</span>', programs_data)
	#print "Subtitles: %s" % subtitles

	# ['http://l.yimg.com/ea/img/-/100714/0714_city_homicide_ep56v2_sml-163qgka.jpg', 'http://l.yimg.com/ea/img/-/100714/0714_city_homicide_ep55v2_sml-163qgjl.jpg']	
	thumbs = re.findall(r'src="(.*?)\?', programs_data)
	#print "Thumbnails: %s" % thumbs

	# ['/plus7/city-homicide/-/watch/7583800/wed-14-july-series-4-episode-2/', '/plus7/city-homicide/-/watch/7583794/wed-14-july-series-4-episode-1/']
	urls = re.findall(r'<h3><a href="(.*?)">', programs_data)
	#print "URLs: %s" % urls

	num_episodes = len(urls)

	#print "Number of Episodes: %d" % num_episodes

	for i in xrange(num_episodes):
		program = classes.Program()
		program.title = titles[i]
		program.description = descs[i]
		program.thumbnail = thumbs[i]
		program.url_path = urls[i]

		# season 4 episode 2
		program.episode = subtitles[i].split(',')[-1].lstrip(" ").rstrip(" ")
		#print "Episode: %s" % program.episode

		#date_string = token6[i].split(',')[0].lstrip(" ").rstrip(" ")
		#print "date_string: %s " % date_string
		#date = "%s %s" % (date_string, program.get_year())
		#print "date: %s"
		#timestamp = time.mktime(time.strptime(date, '%a %d %b %Y'))
		#print "timestamp: %s" % timestamp
		#program.date = datetime.date.fromtimestamp(timestamp)

		program_list.append(program)
		print program.get_xbmc_list_item()
		print program.make_xbmc_url()

	return program_list


def get_program(path):

	# This stuff needs to go into parser
	index = fetch_url("http://au.tv.yahoo.com%s" % path) 

	program = classes.Program()

	program.id = re.findall("vid : '(.*?)'", index)[0]
	print "Program ID: %s" % program.id

	program.title = re.findall("<h1>(.*?)</h1>", index)[0]
	print "Program Title: %s" % program.title

	program.category = re.findall("Genre: <strong>(.*?)</strong>", index)[0]
	program.rating = re.findall("Classified: <strong>(.*?)</strong>", index)[0]

	# Get the URL, but split it from the '?', to get the high-res image
	program.thumbnail = re.findall('<img class="listimg" src="(.*?)" alt', index)[0].split("?")[0]

	# Get metadata
	url = "http://cosmos.bcst.yahoo.com/rest/v2/pops;id=%s;lmsoverride=1" % program.id
	index = fetch_url(url)

	program.episode_title = re.findall("<title><!\[CDATA\[(.*?)\]\]></title>", index)[0].split(": ")[1]
	print "Episode title: %s" % program.episode_title

	program.description = re.findall("<description><!\[CDATA\[(.*?)\]\]></description>", index)[0]
	print "Episiode description: %s" % program.description

	program.thumbnail = re.findall('<media:content medium="image" url="(.*?)" name=', index)[0]

	# Parsing the date is a nightmare
	date_string = re.findall("<media:pubStart><!\[CDATA\[(.*?)\]\]></media:pubStart>", index)[0]
	date_parts = date_string.split()
	date_without_tz = " ".join(date_parts[:-1])
	timestamp = time.mktime(time.strptime(date_without_tz, '%m/%d/%Y %I:%M:%S %p'))
	program.date = datetime.date.fromtimestamp(timestamp)

	# Get stream
	#url = "http://cosmos.bcst.yahoo.com/rest/v2/pops;id=%s;lmsoverride=1;element=stream;bw=1200" % program.id
	#index = fetch_url(url)

	#program.rtmp_host = re.findall('url="(.*?)"', index)[0]
	#program.rtmp_path = re.findall('path="(.*?)"', index)[0]

	#duration = re.findall('duration="(.*?)"', index)[0]
	#print "Duration: %s" % duration
	#program.duration = int(duration)
	#print "Parsed duration: %d" % program.duration

	return program

def get_stream(program_id):

	# Get stream
	url = "http://cosmos.bcst.yahoo.com/rest/v2/pops;id=%s;lmsoverride=1;element=stream;bw=1200" % program_id
	index = fetch_url(url)
	
	rtmp_host = re.findall('url="(.*?)"', index)[0]
	rtmp_path = re.findall('path="(.*?)"', index)[0]

	return { "rtmp_host": rtmp_host, "rtmp_path": rtmp_path }

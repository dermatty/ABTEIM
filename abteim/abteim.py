#!/home/stephan/.virtualenvs/uptime/bin/python

import requests, time, sys, configparser, json, platform, datetime
from urllib3.exceptions import InsecureRequestWarning
from os.path import expanduser
import fridagram as fg
import logging
import logging.handlers

# emojis from https://apps.timwhitlock.info/emoji/tables/unicode
EM_DOWN = "\U0001F621"
EM_UP = "\U00002705"   # WHITE HEAVY CHECK MARK

HOSTNAME = platform.uname().node

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def make_request(url, max_retries=5, retry_delay=3, timeout=5):
	retries = 0
	while retries < max_retries:
		try:
				response = requests.get(url, verify=False, timeout=timeout)
				# Check if the response was successful
				if response.status_code == 200:
					return "200"
		except Exception as e:
				pass
		retries += 1
		time.sleep(retry_delay)
	return "404"

def convert_secs(seconds):
	seconds0 = seconds
	seconds = seconds % (24 * 3600)
	hour = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60

	rs = ""
	if hour > 0:
		hh = str(hour)
		if hour > 1:
			rs = hh + " hours"
		else:
			rs = hh + " hour"
	if (minutes > 0 or seconds > 0) and rs != "":
		rs = rs + ", "
	if minutes > 0:
		mm = str(minutes)
		if minutes > 1:
			rs = rs + mm + " minutes"
		else:
			rs = rs + mm + " minute"
	if len(rs) > 2:
		rrs = rs[-2]
	else:
		rrs = ""
	if seconds > 0 and "," not in rrs and rs != "":
		#print(str(seconds) + "/" + str(rrs) + "/" + str(rs))
		rs = rs + ", "
	if seconds > 0:
		ss = str(seconds)
		if seconds > 1:
			rs = rs + ss + " seconds"
		else:
			rs = rs + ss + " second"
	return rs

statuses = {
    200: "Website Available",
    301: "Permanent Redirect",
    302: "Temporary Redirect",
    404: "Not Found",
    500: "Internal Server Error",
    503: "Service Unavailable"
}

def start():
	userhome = expanduser("~")
	maindir = userhome + "/.abteim/"
	statusfile = maindir + "webstatus.txt"
	motd = "ABTEIM website monitoring now on " + str(HOSTNAME) +" ..."

	# Init Logger
	logger = logging.getLogger("abt")
	logger.setLevel(logging.DEBUG)
	fh = logging.FileHandler(maindir + "uptime.log", mode="w")
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	fh.setFormatter(formatter)
	logger.addHandler(fh)
	logger.info(motd)

	cfg_file = maindir + "config"
	# read interval & weburls config
	try:
		cfg = configparser.ConfigParser()
		cfg.read(cfg_file)

		interval = int(cfg["GENERAL"]["interval"])
		logger.info("Set query interval to " + str(interval) + " seconds!")

		max_retries = int(cfg["GENERAL"]["max_retries"])
		logger.info("Set max_retries to " + str(max_retries) + "!")

		retry_delay = int(cfg["GENERAL"]["retry_delay"])
		logger.info("Set retry_delay to " + str(retry_delay) + "!")

		timeout = int(cfg["GENERAL"]["timeout"])
		logger.info("Set timeout to " + str(timeout) + "!")

		weburls_values = cfg["WEBURLS"]["weburls"]
		weburls = json.loads(weburls_values)
		logger.info("Weburls are: " + str(weburls))


	except Exception as e:
		print(str(e))
		logger.error(str(e))
		sys.exit()
	website_url = []
	httpsstr = "https://"
	for w in weburls:
		if httpsstr not in w:
				w = httpsstr + w
		website_url.append([w, "999", 0.0])
	logger.info("website_url is: " + str(website_url))

	# Init telegram/fridgram
	try:
		ret, cfg0 = fg.read_config(cfg_file, logger)
		if not ret:
				raise Exception(cfg0)
	except Exception as e:
		logger.error(str(e))
		sys.exit()
	fg.send_message(cfg0.token, cfg0.chatids, motd)
	logger.info("Telegram motd sent!")

	while True:
		status_code = "200"
		for i, (url, old_status_code, downtimestart) in enumerate(website_url):
			status_code = make_request(url, max_retries=max_retries, retry_delay=retry_delay, timeout=timeout)
			#try:
			#       web_response = requests.get(url, verify=False, timeout=10)
			#       status_code = str(web_response.status_code)
			#except Exception as e:
			#       logger.error(str(e))
			#       status_code = "404"
			url0 = url.replace("https://", "")
			url0 = url0.replace("http://", "")
			logger.debug(url0 + ": " + status_code + "(was: " + old_status_code + ")")
			if status_code != old_status_code:
				if int(status_code) == 200:
					if downtimestart == 0.0:
							dtstr = ""
					else:
							dt = int(round(time.time() - downtimestart, 0))
							dtstr =  "It was down for " + convert_secs(dt) + "."
					status_answer = url0 + " is UP! " + dtstr
					logger.info(status_answer)
					status_answer = EM_UP + " " + status_answer
					newdts = 0.0
				else:
					status_answer = url0 + " is DOWN!"
					logger.warning(status_answer)
					status_answer = EM_DOWN + " " + status_answer
					newdts = time.time()

				website_url[i][1] = status_code
				website_url[i][2] = newdts
				r, ok = fg.send_message(cfg0.token, cfg0.chatids, status_answer)
			time.sleep(2)

		# write to statusfile
		try:
			with open(statusfile, "w") as f:
				for (url, old_status_code, _) in website_url:
					url0 = url.replace("https://", "")
					url0 = url0.replace("http://", "")
					tstr = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S / ")
					s0 = tstr + url0 + " / "
					if int(status_code) == 200:
							s0 += "UP"
					else:
							s0 += "DOWN"
					s0 += "\n"
					f.write(s0)
		except Exception as e:
				logger.error(str(e))
		time.sleep(interval)
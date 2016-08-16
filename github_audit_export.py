#!/usr/bin/env python


import mechanize
import cookielib
import json
import time 
import argparse
import sys
import requests
import os



if os.environ.has_key("log_uri"):
	SUMO_URI = os.environ['log_uri']
else:
	print 'Evniroment variable log_uri not found'
	sys.exit


os.environ['HOME']

def main():

	parser = argparse.ArgumentParser()

	parser.add_argument('-username', help='Github username');
	parser.add_argument('-password', help='Github password');
	parser.add_argument('-file', help='Fetches username and password from json formatted config.json file. Does not take a value (boolean). ', action='store_true');
	parser.add_argument('-otp', help='OTP string if Github 2FA is enabled');
	parser.add_argument('-org', help='Github Org name');

	args = parser.parse_args()
		
	if (not (args.username and args.password) and not args.file) or not args.org: #or not args.otp:  <-- removing OTP requirement
		print 'Missing arguments. Try -h for help'
		sys.exit()
	elif args.file:
		try:
			config_file = open('config.json', 'r')
			configs = config_file.read()
		except Exception, e:
			print "Unable to open config.json file."
			raise e
		else:
			config_dict=json.loads(configs)
			args.username = config_dict['username']
			args.password = config_dict['password']

	try:
		placeholder = open('placeholder.state', 'r')
		timestamp = placeholder.read()
	except Exception, e:
		print e
		print 'Placeholder.state file not found. Triggering first-time export. All github audit logs will be exported.'
		if raw_input("Continue (y/n)? :") != 'y':
			sys.exit()
		else:
			timestamp_int = 0  #Seting timestamp to 0. All logs will be exported.
			pass
	else:
		try:
			if timestamp != '':
				timestamp_int = int(timestamp)
			print 'Timestamp found from previous run in placeholder.state: ' + timestamp
			placeholder.close()
		except Exception, e:
			print 'Placeholder.state is empty OR timestamp doesn\'t exist as a string'
			if raw_input("Continue (y/n)? :") != 'y':
				sys.exit()
			else:
				print 'Seting timestamp to 0. All logs will be exported.'
				timestamp_int = 0
			pass
		



	#-----------------------------------Start fake browser setup--------------------------------------------------
	#Pulled from http://stockrt.github.io/p/emulating-a-browser-in-python-with-mechanize/

	# Browser
	br = mechanize.Browser()

	# Cookie Jar
	cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)

	# Browser options
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)

	# Follows refresh 0 but not hangs on refresh > 0
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

	# Want debugging messages?
	#br.set_debug_http(True)
	#br.set_debug_redirects(True)
	#br.set_debug_responses(True)

	# User-Agent (this is cheating, ok?)
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]


	#-----------------------------------End of fake browser setup--------------------------------------------------




	r = br.open('http://github.com')
	r = br.open('https://github.com/login')

	#for f in br.forms():
	#	print f

	#Initial Login
	br.select_form(nr=1)
	br.form['login']=args.username
	br.form['password']=args.password
	br.submit()

	print 'Completed initial login request.'

	#Two-factor auth
	if not args.otp:
		print "Not performing OTP auth"
	else:
		br.select_form(nr=1)
		br.form['otp']=args.otp
		br.submit()

	print 'Completed 2FA login request.'

	#Browse to audit url
	r = br.open('https://github.com/organizations/' + args.org + '/settings/audit-log')
	#print br.response().read()


	#Export audit logs in Json
	br.select_form(nr=4)
	br.form['export_format']=['json']
	br.submit()

	print 'Completed audit log export request.'
	print 'Export Response: ' + br.response().read()
	#print br.response().read()

	#The response contains a 
	#job_url: This URL provides the status of the export job that is running on the github back-end. The audit log cannot be fetched until this job has run successfully.
	#export_url: This is the download URL for the audit log.
	audit_export_response = json.loads(br.response().read())

	print 'Parsed export log job_url.'


	print 'Checking job status.'

	#Check the status of the job
	while True:
		#Parse the response
		try:

			r = br.open(str(audit_export_response['job_url']))
			print 'Response: ' + br.response().read()
			print "Response code: " + str(r.code)

			audit_export_job_status = json.loads(br.response().read())

			#Fetch the audit log if the job completed successfully
			if str(audit_export_job_status['job']['state']) == 'success': #or r.code == '200':
				print 'Export job completed. Waiting 5 seconds to allow for download link creation.'
				print str(audit_export_response['export_url'])
				time.sleep(5)
				r = br.open(str(audit_export_response['export_url']))
				break
			print 'Waiting for completion. State: ' + str(audit_export_job_status['job']['state']) 
		  	time.sleep(1)

		except Exception, e:
			#Not sure why we get a 400 here but, it looks like it occurs when the job has completed successfully (without returnin a success the job status)
			print e
			break

	print 'Sleeping for 5, then making download request for the audit log export-url.'

	time.sleep(5)
	r = br.open(str(audit_export_response['export_url']))
	#print br.response().read() #prints the entire returned json object, which contains the full audit log

	log_export =  json.loads(br.response().read())

	#print str(log_export[0])

	
	log_export_parsed = str() #This is what we're going to send to the sumo function

	#Go through the dict and only export logs since the previously  marked 
	for log in log_export:
		if log['created_at'] >  timestamp_int: #This condition is always true if there is no placeholder.state, because we set timestamp_int to 0
			log_export_parsed = log_export_parsed + json.dumps(log) + "\n" #We parse it like this because the Sumologic ingestion default is one log message per line
			#log_export_parsed.add(log)
	print log_export_parsed

	try:
		print 'Shipping selected logs to sumologic.'
		shipit2sumo(log_export_parsed)
		#print json.dumps(log_export_parsed)
	except Exception, e:
		print e
	else:
		#shipit2sumo did not die a horrible death
		#Store the last timestamp in the state file. This way we don't export it and anything before it to any external log destination again.
		try:
			placeholder = open('placeholder.state', 'w')
			placeholder.write(json.dumps(log_export[-1]['created_at']))
			placeholder.close()
		except Exception, e:
			print e
			pass


def shipit2sumo(logs): #Sends the contents of the logs variable to sumo
	headers = {'content-type': 'application/json; charset=UTF-8', 'accept': 'application/json'}
	requests.post(SUMO_URI, data=logs, headers=headers)

if __name__ == '__main__':
	main()


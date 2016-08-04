import mechanize
import cookielib
import json
import time 
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

#Set organization name
org = ''


r = br.open('http://github.com')
r = br.open('https://github.com/login')

#for f in br.forms():
#	print f

br.select_form(nr=1)
br.form['login']='<username>'
br.form['password']='<password>'

br.select_form(nr=1)
br.form['otp']='<OTP>'
br.submit()

r = br.open('https://github.com/organizations/' + org + '/settings/audit-log')
#print br.response().read()

br.select_form(nr=4)
br.form['export_format']=['0','json']
br.submit()

#print br.response().read()

#The response contains a 
#job_url: This URL provides the status of the export job that is running on the github back-end. The audit log cannot be fetched until this job has run successfully.
#export_url: This is the download URL for the audit log.
audit_export_response = json.loads(br.response().read())

#Check the status of the job
r = br.open(str(audit_export_response['job_url']))

while True:
	#Parse the response
	audit_export_job_status = json.loads(br.response().read())
	#Fetch the audit log if the job completed successfully
	if audit_export_job_status['state'] == 'success':
		r = br.open(str(theresponse['export_url']))
		break
  	time.sleep(5)
  
  

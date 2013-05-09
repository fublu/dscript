#! /usr/bin/python
# To create the JSON object manually, run the runloop file
# Permissions must be set correctly, all files will be created with www-data permissions,
# so directories need to writable by www-data

import web
import sys
import time
import json
import os
from web import form

#Need to set the absolute path for apache, otherwise it will not find the templates
root = os.path.dirname(__file__)
render = web.template.render(os.path.join(root, 'templates'))
cache=False #Apache might send cached site backs otherwise

urls = (
	'/', 'index',
	'/runscript', 'runscript',
	'/counter', 'counter'
	#'/test', 'test'
)

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc() #when using mod_wsgi

class index:
	def GET(self):
		return render.index()
		
class runscript:
	def GET(self):
	
		#Getting Input Value:
		getInput = web.input(macdomain="5/0/4") ##5/0/4 is the default value
		
		#Checking if the file exists
		#If the file exists it checks if the script is already running (1)
		#If so a 1 is returned and the calling website refuses to run the script (handled in JS)
		#This is necessary so that two processes don't write into the same file
		#If the file should not exist, the script will be run, which also will create it
		try:
			fh_status = open('/var/www/dscript/static/status')
			data = json.loads(fh_status.read())
			if data['RUN_STATE'] is 1:
				return (1)
			else:
				os.system("/var/www/dscript/dscript.py " + getInput.macdomain + " &")
		except:
			os.system("/var/www/dscript/dscript.py " + getInput.macdomain + " &")
			#The status file will be opened by the dscript.py

#This class returns the status using json (CM_TOTAL, CM_COUNT, CM_ONLINE, RUN_STATE)	
class counter:
	def GET(self):
		fh_status = open('/var/www/dscript/static/status')
		data = json.loads(fh_status.read())
		fh_status.close()
		web.header('Content-Type', 'application/json')
		return json.dumps(data)

"""
# For testing
class test:
	def GET(self):
		getInput = web.input(macdomain="No Value specified")
		return "test: " + str(getInput.macdomain)
"""

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()
	
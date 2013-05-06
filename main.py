#! /usr/bin/python
# To create the JSON object manually, run the runloop file
# Permissions must be set correctly, all files will be created with www-data permissions,
# so directories need to writable by www-data

import web
import sys
import json
import os

#Need to set the correct path for apache, otherwise it will not find the templates
root = os.path.dirname(__file__)
render = web.template.render(os.path.join(root, 'templates'))

urls = (
	'/', 'index',
	'/runscript', 'runscript',
	'/count', 'count'
)

#web.debug = True
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()

#Homepage
class index:
	def GET(self):
		return render.index()

#This class is the first Ajax call, used to start the script
class runscript:
	def GET(self):
		#Checking if the file exists
		#If the file exists it checks if the script is already running (0)
		#If so a 0 is returned which refuses to run the script (handled in JS)
		#This is necessary so that two processes don't write into the same file
		#If the file should not exist, the script will be run, which will create it
		try:
			fh_status = open('/var/www/dscript/static/datafileCount')
			data = json.loads(fh_status.read())
			if data['status'] is 0:
				return (0)
			else:
				os.system("/var/www/dscript/runloop.py &")
		except:
			os.system("/var/www/dscript/runloop.py &")

#Stupid Name, should of called it status or something
#This class returns the status using json (total, the changing count and a status field)	
class count:
	def GET(self):
		fh_status = open('/var/www/dscript/static/datafileCount')
		data = json.loads(fh_status.read())
		fh_status.close()
		web.header('Content-Type', 'application/json')
		return json.dumps(data)

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()
	
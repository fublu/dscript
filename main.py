#! /usr/bin/python

import web
import sys
import json
import os

render = web.template.render('templates')

urls = (
	'/', 'index',
	'/runscript', 'runscript',
	'/count', 'count'
)

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
		fh_status = open('./datafileCount')
		data = json.loads(fh_status.read())
		if data['status'] is 0:
			return (0)
		else:
			os.system("./runloop.py &")
	except:
		os.system("./runloop.py &")
		
#Stupid Name, should of called it status or something
#This class returns the status using json (total, the changing count and a status field)	
class count:
 def GET(self):
	fh_status = open('./datafileCount')
	data = json.loads(fh_status.read())
	fh_status.close()
	web.header('Content-Type', 'application/json')
	return json.dumps(data)

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()

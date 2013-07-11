"""
	Version:	Dev. 0.1 - Threading and URL corrections 
	Author:		Memleak13
	Date:		11.07.13

	This is the main module which is initilized by Apache.
	Permissions must be set correctly, all files will be created with 
	www-data permissions, directories need to writable by www-data
	
	Apache -> main.py -> index.html -> main.py -> dscript.py
"""
import web
import sys
import os
import json

#Set absolute path for apache
root = os.path.dirname(__file__)
render = web.template.render(os.path.join(root, 'templates'), cache=False)

urls = (
	'/', 'index',
	'/runscript', 'runscript',
	'/counter', 'counter'
)
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc() #when using mod_wsgi

class index:
	"""The initial site allows the user to select the macdomain."""
	
	def GET(self):
		"""Returns /templates/index.html"""
		return render.index()
		
class runscript:
	"""Runs dscript.py"""
	
	def GET(self):
		"""Checks conditions before running script
		
		Checks if status file exists and if the script is already running.
		"""
		#Get get arguments
		argv = web.input()
		macdomain = argv.macdomain
		topology = argv.topology

		try:
			fh_status = open(root + '/static/status')
			data = json.loads(fh_status.read())
			if data['RUN_STATE'] is 1:
				return (1)
			else:
				os.system(root + '/dscript.py %s %s &' 
						  % (macdomain, topology))
		#Throw exception if file does not exist and runs dscript.py. dscript
		#creates the file.
		except:
			os.system(root + '/dscript.py %s %s &' % (macdomain, topology))

class counter:
	"""Returns run state and counter"""
	
	def GET(self):
		fh_status = open(root + '/static/status')
		data = json.loads(fh_status.read())
		fh_status.close()
		web.header('Content-Type', 'application/json')
		return json.dumps(data)
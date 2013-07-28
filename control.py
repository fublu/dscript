import os
import json
import threading
import Queue

class Control (threading.Thread):
	def __init__(self, queue, exit_marker):
		threading.Thread.__init__(self)
		self.queue = queue
		self.exit = exit_marker #Used to exit the run loop
		self.wd = os.path.dirname(__file__) #wd = working directory
		self.result = open(self.wd + '/static/result.html', 'w') #Html
		self.status = open(self.wd + '/static/status', 'w') #Stats
		self.debug = open(self.wd + '/static/debug', 'w')

		self.run_state = 1	#states if the script is running (0=no, 1=yes)
		self.cm_total = ''	#holds all CM in macdomain
		self.cm_count = 0	#holds number of processed modems
		self.cm_online = 0	#this counter counts only online modems	

		self.debug.write('1. Control - Init')
		print ('Control queue ' + str(queue))
		

	def run(self):
		"""Writes tr containg modem values

		Args:
			modem: cable modem
		"""

		self.debug.write('2. Control - Run')
		
		while True:
			modem = self.queue.get()
			if modem is self.exit:
				#self.debug.write('Marker: ' + str(modem))
				break
			#print ('Get Modem: ' + str(modem) + '\n')
			#self.debug.write(modem)
			self.debug.write(str(modem.thread_id) + '\n')
			#self.queue.task_done() #debug


			self.result.write('<tr>')
			self.result.write('<td>' + modem.mac + '</td>')
			self.result.write('<td>' + modem.ip + '</td>')
			self.result.write('<td>' + modem.iface + '</td>')
			self.result.write('<td>' + modem.state + '</td>')
			self.result.write('<td>' + modem.rxpwr + '</td>')
			#US 
			for value in modem.macversion:
				self.result.write('<td>' + value + '</td>')
			for value in modem.upsnr:
				self.result.write('<td>' + value + '</td>')
			for value in modem.receivedpwr:
				self.result.write('<td>' + value + '</td>')
			for value in modem.reportedtransmitpwr:
				self.result.write('<td>' + value + '</td>')
			for value in modem.dspwr:
				self.result.write('<td>' + value + '</td>')
			for value in modem.toff:
				self.result.write('<td>' + value + '</td>')
			for value in modem.uncorrectables:
				self.result.write('<td>' + value + '</td>')
			for value in modem.flaps:
				self.result.write('<td>' + value + '</td>')
			for value in modem.errors:
				self.result.write('<td>' + value + '</td>')
			for value in modem.reason:
				self.result.write('<td>' + value + '</td>')
			#DS	
			for value in modem.docsIfDownChannelPower:
				self.result.write('<td>' + value + '</td>')
			for value in modem.docsIfSigQSignalNoise:
				self.result.write('<td>' + value + '</td>')
			for value in modem.docsIfSigQUncorrectables:
				self.result.write('<td>' + value + '</td>')
			for value in modem.docsIfSigQMicroreflections:
				self.result.write('<td>' + value + '</td>')
			for value in modem.docsIfCmStatusTxPower:
				self.result.write('<td>' + value + '</td>')
			for value in modem.docsIfCmStatusInvalidUcds:
				self.result.write('<td>' + value + '</td>')
			for value in modem.docsIfCmStatusT3Timeouts:
				self.result.write('<td>' + value + '</td>')
			for value in modem.docsIfCmStatusT4Timeouts:
				self.result.write('<td>' + value + '</td>')		
			self.result.write('</tr>')

			self.cm_count += 1
			#TODO, find a better way for this GLOBAL
			#This value is set by the macdomain.
			self.writeState(self.cm_total, self.cm_count, self.cm_online,
				self.run_state)
			self.queue.task_done()
			

	def writeState(self, cm_total, cm_count, cm_online, run_state): 
		"""Writes stats into file
		
		These stats serve as a modem counter and includes the running state  of the
		script.
		"""
		data = {'CM_TOTAL' : cm_total, 'CM_COUNT': cm_count, 
				'CM_ONLINE' : cm_online, 'RUN_STATE' : run_state}
		self.status.seek(0)
		self.status.write(json.dumps(data))

	def write_th(self, title, loop):
		"""writes the th into a file

		Depending on topology and called from create_table_header().
		"""
		for i in range(loop):
			self.result.write('<th>' + title + '</th>')

	def create_html_header(self):
		"""Writes HTML Header
		
			The header contains some javascript to include tablesort 2.0
			http://tablesorter.com
		"""
		self.result.write('<!DOCTYPE HTML>')
		self.result.write('<html>')
		self.result.write('<head>')	
		self.result.write(
			'<link rel="stylesheet" href="/static/themes/blue/style.css" />')
		self.result.write(
			'<script type="text/javascript"' 
			' src="http://code.jquery.com/jquery-1.8.3.min.js"></script>')
		self.result.write(
			'<script type="text/javascript"'
			' src="/static/jquery.tablesorter.min.js"></script>')
		self.result.write('<script type="text/javascript">')
		self.result.write('jQuery(document).ready(function()')
		self.result.write('{') 
		self.result.write('jQuery("#resultTable").tablesorter({')
		self.result.write('widthFixed: true,')
		self.result.write("widgets: ['zebra']")
		self.result.write('}')
		self.result.write(');') 
		self.result.write('}') 
		self.result.write(');') 
		self.result.write('</script>')	
		self.result.write('</head>')
		self.result.write('<body>')

	def create_table_header(self, index):
		"""Writes HTML table header"""
		self.result.write('<table id="resultTable" class="tablesorter">')
		self.result.write('<thead>')
		self.result.write('<tr>')
		#US (index depends on the topology)
		self.write_th('mac',1)
		self.write_th('ip',1)
		self.write_th('iface',1)
		self.write_th('state',1)
		self.write_th('rxpwr',1) 
		self.write_th('Docsis',1)
		self.write_th('upsnr',index)
		self.write_th('receivedpwr',index)
		self.write_th('reportedtransmitpwr',index)
		self.write_th('dspwr',1)
		self.write_th('toff',index)
		self.write_th('init toff',index)
		self.write_th('uncorrectables',index)
		self.write_th('flaps',1)
		self.write_th('errors',1)
		self.write_th('reason',1)
		#DS
		self.write_th('docsIfDownChannelPower',4)
		self.write_th('docsIfSigQSignalNoise<',4)
		self.write_th('docsIfSigQUncorrectables',4)
		self.write_th('docsIfSigQMicroreflections',4)
		self.write_th('docsIfCmStatusTxPower',1)
		self.write_th('docsIfCmStatusInvalidUcds',1)
		self.write_th('docsIfCmStatusT3Timeouts',1)
		self.write_th('docsIfCmStatusT4Timeouts',1)

		self.result.write('</tr>')
		self.result.write('</thead>')
		self.result.write('<tbody>')

	def create_html_footer(self):
		"""Writes HTML footer"""	
		self.result.write('</table>')
		self.result.write('</body>')
		self.result.write('</html>')

	def close(self):
		self.result.close()
		self.status.close()
		self.debug.close()
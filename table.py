"""
	Version:	0.1 - Beta
	Author:		Memleak13
	Date:		22.06.13
"""

class Table(object):
	"""Represents an html table 
	
	This class is used to write the mac domain table containing all cable 
	modems into an html file. It differs between the mac domain topology and 
	the docsis version of the modem. Depending on the topology and the 
	docsis version, empty cells for the modems need to be created to 
	compensate for d3 bonded comlumns.

	"""

	def __init__(self, topology):
		"""Sets the topology of the mac domain

		index: describes how many times a 'for' loop needs to run through. 
		This loop is responsible for creating empty cells.

		Args: topology: Macdomain topology 
						(ex. 1214 = 1USG (2xbonded), 1 DSG(4xbonded))
		"""
		if topology == '1214' or topology == '2214':
			self.index = 2
		if topology == '1314' or topology == '1324':
			self.index = 3

		self.result = open(
			'/home/tbsadmin/projects/dscript/static/result.html', 'w') #Html 
		self.create_html_header()
		self.create_table_header(self.index)

	def adjust_4_d3(self, modem):
		"""No adjustment is needed
		
		Future placeholder

		Args:
			modem: D3 modem
		"""
		self.write_tr(modem)

	def adjust_4_d2(self, modem):
		"""Adds empty cells for d2 modems
		
		Depending on the topology additional one, two or more empty entries 
		need to be added to compensated for d3 bonded tables columns. 

		Args:
			modem: D2 modem
		"""
		#Creating empty cells if a d2 value exists already
		#(2 extra if it is a 3 bonded US. 1 extra if 2 bonded US)
		for i in range (self.index -1):
			modem.upsnr.append(' ')
			modem.receivedpwr.append(' ')
			modem.reportedtransmitpwr.append(' ')
			modem.toff.insert(1,' ')
			modem.toff.insert(4,' ')
			modem.uncorrectables.append(' ')
			
		#if no value exists for this column, one extra empty cell
		#needs to be appended
		modem.reportedtransmitpwr.append(' ')
		modem.reason.append(' ')

		#Empty DS (always append 3 times).
		for i in range(3):
			modem.docsIfDownChannelPower.append(' ')
			modem.docsIfSigQSignalNoise.append(' ')
			modem.docsIfSigQUncorrectables.append(' ')
			modem.docsIfSigQMicroreflections.append(' ')

		self.write_tr(modem)

	def adjust_4_d1(self, modem):
		"""Adds empty cells for d1 modems
		
		To make things easier and because I am lazy, SNMP requests for d1 
		modems have been disabled. There are only a few operational anyway.
		Only basic values are written into the file.

		Args:
			modem: D1 modem
		"""
		self.result.write('<tr>')
		self.result.write('<td>' + modem.mac + '</td>')
		self.result.write('<td>' + modem.ip + '</td>')
		self.result.write('<td>' + modem.iface + '</td>')
		self.result.write('<td>' + modem.state + '</td>')
		self.result.write('<td>' + modem.rxpwr + '</td>')
		self.result.write('<td>' + modem.macversion[0] + '</td>')
		self.result.write('</tr>')

	def write_tr(self, modem):
		"""Writes tr containg modem values

		Args:
			modem: cable modem
		"""	
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

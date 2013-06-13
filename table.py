"""
	Version:	0.1 - Beta
	Author:		Memleak13
	Date:		22.06.13
"""

class Table(object):
	"""Represents an html table 
	
	This class is used to write the mac domain table containing all cable modems
	into a file. It differs between the mac domain topology and the the docsis
	version of the modem. Depending on the topology and the docsis version, 
	empty cells for the modems need to be created. Otherwise it would not be 
	possible to store all the modem in the same table.

	"""

	def __init__(self, topology):
		"""Sets the topology of the mac domain

		Args: topology: Macdomain topology
		"""
		self.topology = topology
		self.result = open('/home/tbsadmin/projects/dscript/static/result.html', 'w') #Html 
		self.create_html_header()
		self.create_table_header()

	def adjust_4_d3(self, modem):
		"""No adjustment is needed
		
		Future placeholder

		Args:
			modem: D3 modem
		"""
		self.write_tr(modem)

	def adjust_4_d2(self, modem):
		"""Adds empty cells for d2 modems
		
		Depending on topology additional one, two or more entries need to be 
		added to certain values. This to compensate for bonded d3 values by 
		creating empty cells.

		TODO: Depending on topology two different sets of values are created

		Args:
			modem: D2 modem
		"""
		#Empty US
		modem.upsnr.append('-')
		modem.receivedpwr.append('-')
		modem.reportedtransmitpwr.append('-')
		modem.reportedtransmitpwr.append('-')
		modem.toff.insert(1,'-')
		modem.toff.insert(3,'-')
		modem.uncorrectables.append('-')
		modem.reason.append('-')
		#Empty DS
		modem.docsIfDownChannelPower.append('-')
		modem.docsIfDownChannelPower.append('-')
		modem.docsIfDownChannelPower.append('-')
		modem.docsIfSigQSignalNoise.append('-')
		modem.docsIfSigQSignalNoise.append('-')
		modem.docsIfSigQSignalNoise.append('-')
		modem.docsIfSigQUncorrectables.append('-')
		modem.docsIfSigQUncorrectables.append('-')
		modem.docsIfSigQUncorrectables.append('-')
		modem.docsIfSigQMicroreflections.append('-')
		modem.docsIfSigQMicroreflections.append('-')
		modem.docsIfSigQMicroreflections.append('-')

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
		
	def create_html_header(self):
		"""Writes HTML Header
		
			The header contains some javascript to include tablesort 2.0
			http://tablesorter.com
		"""
		self.result.write('<!DOCTYPE HTML>')
		self.result.write('<html>')
		self.result.write('<head>')	
		self.result.write('<link rel="stylesheet" href="/static/themes/blue/style.css" />')
		self.result.write('<script type="text/javascript" src="http://code.jquery.com/jquery-1.8.3.min.js"></script>')
		self.result.write('<script type="text/javascript" src="/static/jquery.tablesorter.min.js"></script>')
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

	def create_table_header(self):
		"""Writes HTML table header"""
		
		self.result.write('<table id="resultTable" class="tablesorter">')
		self.result.write('<thead>')
		self.result.write('<tr>')
		self.result.write('<th>mac</th>')
		self.result.write('<th>ip</th>')
		self.result.write('<th>iface</th>')
		self.result.write('<th>state</th>')
		self.result.write('<th>rxpwr</th>') 
		self.result.write('<th>Docsis</th>')
		self.result.write('<th>upsnr</th>')
		self.result.write('<th>upsnr</th>')
		self.result.write('<th>receivedpwr</th>')
		self.result.write('<th>receivedpwr</th>')
		self.result.write('<th>reportedtransmitpwr</th>')
		self.result.write('<th>reportedtransmitpwr</th>')
		self.result.write('<th>dspwr</th>')
		self.result.write('<th>toff</th>')
		self.result.write('<th>toff</th>')
		self.result.write('<th>init toff</th>')
		self.result.write('<th>init toff</th>')
		self.result.write('<th>uncorrectables</th>')
		self.result.write('<th>uncorrectables</th>')
		self.result.write('<th>flaps</th>')
		self.result.write('<th>errors</th>')
		self.result.write('<th>reason</th>')
		self.result.write('<th>docsIfDownChannelPower</th>')
		self.result.write('<th>docsIfDownChannelPower</th>')
		self.result.write('<th>docsIfDownChannelPower</th>')
		self.result.write('<th>docsIfDownChannelPower</th>')
		self.result.write('<th>docsIfSigQSignalNoise</th>')
		self.result.write('<th>docsIfSigQSignalNoise</th>')
		self.result.write('<th>docsIfSigQSignalNoise</th>')
		self.result.write('<th>docsIfSigQSignalNoise</th>')
		self.result.write('<th>docsIfSigQUncorrectables</th>')
		self.result.write('<th>docsIfSigQUncorrectables</th>')
		self.result.write('<th>docsIfSigQUncorrectables</th>')
		self.result.write('<th>docsIfSigQUncorrectables</th>')
		self.result.write('<th>docsIfSigQMicroreflections</th>')
		self.result.write('<th>docsIfSigQMicroreflections</th>')
		self.result.write('<th>docsIfSigQMicroreflections</th>')
		self.result.write('<th>docsIfSigQMicroreflections</th>')
		self.result.write('<th>docsIfCmStatusTxPower</th>')
		self.result.write('<th>docsIfCmStatusInvalidUcds</th>')
		self.result.write('<th>docsIfCmStatusT3Timeouts</th>')
		self.result.write('<th>docsIfCmStatusT4Timeouts</th>')
		self.result.write('</tr>')
		self.result.write('</thead>')
		self.result.write('<tbody>')

	def create_html_footer(self):
		"""Writes HTML footer"""	
		self.result.write('</table>')
		self.result.write('</body>')
		self.result.write('</html>')

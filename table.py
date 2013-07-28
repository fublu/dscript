"""
	Version:	Dev. 0.1 - Threading and URL corrections 
	Author:		Memleak13
	Date:		11.07.13

	This module adjusts the modem values to be inserted into the html table
"""
import datetime
import Queue

class Table(object):
	"""Represents an html table 
	
	This class is used to write the mac domain table containing all cable 
	modems into an html file. It differs between the mac domain topology and 
	the docsis version of the modem. Depending on the topology and the 
	docsis version, empty cells for the modems need to be created to 
	compensate for d3 bonded comlumns.
	"""

	def __init__(self, index, queue):
		"""Sets the topology of the mac domain

		Args: 
			index: describes how many times a 'for' loop needs to run through. 
				This loop is responsible for creating empty cells.
		"""
		self.queue = queue
		self.index = index

	def adjust_4_d3(self, modem):
		"""No adjustment is needed
		
		Future placeholder

		Args:
			modem: D3 modem
		"""
		self.queue.put(modem)

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
		
		self.queue.put(modem)

	def adjust_4_d1(self, modem):
		"""Adds empty cells for d1 modems
		
		To make things easier and because I am lazy, SNMP requests for d1 
		modems have been disabled. There are only a few operational anyway.
		Only basic values are written into the file.

		Args:
			modem: D1 modem
		"""
		self.queue.put(modem)
		#try:
		#	self.result.write('<tr>')
		#	self.result.write('<td>' + modem.mac + '</td>')
		#	self.result.write('<td>' + modem.ip + '</td>')
		#	self.result.write('<td>' + modem.iface + '</td>')
		#	self.result.write('<td>' + modem.state + '</td>')
		#	self.result.write('<td>' + modem.rxpwr + '</td>')
		#	self.result.write('<td>' + modem.macversion[0] + '</td>')
		#	self.result.write('</tr>')
		#except Exception as e: 
		#	"""
		#	DEBUG = open(self.ROOT + '/static/debug', 'a') #Debug
		#	DEBUG.write(str(datetime.datetime.now()) + ' D1 Error\n')
		#	DEBUG.write('mac: ' + modem.mac + '	ip: ' + modem.ip + '\n')
		#	DEBUG.write(str(e) + '\n\n')
		#	DEBUG.write(str(modem.__dict__) + '\n\n')
		#	DEBUG.close()
		#	"""
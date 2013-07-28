#!/usr/bin/python
"""
	Version:	Dev. 0.1 - Threading and URL corrections 
	Author:		Memleak13
	Date:		11.07.13

	This is the main script which requests the data from the cmts and modems.
	It is started from main.py and calls table.py to create the html file.

	#Todo:
		1. queue is passed from main to md to table ... not nice
		2. add destructors to class (see cmts)
"""
#My modules
from table import Table
from control import Control

#Other modules
import re 			#used to define telnet prompt
import sys 			#argv
import datetime     #debugging timestamps 
import telnetlib	#telnet lib
import threading 	#threading for control and modem class
import os 			#used to define the root path directory
import Queue 		#table <-> control
from pysnmp.entity.rfc3413.oneliner import cmdgen 	#snmp command generation


class Cmts(object):
	"""Represents a cmts.
	
	It is identified by its name and IP address.
	It contains the macdomain domain which contains all modems.
    The telnet object is used to access the cmts and run commands. 
	The session stays open until the object is destroyed.
	"""

	def __init__(self, ip, name):
		"""Inits cmts with ip, name and 2 telnet object.

		This creates 2 telnet streams. Depending on the tread id 
		1 or the other is used. It seems that only 4 request per
		second per stream are processed by the cmts. The idea is 
		to double this by having 2 telnet streams open.

		TODO: Above does not seem to be quite true however !
		
		Args:
			ip: ip address
			name: the name of the device, also used for the telnet prompt
		"""
		self.ip = ip
		self.name = name
		self.tn1 = TelnetAccess(self.ip, self.name, IOS_UID, IOS_PW)
		self.tn2 = TelnetAccess(self.ip, self.name, IOS_UID, IOS_PW) 
    
	def createMacDomain(self, iface, topology, queue):
		"""Creates and stores the mac domain.
		
		See MacDomain class.
		
		Args:
			iface: the macdomain selected by the user
		"""
		self.macdomains  = MacDomain(iface, topology, queue)

	def getCMs(self):
		"""Retrieves all modems in the specified macdomain
		
		By running the ios command "show cable modem cable [macdomain]"
		"""
		return self.tn1.runCommand('show cable modem cable ' + 
			str(self.macdomains.name))

	def getCMverbose(self, cmmac, thread_id):
		"""Retrives values for a specific cable modem.
		
		By running the ios comand "show cable modem [mac] verbose.
		
		Args:
			cmmac: mac address of the cable modem
			thread_id: used to alternate between telnet streams
		"""
		if thread_id % 2 == 0:
			return self.tn1.runCommand('show cable modem ' + cmmac + ' verbose')
		else:
			return self.tn2.runCommand('show cable modem ' + cmmac + ' verbose')

	def __del__(self):
		"""Closes and deletes the telnet connection"""
		self.tn1.closeTN() 	
		self.tn2.closeTN() 	
		del self.tn1 		
		del self.tn2 		

class MacDomain(object):
	"""Represents the mac domain.
	
	Identified by its name (the macdomain selected by the user).
	It contains a list of all cable modems in this domain
	"""
		
	def __init__(self, name, topology, queue):
		"""Inits the macdomain

		index is used by the table and control class to adjust the table
		cells if the modem is a d1 or d2 modem. It determins how often a
		loop is run through and depends what topology is used
		
		Args:
			name: represents the mac domain (ex. c5/1/0)
			topology: Macdomain topology 
				(ex. 1214 = 1USG (2xbonded), 1 DSG(4xbonded))
		"""
		self.name = name
		self.topology = topology
		self.queue = queue
		if topology == '1214' or topology == '2214':
			self.index = 2
		if topology == '1314' or topology == '1324':
			self.index = 3
		self.table = Table(self.index, queue) 

	def extractData(self, get_cm_output):
		"""Extracts and filters modem values.
		
		Filters the cmts output to contain just modems. According to this list
		it the creates a thread for each modem.
		"""
		
		#Step 2.1: Reading and filtering the cmts output to include only modems
		get_cm_output = get_cm_output.split('\n')
		clean_list = []
		for line in get_cm_output:
			clean_list.append(line)
		del clean_list[0:4]
		del clean_list[len(clean_list)-1]
		del clean_list[len(clean_list)-1]
		global control 
		control.cm_total = len(clean_list)
		
		#Step 2.2: Create cm object with initial values
		all_threads = []
		thread_id = 1
		for line in clean_list:
			modem = Modem(line, thread_id) 
			all_threads += [modem]
			thread_id += 1
			modem.start()		
		for thread in all_threads:
			thread.join()
		global exit_marker 
		self.queue.put(exit_marker)

class Modem(threading.Thread):
	"""Represents the modem.
	
	Includes all docis values retreived by the cmts or modem.
	Connects to the modem using snmp.
	The locks locks are needed to control the telnet access to the cmts. If 
	this were not the case, the cmts would be flooded by telnet requests and 
	all vty lines would finally be occupied. 

	The thread id is used to alternate between telnet streams
	"""	
	snmpcommunity = 'web4suhr'
	lock1 = threading.Lock()
	lock2 = threading.Lock()

	def __init__(self, line, thread_id):
		"""Inits modem setting all attributes to empty values
		
		To keep things simple, I created lists for all attributes except the
		initial ones. Even if they only take one attribute.

		Args:
			line: contains one line of the cmts "show cable modem" output
		"""
		threading.Thread.__init__(self)
		self.thread_id = thread_id
		self.line = line
		self.mac = ''
		self.ip = ''
		self.iface = ''
		self.state = ''
		self.rxpwr = ''
		self.macversion = []
		self.upsnr = []
		self.receivedpwr = []
		self.reportedtransmitpwr = []
		self.dspwr = []
		self.toff = []
		self.uncorrectables = []
		self.flaps = []
		self.errors = []
		self.reason = []
		self.padj = []
		self.docsIfDownChannelPower = []
		self.docsIfCmStatusTxPower = []
		self.docsIfSigQSignalNoise = []
		self.docsIfSigQUncorrectables = []
		self.docsIfSigQMicroreflections = []
		self.docsIfCmStatusInvalidUcds = []
		self.docsIfCmStatusT3Timeouts = []
		self.docsIfCmStatusT4Timeouts = []

	def run(self):
		"""sets and receives all modem values by telnet or snmp"""
		#Setting the initial values (mac, ip etc..)
		values = self.line.split()
		self.mac = values[0].strip()
		self.ip = values[1].strip()
		self.iface = values[2].strip()
		self.state = values[3].strip()
		self.rxpwr = values[5].strip()

		#Step 2.3: Setting US and other values retrieved from the cmts
		#Todo: duplicated code (here and in cmts) 		
		if self.thread_id % 2 == 0:
			Modem.lock1.acquire()
			verbose_output = ubr01shr.getCMverbose(values[0], self.thread_id)
			Modem.lock1.release()
			self.setUSData(verbose_output)
		else: 
			Modem.lock2.acquire()
			verbose_output = ubr01shr.getCMverbose(values[0], self.thread_id)
			Modem.lock2.release()
			self.setUSData(verbose_output)
			
		#Step 2.4: 	Setting DS data retrieved from the modem by snmp
		#Todo: Strangely enough if I disable this if, it messes up
		#the html table. D2 values are not properly displayed anymore ...
		if ('DOC3.0' in self.macversion or 'DOC2.0' in self.macversion or 
			'DOC1.1' in self.macversion):
			self.setDSData()

		#Step 2.5: Adjusting table for d2 and d1 values
		if 'DOC3.0' in self.macversion:
			ubr01shr.macdomains.table.adjust_4_d3(self)
		elif 'DOC2.0' in self.macversion or 'DOC1.1' in self.macversion:
			ubr01shr.macdomains.table.adjust_4_d2(self)
		else:
			ubr01shr.macdomains.table.adjust_4_d1(self)

	def setUSData(self, verbose_output):
		"""Sets US Data"""
		verbose_output = verbose_output.split('\n')
		for line in verbose_output:
			if 'MAC Version' in line:
				value = line.split(':')
				#Line needs to be split again in case of multiple values(bonded)
				value = value[1].split()
				for index in value:
					self.macversion.append(index.strip())
			elif 'Upstream SNR' in line:
				value = line.split(':')
				value = value[1].split()
				for index in value:
					self.upsnr.append(index.strip())
			elif 'Received Power' in line:
				value = line.split(':')
				value = value[1].split()
				for index in value:
					self.receivedpwr.append(index.strip())
			elif 'Reported Transmit Power' in line:
				value = line.split(':')
				value = value[1].split()
				for index in value:
					self.reportedtransmitpwr.append(index.strip())
			elif 'Downstream Power' in line:
				value = line.split(':')
				self.dspwr.append(value[1].strip())
			elif 'Timing Offset' in line:
				value = line.split(':')
				value = value[1].split()
				for index in value:
					self.toff.append(index.strip())
			elif 'Uncorrectable Codewords' in line:
				value = line.split(':')
				value = value[1].split()
				for index in value:
					self.uncorrectables.append(index.strip())
			elif 'Flaps' in line:
				value = line.split(':')
				self.flaps.append(value[1].strip())
			elif 'Errors' in line:
				value = line.split(':')
				self.errors.append(value[1].strip())
			elif 'CM Initialization Reason' in line:
				value = line.split(':')
				value = value[1].split()
				for index in value:
					self.reason.append(index.strip())

	def setDSData(self):
		"""Sets DS Data."""
		if 'online' in self.state:
			#Todo: disabled, as would requiere another lock! 
			#This var is not required by the app anyway!
			#global control
			#control.cm_online += 1			
			receivedsnmpvalues = self.getsnmp()
			for mib, snmpvalue in sorted(receivedsnmpvalues.iteritems()):
				if 'docsIfDownChannelPower' in mib:
					self.docsIfDownChannelPower.append(snmpvalue)
				if 'docsIfSigQSignalNoise' in mib:
					self.docsIfSigQSignalNoise.append(snmpvalue)
				if 'docsIfSigQUncorrectables' in mib:
					self.docsIfSigQUncorrectables.append(snmpvalue)
				if 'docsIfSigQMicroreflections' in mib:
					self.docsIfSigQMicroreflections.append(snmpvalue)
				if 'docsIfCmStatusTxPower' in mib:
					self.docsIfCmStatusTxPower.append(snmpvalue)
				if 'docsIfCmStatusInvalidUcds' in mib:
					self.docsIfCmStatusInvalidUcds.append(snmpvalue)
				if 'docsIfCmStatusT3Timeouts' in mib:
					self.docsIfCmStatusT3Timeouts.append(snmpvalue)
				if 'docsIfCmStatusT4Timeouts' in mib:
					self.docsIfCmStatusT4Timeouts.append(snmpvalue)
	
	def getsnmp(self):
		"""Connects to modem using SNMP.
		
		Returns: snmpvalue, a dictionary mapping mib to its corresponding
			value.
		"""
		snmpvalue = {}  #dictionary which will be returned
		try:
			cmdGen = cmdgen.CommandGenerator()
			errorIndication, errorStatus, errorIndex, varBindTable = cmdGen.nextCmd(
				cmdgen.CommunityData(Modem.snmpcommunity, mpModel=0),
				cmdgen.UdpTransportTarget((self.ip, 161)),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfDownChannelPower'),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfSigQSignalNoise'),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfCmStatusTxPower'),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfSigQUncorrectables'),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfSigQMicroreflections'),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfCmStatusInvalidUcds'),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfCmStatusT3Timeouts'),
				cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfCmStatusT4Timeouts'),
				#cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfCmStatusT1Timeouts'),
				#cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfCmStatusT2Timeouts'),
				#cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfUpChannelTxTimingOffset'),
				#cmdgen.MibVariable('DOCS-IF-MIB', 'docsIfCmStatusInvalidMaps'),
				lookupNames=True, lookupValues=True
				)
			if errorIndication:
				print(errorIndication)
			else:
				if errorStatus:
					print('%s at %s' % (
							errorStatus.prettyPrint(),
							errorIndex and varBindTable[-1][int(errorIndex)-1] or '?'
							)
						)
				else:
					for varBindTableRow in varBindTable:
						for name, val in varBindTableRow:
							snmpvalue[name.prettyPrint()] = val.prettyPrint()
			#print('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

		except Exception as e:
			global control
			control.debug.write(str(datetime.datetime.now()) + 'SNMP ERROR\n')
			control.debug.write('mac: ' + self.mac + '	ip: ' + self.ip + '\n')
			control.debug.write(str(e) + '\n\n')
			control.debug.write(str(self.__dict__) + '\n\n')
			control.debug.close()
		return snmpvalue

class TelnetAccess(object):
	"""Creates and establishes a telnet session."""
	
	# Defining regular expressions for the different prompts
	ios_unprivPrompt = re.compile ('.*>')
	ios_privPrompt = re.compile ('.*#')
	regexlist = [ios_unprivPrompt, ios_privPrompt, 'Username:', 'Password:', 
				 'username:', 'password:']
	
	def __init__(self, ip, name, uid, password):
		"""Inits the telnet session and connects to the device.
		
		Args:
			ip: ip address
			uid: user id
			password: well ... 
		"""
		self.ip = ip
		self.prompt = name + '#' #read_until prompt (ex. ubr01SHR#)
		self.uid = uid
		self.password = password
		self.telnetoutput = ''
		self.tn = telnetlib.Telnet(self.ip) #Connect
		#IOS Login prodedure (unpriv -> enable -> priv)
		self.tn.expect(TelnetAccess.regexlist)
		self.tn.write(self.uid + "\n")
		self.tn.expect(TelnetAccess.regexlist)
		self.tn.write(self.password + "\n")
		self.tn.expect(TelnetAccess.regexlist)

	def runCommand(self,command):
		"""Runs a command on a device connected by telnet.
		
		and returns the output
		
		Args:
			command: whatever could this stand for ...
		"""
		self.tn.write(command + "\n")
		return self.tn.read_until(self.prompt)

	def closeTN(self):
		"""Close connection"""
		self.tn.close()
		
#TODO: Add following to main() 
ROOT = os.path.dirname(__file__)	#setting root path to directory of file
IOS_UID = 'dscript'
IOS_PW = 'hf4ev671'

#Step 1.1 - Receiving argv(mac domain), create cmts, macdomain, queues, 
#	control etc...
macdomain = str(sys.argv[1])
topology = str(sys.argv[2])
queue = Queue.Queue()
exit_marker = object()

#To run script from command line
#macdomain = '5/1/1' #Debug
#topology = '1214' #Debug

ubr01shr = Cmts('10.10.10.50', 'ubr01SHR') #Case Sensitiv! Telnet prompt!
ubr01shr.createMacDomain(macdomain, topology, queue)
control = Control(queue, exit_marker) # contains all write and state procedures
control.start()
control.create_html_header()
control.create_table_header(ubr01shr.macdomains.index)

#Step 1.2 Receiving list of all cm in this upstream
get_cm_output = ubr01shr.getCMs()

#Step 2.1 - 2.5: Retrieve, split list, create modem threads
ubr01shr.macdomains.extractData(get_cm_output)	

#Step 3 - Finishing
control.join()
control.create_html_footer()
control.run_state = 0
control.writeState(control.cm_total, control.cm_count, control.cm_online,
	control.run_state)
del ubr01shr
del control


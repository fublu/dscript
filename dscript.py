#!/usr/bin/python
"""
	Version:	Dev. 0.1 - Threading and URL corrections 
	Author:		Memleak13
	Date:		11.07.13

	This is the main script which requests the data from the cmts and modems.
	It is started from main.py and calls table.py to create the html file.
"""
#My modules
from table import Table
from control import Control

#Other modules
import re
import sys
import time 
import datetime      
import telnetlib
#import json
import threading
import os
import Queue
from pysnmp.entity.rfc3413.oneliner import cmdgen


class Cmts(object):
	"""Represents a cmts.
	
	It is identified by its name and IP address.
	It contains the macdomain domain which includes the requsted modems.
	It creates a telnet object when initilized. The telnet object is 
	used to access the cmts and run commands. The session stays open until the 
	object is destroyed.
	"""

	lock1 = threading.Lock()
	lock2 = threading.Lock()
	
	def __init__(self, ip, name):
		"""Inits cmts with ip, name and 2 telnet object.

		 This creates 2 telnet streams. Depending on the tread id 
		 1 or the other is used. It seems that only 4 request per
		 second per stream are processed by the cmts. The idea is 
		 to double this by having 2 telnet streams open

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
		"""Retroves values for a specific cable modem.
		
		By running the ios comand "show cable modem [mac] verbose.
		The output is written into the file telnetoutput
		
		Args:
			cmmac: mac address of the cable modem
			thread_id: used to alternate between telnet streams
		"""
		if thread_id % 2 == 0:
			#Cmts.lock1.acquire()
			return self.tn1.runCommand('show cable modem ' + cmmac + ' verbose')
			#Cmts.lock1.release()
		else:
			#Cmts.lock2.acquire()
			return self.tn2.runCommand('show cable modem ' + cmmac + ' verbose')
			#Cmts.lock2.release()

	def __del__(self):
		"""Closes and deletes the telnet connection"""
		self.tn1.closeTN() 	# close telnet connection
		self.tn2.closeTN() 	# close telnet connection
		del self.tn1 		# delete object
		del self.tn2 		# delete object

class MacDomain(object):
	"""Represents the mac domain.
	
	Identified by its name (the macdomain selected by the user).
	It contains a list of all cable modems in this domain by filtering
	the cmts output. 
	"""
		
	def __init__(self, name, topology, queue):
		"""Inits the macdomain

		index is used to describe how many times a loop is run for.
		this attribute is used by the table and control class
		
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
		
		Filters the cmts output to contain just modems.
		Creates a modem object where it stores US and DS information for each 
		modem by retrieving the data from the cmts(US) over telnet and from the 
		cable modem over snmp(DS). Finally it writes this data into an html 
		file (result.html).
		
		Refers to step 2.1 - 2.5
		"""
		
		#Step 2.1: Reading and filtering the cmts output to include only modems
		
		#fin = open(ROOT + '/static/telnetoutput', 'r')
		#DEBUG.write(get_cm_output) 
		get_cm_output = get_cm_output.split('\n')
		
		"""
		for line in cm_output:
			DEBUG.write('Test' + line + '\n') 
		"""

		cleanedlist = []
		for line in get_cm_output:
			cleanedlist.append(line)
		del cleanedlist[0:4]
		del cleanedlist[len(cleanedlist)-1]
		del cleanedlist[len(cleanedlist)-1]

		#TODO, should be a class or instance variable, if possible
		#This global is also used by the control class, find a better
		#solution
		global control 
		control.cm_total = len(cleanedlist)
		
		#fin.close()
		
		#Step 2.2: Modem object (thread) is created with initial values.
		#cmdatafromcmts = [] #NEW: needs to be added to CM
		all_threads = []
		thread_id = 1 # TODO: Setting a thread id for debugging purposes
		for line in cleanedlist:
			modem = Modem(line, thread_id) #NEW: add line to Modem
			all_threads += [modem]
			thread_id += 1
			modem.start()		
		for thread in all_threads:
			thread.join()
		global exit_marker
		print ('Putting Exit' + str(exit_marker))
		self.queue.put(exit_marker)
			
		"""
			#NEW: All will be added to CM - can be initiated in init. 

			del cmdatafromcmts[:]
			cmdatafromcmts = line.split()
			modem.mac = cmdatafromcmts[0].strip()
			modem.ip = cmdatafromcmts[1].strip()
			modem.iface = cmdatafromcmts[2].strip()
			modem.state = cmdatafromcmts[3].strip()
			modem.rxpwr = cmdatafromcmts[5].strip()
			
			#Step 2.3: Setting US and other values retrieved from the cmts
			
			#NEW: LOCK
			# 2 Reasons - 1. Access to CMTS limited, 2. Write file
			ubr01shr.getCMverbose(cmdatafromcmts[0])
			modem.setUSData()
			#NEW: RELEASE
		
			#Step 2.4: 	Setting DS data retrieved from the modem 
			# 			except (D1 Modems)
			if 'DOC3.0' in modem.macversion or 'DOC2.0' in modem.macversion:
				modem.setDSData()
			
			#NEW: LOCK	
			#Step 2.5: Writting html ouptut 
			if 'DOC3.0' in modem.macversion:
				self.table.adjust_4_d3(modem) #NEW: not self
			
			elif 'DOC2.0' in modem.macversion: #NEW: not self
				self.table.adjust_4_d2(modem)
			
			else:
				self.table.adjust_4_d1(modem) #NEW: not self

				
			global CM_COUNT
			CM_COUNT+=1
			writeState();
			#NEW: RELEASE

			del modem 
			"""

class Modem(threading.Thread):
	"""Represents the modem.
	
	Includes all docis values retreived by the cmts or modem.
	Connects to the modem using snmp.

	3 locks are created. 1 for the first telnet stream, 1 for 
	the second telnet stream and 1 to write the html file

	The thread id is used to alternate between telnet streams
	"""
	
	snmpcommunity = 'web4suhr'
	lock1 = threading.Lock()
	lock2 = threading.Lock()
	#lock3 = threading.Lock()

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
		"""initiated by start()"""
		values = self.line.split()
		self.mac = values[0].strip()
		self.ip = values[1].strip()
		self.iface = values[2].strip()
		self.state = values[3].strip()
		self.rxpwr = values[5].strip()

		#Step 2.3: Setting US and other values retrieved from the cmts
		#The look has two purposes. 1 to limit number of telnet connections
		#to cmts. 2 to lock the file access (telnetoutput)
		#TODO: find a better way, duplicated code, especially as the same
		#	the same condition is found in the cmts class again!

		
		if self.thread_id % 2 == 0:
			Modem.lock1.acquire()
			
			#DEBUG.write('Thread Id: ' + str(self.thread_id) + 
			#		'    CMVerbose Timestamp: ' + str(datetime.datetime.now()) + 
			#		'	 State: ' + self.state + '\n')

			verbose_output = ubr01shr.getCMverbose(values[0], self.thread_id)
			self.setUSData(verbose_output)
			Modem.lock1.release()
		else: 
			Modem.lock2.acquire()
			
			#DEBUG.write('Thread Id: ' + str(self.thread_id) + 
			#		'    CMVerbose Timestamp: ' + str(datetime.datetime.now()) + 
			#		'	 State: ' + self.state + '\n')

			verbose_output = ubr01shr.getCMverbose(values[0], self.thread_id)
			self.setUSData(verbose_output)
			Modem.lock2.release()
		

		#verbose_output = ubr01shr.getCMverbose(values[0], self.thread_id) #Debug
		#self.setUSData(verbose_output) #Debug

		#print (self.macversion[0] + '\n') #Debug

		#Step 2.4: 	Setting DS data retrieved from the modem 
		# 			except (D1 Modems), no Lock.l
		if 'DOC3.0' in self.macversion or 'DOC2.0' in self.macversion:
			self.setDSData() #Debug

		#Step 2.5: Writting html ouptut
		#Modem.lock3.acquire()

		"""
		DEBUG.write('Thread Id: ' + str(self.thread_id) + 
			'    HTML Output Timestamp: ' + str(datetime.datetime.now()) + 
			' 	 MAC: ' + self.mac + '\n') 
		"""
		global control #Debug
		print ('Alive? ' + str(control.is_alive()))#Debug
		if 'DOC3.0' in self.macversion:
			print ('if D3: ' + str(self.thread_id) + '\n') #Debug
			ubr01shr.macdomains.table.adjust_4_d3(self) #Debug


		elif 'DOC2.0' in self.macversion:
			print ('if D2 '+ str(self.thread_id) + '\n') #Debug
			ubr01shr.macdomains.table.adjust_4_d2(self) #Debug

		else:
			print ('if D1 ' + str(self.thread_id) + '\n') #Debug
			ubr01shr.macdomains.table.adjust_4_d1(self) #Debug

		
		
		#global CM_COUNT #TODO
		#CM_COUNT+=1
		#writeState();
		
		#Modem.lock3.release()	

	def setUSData(self, verbose_output):
		"""Sets US Data"""
		verbose_output = verbose_output.split('\n')
		#fin = open(ROOT + '/static/telnetoutput', 'r')
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
		#fin.close()

	def setDSData(self):
		"""Sets DS Data."""
		if 'online' in self.state:
			#disabled temporary as this would require another lock
			#global CM_ONLINE
			#CM_ONLINE += 1					
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
			DEBUG = open(ROOT + '/static/debug', 'a') #Debug
			DEBUG.write(str(datetime.datetime.now()) + 'SNMP ERROR\n')
			DEBUG.write('mac: ' + self.mac + '	ip: ' + self.ip + '\n')
			DEBUG.write(str(e) + '\n\n')
			DEBUG.write(str(self.__dict__) + '\n\n')
			DEBUG.close()

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
		#self.telnetoutput = open(
		#	ROOT + '/static/telnetoutput', 'w')		
		self.tn.write(command + "\n")
		return self.tn.read_until(self.prompt)
		#self.telnetoutput.write(output)
		#self.telnetoutput.close()

	def closeTN(self):
		"""Close connection"""
		self.tn.close()
		
#TODO: Add following to main() 

ROOT = os.path.dirname(__file__)	#setting root path to directory of file
#RUN_STATE = 1	#states if the script is running (0=no, 1=yes)
#CM_TOTAL = ''	#holds all CM in macdomain
#CM_COUNT = 0	#holds number of processed modems
#CM_ONLINE = 0	#this counter counts only online modems
IOS_UID = 'dscript'
IOS_PW = 'hf4ev671'
#STATUS = open(ROOT + '/static/status', 'w') #Stats
#DEBUG = open(ROOT + '/static/debug', 'w')

#Step 1.1 - Receiving argv(mac domain), create cmts, macdomain, control etc...

macdomain = str(sys.argv[1])
topology = str(sys.argv[2])
queue = Queue.Queue()
exit_marker = object()

#To run script from command line
#macdomain = '5/1/0' #Debug
#topology = '1214' #Debug

ubr01shr = Cmts('10.10.10.50', 'ubr01SHR') #Case Sensitiv, used for telnet prompt
ubr01shr.createMacDomain(macdomain, topology, queue)

control = Control(queue, exit_marker) # contains all write and status procedures
control.start()
control.create_html_header()
control.create_table_header(ubr01shr.macdomains.index)

get_cm_output = ubr01shr.getCMs()

#Step 2.1 - 2.5: Retrieve, filter data
ubr01shr.macdomains.extractData(get_cm_output)	
#queue.put(exit_marker) 

#Step 3 - Cleaning up
control.join()
control.create_html_footer()
#ubr01shr.macdomains.table.result.close()
#RUN_STATE=0
control.run_state = 0
control.writeState(control.cm_total, control.cm_count, control.cm_online,
	control.run_state)
#STATUS.close()
#del ubr01shr
del control


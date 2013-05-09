#!/usr/bin/python
"""
	Version:	0.1.1 - New Concept using webpy and ajax instead of plain old cgi 
	Author:		Memleak13
	Date:		09.05.13 - 12:00
"""

import re
import sys
import time        
import telnetlib
import json
from pysnmp.entity.rfc3413.oneliner import cmdgen

class Cmts(object):
	def __init__(self, ip, name):
		self.ip = ip
		self.name = name
		self.macdomains = '' #a list of all macdomain objects, as there is only one right now, it is a string
		self.tn = TelnetAccess(self.ip, IOS_UID, IOS_PW) # creates a telnet obj and logs into cmts stays logged in
    
	def createMacDomain(self, iface):
		self.macdomains  = MacDomain(iface)

	def getCMs(self):
		self.tn.runCommand('show cable modem cable ' + str(self.macdomains.name))

	def getCMverbose(self, cmmac):
		self.tn.runCommand('show cable modem ' + cmmac + ' verbose')
		#print ('show cable modem ' + cmmac + ' verbose')

	def __del__(self):
		self.tn.closeTN() 	# close telnet connection
		del self.tn 		# delete object


class MacDomain(object):
	def __init__(self, name):
		self.name = name

	def extractData(self):
		#Step 2.1:  #Reading and filtering the cmts output to include only modems
		#by deleteing first 4 and last 2 lines, file is stored in cleanedlist
		fin = open('/home/tbsadmin/projects/dscript/static/telnetoutput', 'r')
		cleanedlist = []
		for line in fin: 
			cleanedlist.append(line)
		del cleanedlist[0:4]
		del cleanedlist[len(cleanedlist)-1]
		del cleanedlist[len(cleanedlist)-1]
		global CM_TOTAL
		CM_TOTAL = len(cleanedlist)
		fin.close()
		#print ('Total modems on card: %d' % self.cmtotal)
	
		"""
		#Step 2.2 : - Line by line the cleanedlist is splitted into its values
					- Modem is then created with these inital values. After data has been written added and written into the file, this object
					  is then deleted (to clear all values).	
		"""
		cmdatafromcmts = []
		for line in cleanedlist:
			modem = Modem() 
			del cmdatafromcmts[:]
			cmdatafromcmts = line.split()
			
			modem.mac = cmdatafromcmts[0].strip()
			modem.ip = cmdatafromcmts[1].strip()
			modem.iface = cmdatafromcmts[2].strip()
			modem.state = cmdatafromcmts[3].strip()
			modem.rxpwr = cmdatafromcmts[5].strip()
			
			print "Modem Mac: " + cmdatafromcmts[0]

			#Step 2.3 : - Telneting to cmts, running verbose command, storing output in telnetoutput
			#           - Filtering verbose values and adding them to created modem object   
			ubr01shr.getCMverbose(cmdatafromcmts[0])
			modem.setUSData()
		
			#Step 2.4 : - Gathering CM DS Data by SNMP and storing them in created modem object
			modem.setDSData()

			#Step 2.5: writing <tr> with all the modem values into ./result.html, the returned file by AJAX
			if 'DOC3.0' in modem.macversion:
				self.writeD3data(modem)
			else:
				self.writeD2data(modem)
			# !DEBUG: ISSUE 5.2 setting a timeout. This should give the app enough time to write the complete data into the file
			# time.sleep(2)
			global CM_COUNT
			CM_COUNT+=1
			writeState();
			del modem
	
	def writeD3data(self, modem):
		RESULT.write('<tr>')
		RESULT.write('<td>' + modem.mac + '</td>')
		RESULT.write('<td>' + modem.ip + '</td>')
		RESULT.write('<td>' + modem.iface + '</td>')
		RESULT.write('<td>' + modem.state + '</td>')
		RESULT.write('<td>' + modem.rxpwr + '</td>')
		
		for value in modem.macversion:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.upsnr:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.receivedpwr:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.reportedtransmitpwr:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.dspwr:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.toff:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.uncorrectables:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.flaps:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.errors:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.reason:
			RESULT.write('<td>' + value + '</td>')
			
		for value in modem.docsIfDownChannelPower:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfSigQSignalNoise:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfSigQUncorrectables:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfSigQMicroreflections:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusTxPower:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusInvalidUcds:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusT3Timeouts:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusT4Timeouts:
			RESULT.write('<td>' + value + '</td>')
		
		RESULT.write('</tr>')
		
	def writeD2data(self, modem):
	
		#First empty cells need to be created in the lists, so D3 and D2 Values can be displayed in the same table
		#Upstream 
		modem.upsnr.append('-')
		modem.receivedpwr.append('-')
		modem.reportedtransmitpwr.append('-')
		modem.reportedtransmitpwr.append('-')
		modem.toff.insert(1,'-')
		modem.toff.insert(3,'-')
		modem.uncorrectables.append('-')
		modem.reason.append('-')
		
		#Downstream
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
		
		#Writing table row
		RESULT.write('<tr>')
		RESULT.write('<td>' + modem.mac + '</td>')
		RESULT.write('<td>' + modem.ip + '</td>')
		RESULT.write('<td>' + modem.iface + '</td>')
		RESULT.write('<td>' + modem.state + '</td>')
		RESULT.write('<td>' + modem.rxpwr + '</td>')
		
		#Upstream
		for value in modem.macversion:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.upsnr:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.receivedpwr:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.reportedtransmitpwr:
			RESULT.write('<td>' + value + '</td>')	
		for value in modem.dspwr:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.toff:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.uncorrectables:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.flaps:
			RESULT.write('<td>' + value + '</td>')	
		for value in modem.errors:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.reason:
			RESULT.write('<td>' + value + '</td>')
			
		#Downstream
		for value in modem.docsIfDownChannelPower:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfSigQSignalNoise:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfSigQUncorrectables:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfSigQMicroreflections:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusTxPower:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusInvalidUcds:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusT3Timeouts:
			RESULT.write('<td>' + value + '</td>')
		for value in modem.docsIfCmStatusT4Timeouts:
			RESULT.write('<td>' + value + '</td>')
			
		RESULT.write('</tr>')
		

class Modem(object):
	snmpcommunity = 'web4suhr'
	def __init__(self):
		#To keep things simple, I created list for all attributes
		#but the initial ones. Even if they only take one attribute
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
    
	#Setting data gathered from cmts verbose, flaps, erros and dspwr are strings
	def setUSData(self):
		fin = open('/home/tbsadmin/projects/dscript/static/telnetoutput', 'r')
		for line in fin:
			#each line is checked for the expression, the splitted into values, first ":" as perimeter,
			#then to seperate multiple values (Bondend), it is splitted again with " "
			if 'MAC Version' in line:
				value = line.split(':')
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
		fin.close()

	#Setting data gathered from CM by SNMP
	#TEST: The values needs to be checked as dictionaries are generally unsorted!
	def setDSData(self):
		if 'online' in self.state:
			#CM_ONLINE counts the amount of online modems snmp requests are sent to 
			#this will then be displayed as soon as script finishes
			global CM_ONLINE
			CM_ONLINE += 1
			
			# !DEBUG: Disable SNMP						
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
		snmpvalue = {}  #dictionary which will be returned
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
		#snmpvalue.append(val.prettyPrint())
		#print snmpvalue
		return snmpvalue

class TelnetAccess(object):
	# Defining regular expressions for the different prompts here
	ios_unprivPrompt = re.compile ('.*>')
	ios_privPrompt = re.compile ('.*#')
	regexlist = [ios_unprivPrompt, ios_privPrompt, 'Username:', 'Password:', 'username:', 'password:']

	def __init__(self, ip, uid, password):
		self.ip = ip
		self.uid = uid
		self.password = password
		self.telnetoutput = ''

		#Connecting to host
		self.tn = telnetlib.Telnet(self.ip)

		#IOS Login prodedure (unpriv -> enable -> priv)
		self.tn.expect(TelnetAccess.regexlist) #regexlist is global
		self.tn.write(self.uid + "\n")
		self.tn.expect(TelnetAccess.regexlist)
		self.tn.write(self.password + "\n")
		self.tn.expect(TelnetAccess.regexlist)
		#time.sleep(1) #Setting a delay, otherwise prg. execution to fast and command is run before telnet obj is init.

	def runCommand(self,command):
		#Opening filehandle
		self.telnetoutput = open('/home/tbsadmin/projects/dscript/static/telnetoutput', 'w')		
		#Executing command and returning output
		#self.tn.expect(TelnetAccess.regexlist)
		self.tn.write(command + "\n")
		# !DEBUG: ISSUE 5.1 - Setting Timeout from 0.3 to 0.75 s, giving the app enought time to write the commands output
		time.sleep(0.5) 
		output = self.tn.read_very_eager()
		self.telnetoutput.write(output)

		#Close filehandle
		self.telnetoutput.close()

	def closeTN(self):
		self.tn.close()


def createHTMLHeader():
	RESULT.write('<!DOCTYPE HTML>')
	RESULT.write('<html>')
	RESULT.write('<head>')
	RESULT.write('<meta charset="utf-8">')
	RESULT.write('<style type="text/css">td {color:blue; white-space:nowrap} </style>')
	RESULT.write('</head>')
	RESULT.write('<body>')
	
def createTableHeader():
	RESULT.write('<table border=1>')
	RESULT.write('<tr>')
	RESULT.write('<th>mac</th>')
	RESULT.write('<th>ip</th>')
	RESULT.write('<th>iface</th>')
	RESULT.write('<th>state</th>')
	RESULT.write('<th>rxpwr</th>') 
	RESULT.write('<th>Docsis</th>')
	RESULT.write('<th>upsnr</th>')
	RESULT.write('<th>upsnr</th>')
	RESULT.write('<th>receivedpwr</th>')
	RESULT.write('<th>receivedpwr</th>')
	RESULT.write('<th>reportedtransmitpwr</th>')
	RESULT.write('<th>reportedtransmitpwr</th>')
	RESULT.write('<th>dspwr</th>')
	RESULT.write('<th>toff</th>')
	RESULT.write('<th>toff</th>')
	RESULT.write('<th>init toff</th>')
	RESULT.write('<th>init toff</th>')
	RESULT.write('<th>uncorrectables</th>')
	RESULT.write('<th>uncorrectables</th>')
	RESULT.write('<th>flaps</th>')
	RESULT.write('<th>errors</th>')
	RESULT.write('<th>reason</th>')
	RESULT.write('<th>docsIfDownChannelPower</th>')
	RESULT.write('<th>docsIfDownChannelPower</th>')
	RESULT.write('<th>docsIfDownChannelPower</th>')
	RESULT.write('<th>docsIfDownChannelPower</th>')
	RESULT.write('<th>docsIfSigQSignalNoise</th>')
	RESULT.write('<th>docsIfSigQSignalNoise</th>')
	RESULT.write('<th>docsIfSigQSignalNoise</th>')
	RESULT.write('<th>docsIfSigQSignalNoise</th>')
	RESULT.write('<th>docsIfSigQUncorrectables</th>')
	RESULT.write('<th>docsIfSigQUncorrectables</th>')
	RESULT.write('<th>docsIfSigQUncorrectables</th>')
	RESULT.write('<th>docsIfSigQUncorrectables</th>')
	RESULT.write('<th>docsIfSigQMicroreflections</th>')
	RESULT.write('<th>docsIfSigQMicroreflections</th>')
	RESULT.write('<th>docsIfSigQMicroreflections</th>')
	RESULT.write('<th>docsIfSigQMicroreflections</th>')
	RESULT.write('<th>docsIfCmStatusTxPower</th>')
	RESULT.write('<th>docsIfCmStatusInvalidUcds</th>')
	RESULT.write('<th>docsIfCmStatusT3Timeouts</th>')
	RESULT.write('<th>docsIfCmStatusT4Timeouts</th>')
	RESULT.write('</tr>')
	
def createHTMLFooter():
	RESULT.write('</table>')
	RESULT.write('</body>')
	RESULT.write('</html>')
		

#Writes the counter and running state into the status file which is read by ajax
def writeState(): #writes the modem and runstatus of the app into a file. This file serves as a counter for ajax
	data = {'CM_TOTAL' : CM_TOTAL, 'CM_COUNT': CM_COUNT, 'CM_ONLINE' : CM_ONLINE, 'RUN_STATE' : RUN_STATE}
	STATUS.seek(0)	#move to beginning of file
	STATUS.write(json.dumps(data))

# !MAIN

RUN_STATE = 1	#states if the script is running (0=no, 1=yes)
CM_TOTAL = ''	#holds all CM in macdomain
CM_COUNT = 0	#holds number of processed modems
CM_ONLINE = 0	#this counter counts only online modems
IOS_UID = 'dscript'
IOS_PW = 'hf4ev671'
RESULT = open('/home/tbsadmin/projects/dscript/static/result.html', 'w')	#Holds the file which will be returned by ajax
STATUS = open('/home/tbsadmin/projects/dscript/static/status', 'w')			#holds counter values and runstate
#DEBUG = open('/home/tbsadmin/projects/dscript/static/debug', 'w')

"""
Step 1: Create CMTS Object, telnet cmts and login, issue command, receive cm list
		Just to test this script the mac domain is entered manually into this script
"""

# 1.1 - Creating html and table header 
createHTMLHeader()
createTableHeader()

# 1.2 - Receiving argv value, telneting to cmts 
argv = str(sys.argv[1])

ubr01shr = Cmts('10.10.10.50', 'ubr01shr')

ubr01shr.createMacDomain(argv)

ubr01shr.getCMs()

""" Step 2 (2.1 - 2.5):	- Extract Data from cm list (telnet output from cmts)
						- Create Modem Object
						- Populate CM values from CMTS and CM (SNMP)
						- Add all CMs to macdomain.clist	 
"""

ubr01shr.macdomains.extractData()	 
 	
"""
#Step 3 - Creating HTML footer and cleaning up
"""
createHTMLFooter()

#Cleaning up
del ubr01shr
RUN_STATE=0
writeState()
STATUS.close()
RESULT.close()

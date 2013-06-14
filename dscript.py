#!/usr/bin/python
"""
	Version:	0.1 - Beta
	Author:		Memleak13
	Date:		13.06.13
"""
#My modules
from table import Table

#Other modules
import re
import sys
import time 
import datetime      
import telnetlib
import json
from pysnmp.entity.rfc3413.oneliner import cmdgen


class Cmts(object):
	"""Represents a cmts.
	
	It is identified by its name and IP address.
	It contains the macdomain domain which includes the requsted modems.
	It creates a telnet object when initilized. The telnet object is 
	used to access the cmts and run commands. The session stays open until the 
	object is destroyed.
	"""
	
	def __init__(self, ip, name):
		"""Inits cmts with ip, name and telnet object.
		
		Args:
			ip: ip address
			name: the name of the device, also used for the telnet prompt
		"""
		self.ip = ip
		self.name = name
		self.tn = TelnetAccess(self.ip, self.name, IOS_UID, IOS_PW) 
    
	def createMacDomain(self, iface, topology):
		"""Creates and stores the mac domain.
		
		See MacDomain class.
		
		Args:
			iface: the macdomain selected by the user
		"""
		self.macdomains  = MacDomain(iface, topology)

	def getCMs(self):
		"""Retrieves all modems in the specified macdomain
		
		By running the ios command "show cable modem cable [macdomain]"
		The output is written into the file telnetoutput
		"""
		self.tn.runCommand('show cable modem cable ' + str(self.macdomains.name))

	def getCMverbose(self, cmmac):
		"""Retroves values for a specific cable modem.
		
		By running the ios comand "show cable modem [mac] verbose.
		The output is written into the file telnetoutput
		
		Args:
			cmmac: mac address of the cable modem
		"""
		self.tn.runCommand('show cable modem ' + cmmac + ' verbose')

	def __del__(self):
		"""Closes and deletes the telnet connection"""
		self.tn.closeTN() 	# close telnet connection
		del self.tn 		# delete object

class MacDomain(object):
	"""Represents the mac domain.
	
	Identified by its name (the macdomain selected by the user).
	It contains a list of all cable modems in this domain by filtering
	the cmts output. 
	"""
		
	def __init__(self, name, topology):
		"""Inits the macdomain
		
		Args:
			name: represents the mac domain (ex. c5/1/0)
			topology: HFC topology
		"""
		self.name = name
		self.topology = topology
		self.table = Table(topology) 

	def extractData(self):
		"""Extracts and filters modem values.
		
		Filters the cmts output to contain just modems.
		Creates a modem object where it stores US and DS information for each 
		modem by retrieving the data from the cmts(US) over telnet and from the 
		cable modem over snmp(DS). Finally it writes this data into an html 
		file (result.html).
		
		Refers to step 2.1 - 2.5
		"""
		
		#Step 2.1: Reading and filtering the cmts output to include only modems
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
		
		#Step 2.2: Modem object is created with initial values.
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
			
			#Step 2.3: Setting US and other values retrieved from the cmts
			ubr01shr.getCMverbose(cmdatafromcmts[0])
			modem.setUSData()
		
			#Step 2.4: 	Setting DS data retrieved from the modem 
			# 			except (D1 Modems)
			if 'DOC3.0' in modem.macversion or 'DOC2.0' in modem.macversion:
				modem.setDSData()
				
			#Step 2.5: Writting html ouptut 
			if 'DOC3.0' in modem.macversion:
				self.table.adjust_4_d3(modem)
			
			elif 'DOC2.0' in modem.macversion:
				self.table.adjust_4_d2(modem)
			
			else:
				self.table.adjust_4_d1(modem)

			global CM_COUNT
			CM_COUNT+=1
			writeState();
			del modem
	
class Modem(object):
	"""Represents the modem.
	
	Includes all docis values retreived by the cmts or modem.
	Connects to the modem using snmp.
	"""
	
	snmpcommunity = 'web4suhr'
	def __init__(self):
		"""Inits modem setting all attributes to empty values
		
		To keep things simple, I created lists for all attributes except the
		initial ones. Even if they only take one attribute.
		"""
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
    
	def setUSData(self):
		"""Sets US Data"""
		fin = open('/home/tbsadmin/projects/dscript/static/telnetoutput', 'r')
		for line in fin:
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
		fin.close()

	def setDSData(self):
		"""Sets DS Data."""
		if 'online' in self.state:
			global CM_ONLINE
			CM_ONLINE += 1					
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
			DEBUG = open('/home/tbsadmin/projects/dscript/static/debug', 'a') #Debug
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
		
		Writes the output into a file
		
		Args:
			command: whatever could this stand for ...
		"""
		self.telnetoutput = open(
			'/home/tbsadmin/projects/dscript/static/telnetoutput', 'w')		
		self.tn.write(command + "\n")
		output = self.tn.read_until(self.prompt)
		self.telnetoutput.write(output)
		self.telnetoutput.close()

	def closeTN(self):
		"""Close connection"""
		self.tn.close()
		
def writeState(): 
	"""Writes stats into file
	
	These stats serve as a modem counter and includes the running state  of the
	script.
	"""
	data = {'CM_TOTAL' : CM_TOTAL, 'CM_COUNT': CM_COUNT, 
			'CM_ONLINE' : CM_ONLINE, 'RUN_STATE' : RUN_STATE}
	STATUS.seek(0)
	STATUS.write(json.dumps(data))

#TODO: Add following to main() 

RUN_STATE = 1	#states if the script is running (0=no, 1=yes)
CM_TOTAL = ''	#holds all CM in macdomain
CM_COUNT = 0	#holds number of processed modems
CM_ONLINE = 0	#this counter counts only online modems
IOS_UID = 'dscript'
IOS_PW = 'hf4ev671'
STATUS = open('/home/tbsadmin/projects/dscript/static/status', 'w') #Stats

#Step 1.1 - Receiving argv(mac domain), create cmts, macdomain etc...
macdomain = str(sys.argv[1])
topology = str(sys.argv[2])

ubr01shr = Cmts('10.10.10.50', 'ubr01SHR') #Case Sensitiv, used for telnet prompt
ubr01shr.createMacDomain(macdomain, topology)
ubr01shr.getCMs()

#Step 2.1 - 2.5: Retrieve, filter data
ubr01shr.macdomains.extractData()	 

#Step 3 - Cleaning up
ubr01shr.macdomains.table.create_html_footer()
ubr01shr.macdomains.table.result.close()
RUN_STATE=0
writeState()
STATUS.close()
del ubr01shr.macdomains.table
del ubr01shr


#!/usr/bin/python
"""
    Version:	0.1.1 - New Concept using webpy and ajax instead of plain old simple cgi 
    Author: 	Memleak13
    Date: 	03.05.13

    BUG: rxpwr = psid -> needs to be corrected, wrong field is extracted!
	
"""

import cgi,cgitb
import re
import sys
import time
import telnetlib
from pysnmp.entity.rfc3413.oneliner import cmdgen

cgitb.enable()

#Class Definitions
class Cmts(object):
    def __init__(self, ip, name):
        self.ip = ip
	self.name = name
        self.macdomains = '' #a list of all macdomain objects, as there is only one right now, it is a string
	self.tn = TelnetAccess(self.ip, IOS_UID, IOS_PW) # creates a telnet obj and logs into cmts stays logged in
    
    def createMacDomain(self, iface):
	self.macdomains  = MacDomain(iface)

    def getCMs(self):
	self.tn.runCommand('show cable modem cable ' + ubr01shr.macdomains.name)

    def getCMverbose(self, cmmac):
	self.tn.runCommand('show cable modem ' + cmmac + ' verbose')
	#print ('show cable modem ' + cmmac + ' verbose')

    def __del__(self):
	self.tn.closeTN() 	# close telnet connection
	del self.tn 		# delete object
	

class MacDomain(object):
    def __init__(self, name):
	self.name = name
	self.cmtotal = '' # total cm in macdomain
        self.cmlist = []  # a list of all cm objects in this mac domain
    
	def extractData(self):
	
	#Step 2.1:  #Reading and filtering the cmts output to include only modems
		    #by deleteing first 4 and last 2 lines, file is stored in cleanedlist
	
	fin = open  ('./telnetoutput', 'r') #('./test','r') #in production change to telnetoutput
	cleanedlist = []
	for line in fin: 
        	cleanedlist.append(line)
	del cleanedlist[0:4]
	del cleanedlist[len(cleanedlist)-1]
	del cleanedlist[len(cleanedlist)-1]
	self.cmtotal = len(cleanedlist)
	fin.close()
	print ('Total modems on card: %d' % self.cmtotal)
	
	#Step 2.2 : - Line by line the cleanedlist is splitted into its values
	#           - Modem is then created with these values	
	
	cmdatafromcmts = []
	for line in cleanedlist:
		del cmdatafromcmts[:]
		cmdatafromcmts = line.split()
		modem = Modem(cmdatafromcmts[0].strip(),cmdatafromcmts[1].strip(),cmdatafromcmts[2].strip(),cmdatafromcmts[3].strip(),cmdatafromcmts[5].strip())
		print "Modem Mac: " + cmdatafromcmts[0]

		#Step 2.3 : - Telneting to cmts, running verbose command, storing output in telnetoutput
		#           - Filtering verbose values and adding them to created modem object   
		ubr01shr.getCMverbose(cmdatafromcmts[0])
		modem.setUSData()
		
		#Step 2.4 : - Gathering CM DS Data by SNMP and storing them in created modem object
                modem.setDSData()

		#Step 2.5: adding the CM to the modemlist
		self.cmlist.append(modem)


class Modem(object):
    snmpcommunity = 'web4suhr'
    def __init__(self, mac, ip, iface, state, rxpwr):
	#To keep things simple, I created list for all attributes
	#but the initial ones. Even if they only take one attribute
	
        self.mac = mac
        self.ip = ip
        self.iface = iface
        self.state = state
        self.rxpwr = rxpwr
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
    	fin = open ('./telnetoutput', 'r')
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
		#ONLINE counts the amount of online modems snmp requests are sent to 
		#this will then be displayed as soon as script finishes
		global ONLINE
		ONLINE += 1

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
                self.telnetoutput = open('telnetoutput', 'w')
    		
		#Executing command and returning output
    		#self.tn.expect(TelnetAccess.regexlist)
    		self.tn.write(command + "\n")
    		time.sleep(0.3)
    		output = self.tn.read_very_eager()
    		self.telnetoutput.write(output)

		#Close filehandle
		self.telnetoutput.close()

	def closeTN(self):
		self.tn.close()


#Main

#Global Parameters
IOS_UID = 'dscript'
IOS_PW = 'hf4ev671'
ONLINE = 0  #DEBUG, for comparing performance. This counter counts every online modem, while running through the script

# Step 1: Receive US value from drop down menu using CGI, Create CMTS Object, telnet cmts and login, issue command
#	  receive cm list

# 1.1 - CGI Processing
form = cgi.FieldStorage() # instantiate only once!
selected  =  form.getfirst('us', 'empty')
# Avoid script injection escaping the user input
selected = cgi.escape(selected)

print "Content-type:text/html\r\n\r\n"
print "<!DOCTYPE HTML>"
print "<html>"
print "<head>"
print selected
print "</head>"
print "<body>"


# 1.2 - Script Processing
ubr01shr = Cmts('10.10.10.50', 'ubr01shr')
ubr01shr.createMacDomain(selected)
ubr01shr.getCMs()

# Step 2 (2.1 - 2.5): - Extract Data from cm list (telnet output from cmts)
#		      - Create Modem Object
#		      - Populate CM values from CMTS and CM (SNMP)
#		      - Add all CMs to macdomain.clist	 

ubr01shr.macdomains.extractData()	  	
print ('Total modems on card: %d' % ubr01shr.macdomains.cmtotal)

# Step 3 - Creating Output
#print "Content-type:text/html\r\n\r\n"
#print "<!DOCTYPE HTML>"
#print "<html>"
#print "<head>"
#print selected
#print "</head>"
#print "<body>"

print "<table border=1>"
print "<tr>"
print "<th>mac</th>"
print "<th>ip</th>"
print "<th>iface</th>"
print "<th>state</th>"
print "<th>rxpwr</th>" 
print "<th>Docsis</th>"
print "<th>upsnr</th>"
print "<th>upsnr</th>"
print "<th>receivedpwr</th>"
print "<th>receivedpwr</th>"
print "<th>reportedtransmitpwr</th>"
print "<th>reportedtransmitpwr</th>"
print "<th>dspwr</th>"
print "<th>toff</th>"
print "<th>toff</th>"
print "<th>toff</th>"
print "<th>toff</th>"
print "<th>uncorrectables</th>"
print "<th>uncorrectables</th>"
print "<th>flaps</th>"
print "<th>errors</th>"
print "<th>reason</th>"
print "<th>docsIfDownChannelPower</th>"
print "<th>docsIfDownChannelPower</th>"
print "<th>docsIfDownChannelPower</th>"
print "<th>docsIfDownChannelPower</th>"
print "<th>docsIfSigQSignalNoise</th>"
print "<th>docsIfSigQSignalNoise</th>"
print "<th>docsIfSigQSignalNoise</th>"
print "<th>docsIfSigQSignalNoise</th>"
print "<th>docsIfSigQUncorrectables</th>"
print "<th>docsIfSigQUncorrectables</th>"
print "<th>docsIfSigQUncorrectables</th>"
print "<th>docsIfSigQUncorrectables</th>"
print "<th>docsIfSigQMicroreflections</th>"
print "<th>docsIfSigQMicroreflections</th>"
print "<th>docsIfSigQMicroreflections</th>"
print "<th>docsIfSigQMicroreflections</th>"
print "<th>docsIfCmStatusTxPower</th>"
print "<th>docsIfCmStatusInvalidUcds</th>"
print "<th>docsIfCmStatusT3Timeouts</th>"
print "<th>docsIfCmStatusT4Timeouts</th>"
print "</tr>"

for cm in ubr01shr.macdomains.cmlist:
	if "DOC3.0" in cm.macversion:
		print "<tr>"
		print "<td>" + cm.mac + "</td>"
		print "<td>" + cm.ip + "</td>"
		print "<td>" + cm.iface + "</td>"
		print "<td>" + cm.state + "</td>"
		print "<td>" + cm.rxpwr + "</td>"

		for value in cm.macversion:
			print "<td>" + value + "</td>"
                for value in cm.upsnr:
                        print "<td>" + value + "</td>"
                for value in cm.receivedpwr:
                        print "<td>" + value + "</td>"
                for value in cm.reportedtransmitpwr:
                        print "<td>" + value + "</td>"
                for value in cm.dspwr:
                        print "<td>" + value + "</td>"
                for value in cm.toff:
                        print "<td>" + value + "</td>"
                for value in cm.uncorrectables:
                        print "<td>" + value + "</td>"
                for value in cm.flaps:
                        print "<td>" + value + "</td>"
                for value in cm.errors:
                        print "<td>" + value + "</td>"
                for value in cm.reason:
                        print "<td>" + value + "</td>"

                for value in cm.docsIfDownChannelPower:
                        print "<td>" + value + "</td>"
                for value in cm.docsIfSigQSignalNoise:
                        print "<td>" + value + "</td>"
                for value in cm.docsIfSigQUncorrectables:
                        print "<td>" + value + "</td>"
                for value in cm.docsIfSigQMicroreflections:
                        print "<td>" + value + "</td>"
                for value in cm.docsIfCmStatusTxPower:
                        print "<td>" + value + "</td>"
                for value in cm.docsIfCmStatusInvalidUcds:
                        print "<td>" + value + "</td>"
                for value in cm.docsIfCmStatusT3Timeouts:
                        print "<td>" + value + "</td>"
                for value in cm.docsIfCmStatusT4Timeouts:
                        print "<td>" + value + "</td>"
		print "</tr>"

		

print "</table>"
print "</body>"
print "</html>"


"""
#Debug
for cm in ubr01shr.macdomains.cmlist:
	print 'mac:                         ' + cm.mac
	print 'ip:                          ' + cm.ip
	print 'iface:                       ' + cm.iface
	print 'state:                       ' + cm.state
	print 'rxpwr:                       ' + cm.rxpwr

	for value in cm.macversion:
                print 'macversion:                  ' + value
        for value in cm.upsnr:
                print 'upsnr:                       ' + value
        for value in cm.receivedpwr:
                print 'receivedpwr:                 ' + value
        for value in cm.reportedtransmitpwr:
                print 'reportedtransmitpwr:         ' + value
        for value in cm.dspwr:
                print 'dspwr:                       ' + value
        for value in cm.toff:
                print 'toff:                        ' + value
        for value in cm.uncorrectables:
                print 'uncorrectables:              ' + value
        for value in cm.flaps:
                print 'flaps:                       ' + value
        for value in cm.errors:
                print 'errors:                      ' + value
        for value in cm.reason:
                print 'reason:                      ' + value
	
	for value in cm.docsIfDownChannelPower:
		print 'docsIfDownChannelPower:      ' + value
        for value in cm.docsIfSigQSignalNoise:
                print 'docsIfSigQSignalNoise:       ' + value
        for value in cm.docsIfSigQUncorrectables:
                print 'docsIfSigQUncorrectables:    ' + value
        for value in cm.docsIfSigQMicroreflections:
                print 'docsIfSigQMicroreflections:  ' + value
        for value in cm.docsIfCmStatusTxPower:
                print 'docsIfCmStatusTxPower:       ' + value        
	for value in cm.docsIfCmStatusInvalidUcds:
                print 'docsIfCmStatusInvalidUcds:   ' + value
        for value in cm.docsIfCmStatusT3Timeouts:
                print 'docsIfCmStatusT3Timeouts:    ' + value
        for value in cm.docsIfCmStatusT4Timeouts:
                print 'docsIfCmStatusT4Timeouts:    ' + value
	print "**********************************\n\n"

"""
print 'ONLINE %d' % ONLINE

#Closing up
del ubr01shr



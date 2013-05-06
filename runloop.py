#! /usr/bin/python
# First this script writes the final page, then it loops through a counter entering the momentary count
# into a file which is then read from the app when am ajax call has been made. Once the script
# has finished it enters a status of 1 into the script. This tells the app, if the script is 
# allready running or not
import sys
import json

data = {}

datafinal = open('/var/www/dscript/static/datafileFinalCall', 'w')
datafinal.write (":)))) This was the final Ajax call, returning the static website")
datafinal.close()

datacount = open('/var/www/dscript/static/datafileCount', 'w')
total = 500000
for i in range(total+1):
	data = {'total' : total, 'count': i, 'status' : 0}
	datacount.seek(0)
	datacount.write(json.dumps(data))

data ['status'] = 1
datacount.seek(0)
datacount.write(json.dumps(data))
datacount.close()

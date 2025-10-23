import os
import paramiko
import sqlite3
from getpass import getpass
import fnmatch
import pandas as pd
import tarfile
import gzip
import datetime
import subprocess
from pathlib import Path
import xlsxwriter
import socket
from tsbuddy import extracttar
import time
import argparse


#
#Limitations
#This application does not support switches in standalone mode

#
#TODO
#TODO: Redo ImportAnother
#TODO: Add Reboot Reason
#TODO: If all logs are in Epoch time
#TODO: Remove Unused Logs
#TODO: X logs before and after targetlog
#TODO: Integrate Tech Support downloader
#TODO: 9907s have per NI logs
#TODO: Add another TS? For comparing a timeline of multiple switches?
	#Update Reboots to account for multiple TS
	#Error for same TS twice
#TODO: Multiswitch time correlation? Anchor logs?
#TODO: Log Count per day/hour/minute
#TODO: Add Wireless Log Support
	#This may be another program, or just a subsection of it
		#Unsure if we can mix Switch and AP logs
#TODO: There is the ability to change the log formatting to match a standard. Add support for it.
	#Pending command
#TODO: Add GUI


"""
Implemented categories:
Reboot
Interface
Unused

WIP categories:
All Logs 
VC
OSPF
SPB
Health
Connectity
Critical
Hardware
Upgrades
General
MACLearning
STP
Security
Unclear
Unknown
"""

#Known issues:
#
#
#


"""
Analysis draft.
Select "Look for Problems>Find Root Cause"
"Please enter a timeframe for the issue. Leave this blank if there is not a known timeframe"
select count(*),LogMessage from logs where Timestamp (if applicable) group by LogMessage order by count(*) desc limit 500
for LogMessage in output:
	Categorize
	category.append()
Find largest category that isn't "unused"
"The logs primarily consist of +category+ logs. Running analysis for +category
Autorun "Look of Problems>Category"

"""


"""
Changes from LogParserv2:
1. Not carrying over collect_hosts(). Any log collection will be handled by another tsbuddy module. Though we might want to be able to call from here.
2. This includes not carrying over grab_logs()
"""



SwlogFiles1 = []
SwlogFiles2 = []
SwlogFiles3 = []
SwlogFiles4 = []
SwlogFiles5 = []
SwlogFiles6 = []
SwlogFiles7 = []
SwlogFiles8 = []
ConsoleFiles = []

SwlogDir1 = ""
SwlogDir1B = ""
SwlogDir2B = ""
SwlogDir2 = ""
SwlogDir3 = ""
SwlogDir4 = ""
SwlogDir5 = ""
SwlogDir6 = ""
SwlogDir7 = ""
SwlogDir8 = ""

PrefSwitchName = "None"

AnalysisInitialized = False

RebootsInitialized = False
VCInitialized = False
InterfaceInitialized = False
OSPFInitialized = False
SPBInitialized = False
HealthInitialized = False
ConnectivityInitialized = False
CriticalInitialized = False
UnusedInitialized = False
AllLogsInitialized = False


CriticalRan = False
RebootsRan = False
VCRan = False
InterfaceRan = False
OSPFRan = False
SPBRan = False
HealthRan = False
ConnectivityRan = False
AllLogsRan = False


TSImportedNumber = 0




dir_list = os.listdir()

first_dir_list = os.listdir()

archive_checked = False



def APLogFind(conn,cursor):
	try:
		cursor.execute("create table Logs(id integer primary key autoincrement, TSCount Text, ChassisID Text, Filename Text, Timestamp Text, SwitchName Text, Source Text, Model Text, AppID Text, Subapp Text, Priority text, LogMessage text)")
	except:
		pass
	APLogFiles = []
	for item in dir_list:
		print(item)
		if fnmatch.fnmatch(item, "*.log*"):
			APLogFiles.append(item)
		if fnmatch.fnmatch(item, "*.record*"):
			APLogFiles.append(item)
		if fnmatch.fnmatch(item, "*.txt*"):
			APLogFiles.append(item)
	for file in APLogFiles:
		#print(file)
		Filename = file
		with open(file, 'rt', errors='ignore',encoding='utf-8') as file:
			LogByLine = file.readlines()
			APReadandParse(LogByLine,conn,cursor,Filename)
	cursor.execute("select * from Logs")
	Output = cursor.fetchall()
	#for line in Output:
	#	print(line)
	try:
		with pd.ExcelWriter("APLogTest.xlsx",engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
			print("Exporting data to file. This may take a moment.")
			if TSImportedNumber > 1:
				Output = pd.read_sql("select * from Logs", conn)
			else:
				Output = pd.read_sql("select * from Logs", conn)	
				Output.to_excel(writer, sheet_name="ConsolidatedLogs")
				workbook = writer.book
				worksheet = writer.sheets["ConsolidatedLogs"]
				text_format = workbook.add_format({'num_format': '@'})
				worksheet.set_column("H:H", None, text_format)
		print("Export complete. Your logs are in APLogTest.xlsx")
	except:
		print("Unable to write the file. Check if a file named APLogTest.xlsx is already open")
	
def APReadandParse(LogByLine,conn,cursor,Filename):
	TSCount = TSImportedNumber
	match Filename:
		case "iot-radio-manage.log":
			for line in LogByLine:
				#debug prints
				#print(len(line))
				#print(Filename)
				#print(line)
				#skip empty lines
				if len(line) < 2:
					continue
				#Remove null characters
				line = line.replace('\0',"")
				#Remove (epoch)
				###Regex does not work
				#line = line.replace('\(.*\)', "")
				###Fix this
				TimeStamp = line[0:19]
				line = line.replace("  ", " ")
				parts = line.split(" [")
				TimeStamp = parts[0]
				line2 = parts[1]
				line2 = line2.replace("]", "")
				parts2 = line2.split(" - ")
				AppID = parts2[0]
				SubApp = parts2[1]
				LogMessage = parts2[2]
				LogMessage = LogMessage.strip()
				#single quotes break the function
				LogMessage = LogMessage.replace("'","")
				LogMessage = LogMessage.encode('utf-8')
				LogMessage = str(LogMessage)
				LogMessage = LogMessage.replace("b'","")
				LogMessage = LogMessage.replace("'","")
				cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, AppID, SubApp, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+AppID+"','"+SubApp+"','"+LogMessage+"')")
		case "cgi.log":
			for line in LogByLine:
				#debug prints
				#print(len(line))
				#print(Filename)
				#print(line)
				#skip empty lines
				if len(line) < 2:
					continue
				#Remove null characters
				line = line.replace('\0',"")
				line.replace("[","")
				parts = line.split("]")
				TimeStamp = parts[0]
				LogMessage = parts[1]
				#single quotes break the function
				LogMessage = LogMessage.replace("'","")
				LogMessage = LogMessage.encode('utf-8')
				LogMessage = str(LogMessage)
				LogMessage = LogMessage.replace("b'","")
				LogMessage = LogMessage.replace("'","")
				cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
		case "cert.log":
			for line in LogByLine:
				if len(line) < 2:
					continue
				#Remove null characters
				line = line.replace('\0',"")
				LogMessage = line
				#single quotes break the function
				LogMessage = LogMessage.replace("'","")
				LogMessage = LogMessage.encode('utf-8')
				LogMessage = str(LogMessage)
				LogMessage = LogMessage.replace("b'","")
				LogMessage = LogMessage.replace("'","")
				cursor.execute("insert into Logs (TSCount, Filename, LogMessage) values ('"+str(TSCount)+"','"+Filename+"','"+LogMessage+"')")
		case "cert_manage.log":
			TSCount = TSImportedNumber
			TimeStampLines = []
			LogMessageLines = []
			LineCount = len(LogByLine)
			Counter = 0
			while Counter < LineCount:
				#For even Counter, or Odd Lines
				if Counter % 2 == 0:
					TimeStampLines.append(LogByLine[Counter])
				else:
					LogMessageLines.append(LogByLine[Counter])
				Counter += 1
			LogCount = len(LogMessageLines)
			Counter = 0
			while Counter < LogCount:
				TimeStampRaw = TimeStampLines[Counter]
				LogMessage = LogMessageLines[Counter]
				#Remove null characters
				LogMessage = LogMessage.replace('\0',"")
				#single quotes break the function
				LogMessage = LogMessage.replace("'","")
				#Remove {}
				LogMessage = LogMessage.replace("{","")
				LogMessage = LogMessage.replace("}","")
				TimeStamp = TimeStampRaw.replace('\0',"")
				TimeStamp = TimeStampRaw[1:20]
				#print(TimeStamp)
				#print(LogMessage)
				cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
				Counter += 1
		case "crontab.log":
			TimeStamp_LogMessage_Split(LogByLine,conn,cursor,Filename)
		case "check_nfqueue.record":
			TimeStamp_LogMessage_Split(LogByLine,conn,cursor,Filename)
		case "calog.log":
			Epoch_AppID(LogByLine,conn,cursor,Filename)
		case "activation_clientd.log":
			Epoch_AppID(LogByLine,conn,cursor,Filename)
		case "agm.log":
			Bracket_TimeStamp_LogMessage(LogByLine,conn,cursor,Filename)
		case "ap_manage.log":
			Epoch_AppID(LogByLine,conn,cursor,Filename)
		case "ap_manage.log_back":
			Epoch_AppID(LogByLine,conn,cursor,Filename)
		case "arp-proxy.log":
			for line in LogByLine:
				#debug prints
				#print(len(line))
				#print(Filename)
				#print(line)
				#skip empty lines
				if len(line) < 2:
					continue
				#Remove null characters
				line = line.replace('\0',"")
				TimeStamp = line[0:27]
				TimeStamp = TimeStamp.replace("[","")
				TimeStamp = TimeStamp.replace("]","")
				lineSize = len(line)
				LogMessage = line[28:lineSize]
				LogMessage = LogMessage.strip()
				#single quotes break the function
				LogMessage = LogMessage.replace("'","")
				LogMessage = LogMessage.encode('utf-8')
				LogMessage = str(LogMessage)
				LogMessage = LogMessage.replace("b'","")
				LogMessage = LogMessage.replace("'","")
				cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
		case "baseguard.log":
			for line in LogByLine:
				#debug prints
				#print(len(line))
				#print(Filename)
				#print(line)
				#skip empty lines
				if len(line) < 6:
					continue
				#Remove null characters
				line = line.replace('\0',"")
				parts = line.split(":")
				TimeStampRaw = parts[0]
				Year = TimeStampRaw[0:4]
				Month = TimeStampRaw[4:6]
				Day = TimeStampRaw[6:8]
				Hour = TimeStampRaw[8:10]
				Minute = TimeStampRaw[10:12]
				Second = TimeStampRaw[12:14]
				TimeStamp = (Year+"-"+Month+"-"+Day+" "+Hour+":"+Minute+":"+Second)
				LogMessage = parts[1]
				LogMessage = LogMessage.strip()
				#single quotes break the function
				LogMessage = LogMessage.replace("'","")
				LogMessage = LogMessage.encode('utf-8')
				LogMessage = str(LogMessage)
				LogMessage = LogMessage.replace("b'","")
				LogMessage = LogMessage.replace("'","")
				cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
		case "chan_util.log":
			TimeStampLines = []
			InterfaceLines = []
			ChannelLines = []
			UtilizationLines = []
			NoiseLines = []
			for line in LogByLine:
				 #skip empty lines
				if len(line) < 2:
					continue
				if len(TimeStampLines) == len(NoiseLines):
					parts = line.split(" ")
					Year = parts[4]
					Month = parts[1]
					match Month:
						case "Jan":
							Month = "01"
						case "Feb":
							Month = "02"
						case "Mar":
							Month = "03"
						case "Apr":
							Month = "04"	
						case "May":
							Month = "05"
						case "Jun":
							Month = "06"
						case "Jul":
							Month = "07"
						case "Aug":
							Month = "08"
						case "Sep":
							Month = "09"
						case "Oct":
							Month = "10"
						case "Nov":
							Month = "11"
						case "Dec":
							Month = "12"
					Date = parts[2]
					if len(Date) == 1:
						Date = "0"+str(Date)
					Time = parts[3]
					Timestamp = str(Year)+"-"+Month+"-"+str(Date)+" "+str(Time)
					TimeStampLines.append(Timestamp)
					continue
				if len(TimeStampLines) > len(InterfaceLines):
					line = CleanOutput(line)
					line = line.replace("\n","")
					InterfaceLines.append(line)
					continue
				if len(InterfaceLines) > len(ChannelLines):
					line = CleanOutput(line)
					line = line.replace("\n","")
					ChannelLines.append(line)
					continue
				if len(ChannelLines) > len(UtilizationLines):
					line = CleanOutput(line)
					line = line.replace("\n","")
					UtilizationLines.append(line)
					continue
				if len(UtilizationLines) > len(NoiseLines):
					line = CleanOutput(line)
					line = line.replace("\n","")
					NoiseLines.append(line)
					continue
			Counter = 0
			while Counter < len(NoiseLines):
				TimeStamp = TimeStampLines[Counter]
				LogMessage = InterfaceLines[Counter]+ChannelLines[Counter]+UtilizationLines[Counter]+NoiseLines[Counter]
				cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
				Counter += 1
		case "check_snmpv3_status.log":
			TimeStamp_LogMessage(LogByLine,conn,cursor,Filename)
		case "clienttrack.log":
			Bracket_TimeStamp_LogMessage(LogByLine,conn,cursor,Filename)
		case "collect_log_manager.log":
			counter = 0
			Lines = len(LogByLine)
			while counter < Lines:
				line = LogByLine[counter]
				#debug prints
				#print(len(line))
				#print(Filename)
				#print(line)
				#skip empty lines
				if len(line) < 2:
					continue
				#Remove null characters
				line = line.replace('\0',"")
				parts = line.split(": ")
				TimeStamp = parts[0]
				TimeStamp = TimeStamp.replace("[","")
				TimeStamp = TimeStamp.replace("]","")
				LogMessage = parts[1]
				LogMessage = LogMessage.strip()
				if LogMessage == "ubus_proc_upload_snapshot msg={":
					PathLine = LogByLine[counter+1].strip()
					PasswordLine = LogByLine[counter+2].strip()
					UsernameLine = LogByLine[counter+3].strip()
					LogMessage = LogMessage+PathLine+PasswordLine+UsernameLine+"}"
					#single quotes break the function
					LogMessage = LogMessage.replace("'","")
					LogMessage = LogMessage.encode('utf-8')
					LogMessage = str(LogMessage)
					LogMessage = LogMessage.replace("b'","")
					LogMessage = LogMessage.replace("'","")
					cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
					counter += 5
				else:
					#single quotes break the function
					LogMessage = LogMessage.replace("'","")
					LogMessage = LogMessage.encode('utf-8')
					LogMessage = str(LogMessage)
					LogMessage = LogMessage.replace("b'","")
					LogMessage = LogMessage.replace("'","")
					cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
					counter += 1
		case "configd.log":
			counter = 0
			lines = len(LogByLine)
			while counter < lines:
				line = LogByLine[counter]
				#debug prints
				#print(len(line))
				#print(Filename)
				#print(line)
				#skip empty lines
				if len(line) < 2:
					continue
				#Remove null characters
				line = line.replace('\0',"")
				#Remove (epoch)
				###Regex does not work
				#line = line.replace('\(.*\)', "")
				###Fix this
				line = line.replace("  ", " ")
				parts = line.split(" ")
				TimeStamp = line[0:19]
				AppID = parts[2]
				AppID = AppID.replace("[","")
				AppID = AppID.replace("]","")
				LogPartsCounter = 4
				partsSize = len(parts)
				LogMessage = ""
				while LogPartsCounter < partsSize:
					LogMessage += parts[LogPartsCounter]+" "
					LogPartsCounter += 1
				LogMessage = LogMessage.strip()
				if LogMessage == "The modified config is:" or LogMessage == "call_userconfig_reload with message:":
					LogMessage += LogByLine[counter+1].strip()
					counter += 2
					LogMessage = LogMessage.replace("'","")
					LogMessage = LogMessage.encode('utf-8')
					LogMessage = str(LogMessage)
					LogMessage = LogMessage.replace("b'","")
					LogMessage = LogMessage.replace("'","")
					cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, AppID, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+AppID+"','"+LogMessage+"')")
				else:
					#single quotes break the function
					LogMessage = LogMessage.replace("'","")
					LogMessage = LogMessage.encode('utf-8')
					LogMessage = str(LogMessage)
					LogMessage = LogMessage.replace("b'","")
					LogMessage = LogMessage.replace("'","")
					cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, AppID, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+AppID+"','"+LogMessage+"')")
					counter += 1
		case "core-mon-app-restore-syslog.txt":
			for line in LogByLine:
				#skip empty lines
				fiiiiiix
				if len(line) < 2:
					continue
				line = line.replace('\0',"")
				line = line.strip()
				parts = line.split(" ")
				TimeStamp = parts[0]+" "+parts[1]
				AppID = parts[2]
				SubApp = parts[3]
				Priority = parts[4]
				SwitchName = parts[5]+" "+parts[6]
				LogPartsCounter = 8
				partsSize = len(parts)
				LogMessage = ""
				while LogPartsCounter < partsSize:
					LogMessage += parts[LogPartsCounter]+" "
					LogPartsCounter += 1
				LogMessage = LogMessage.strip()
				#single quotes break the function
				LogMessage = LogMessage.replace("'","")
				LogMessage = LogMessage.encode('utf-8')
				LogMessage = str(LogMessage)
				LogMessage = LogMessage.replace("b'","")
				LogMessage = LogMessage.replace("'","")
				cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, AppID, SubApp, Priority, SwitchName, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+AppID+"','"+SubApp+"','"+Priority+"','"+SwitchName+"','"+LogMessage+"')")
		case _:
			print(Filename+" does not match any of the parsers currently written")

def Bracket_TimeStamp_LogMessage(LogByLine,conn,cursor,Filename):
	TSCount = TSImportedNumber
	for line in LogByLine:
		#debug prints
		#print(len(line))
		#print(Filename)
		#print(line)
		#skip empty lines
		if len(line) < 2:
			continue
		#Remove null characters
		line = line.replace('\0',"")
		parts = line.split(": ")
		TimeStamp = parts[0]
		TimeStamp = TimeStamp.replace("[","")
		TimeStamp = TimeStamp.replace("]","")
		LogMessage = parts[1]
		LogMessage = LogMessage.strip()
		#single quotes break the function
		LogMessage = LogMessage.replace("'","")
		LogMessage = LogMessage.encode('utf-8')
		LogMessage = str(LogMessage)
		LogMessage = LogMessage.replace("b'","")
		LogMessage = LogMessage.replace("'","")
		cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")

def Epoch_AppID(LogByLine,conn,cursor,Filename):
	TSCount = TSImportedNumber
	for line in LogByLine:
		#debug prints
		#print(len(line))
		#print(Filename)
		#print(line)
		#skip empty lines
		if len(line) < 2:
			continue
		#Remove null characters
		line = line.replace('\0',"")
		#Remove (epoch)
		###Regex does not work
		#line = line.replace('\(.*\)', "")
		###Fix this
		line = line.replace("  ", " ")
		parts = line.split(" ")
		TimeStamp = line[0:19]
		AppID = parts[2]
		AppID = AppID.replace("[","")
		AppID = AppID.replace("]","")
		LogPartsCounter = 4
		partsSize = len(parts)
		LogMessage = ""
		while LogPartsCounter < partsSize:
			LogMessage += parts[LogPartsCounter]+" "
			LogPartsCounter += 1
		LogMessage = LogMessage.strip()
		#single quotes break the function
		LogMessage = LogMessage.replace("'","")
		LogMessage = LogMessage.encode('utf-8')
		LogMessage = str(LogMessage)
		LogMessage = LogMessage.replace("b'","")
		LogMessage = LogMessage.replace("'","")
		cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, AppID, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+AppID+"','"+LogMessage+"')")

def TimeStamp_LogMessage(LogByLine,conn,cursor,Filename):
	TSCount = TSImportedNumber
	for line in LogByLine:
		Parts = line.split(" - ")
		TimeStamp = Parts[0]
		LogMessage = Parts[1]
		#Remove null characters
		LogMessage = LogMessage.replace('\0',"")
		TimeStamp = TimeStamp.replace('\0',"")
		cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")


def TimeStamp_LogMessage_Split(LogByLine,conn,cursor,Filename):
	TSCount = TSImportedNumber
	TimeStampLines = []
	LogMessageLines = []
	LineCount = len(LogByLine)
	Counter = 0
	while Counter < LineCount:
		#For even Counter, or Odd Lines
		if Counter % 2 == 0:
			TimeStampLines.append(LogByLine[Counter])
		else:
			LogMessageLines.append(LogByLine[Counter])
		Counter += 1
	LogCount = len(LogMessageLines)
	Counter = 0
	while Counter < LogCount:
		TimeStampRaw = TimeStampLines[Counter]
		LogMessage = LogMessageLines[Counter]
		parts = TimeStampRaw.split(" ")
		Year = parts[4]
		Month = parts[1]
		match Month:
			case "Jan":
				Month = "01"
			case "Feb":
				Month = "02"
			case "Mar":
				Month = "03"
			case "Apr":
				Month = "04"	
			case "May":
				Month = "05"
			case "Jun":
				Month = "06"
			case "Jul":
				Month = "07"
			case "Aug":
				Month = "08"
			case "Sep":
				Month = "09"
			case "Oct":
				Month = "10"
			case "Nov":
				Month = "11"
			case "Dec":
				Month = "12"
		Date = parts[2]
		if len(Date) == 1:
			Date = "0"+str(Date)
		Time = parts[3]
		Timestamp = str(Year)+"-"+Month+"-"+str(Date)+" "+str(Time)
		#Remove null characters
		LogMessage = LogMessage.replace('\0',"")
		Timestamp = TimeStamp.replace('\0',"")
		cursor.execute("insert into Logs (TSCount, TimeStamp, Filename, LogMessage) values ('"+str(TSCount)+"','"+TimeStamp+"','"+Filename+"','"+LogMessage+"')")
		Counter += 1



def CleanOutput(string):
#Remove unneeded characters
	string = string.replace("[", "")
	string = string.replace("]", "")
	string = string.replace(",", "")
	string = string.replace("(", "")
	string = string.replace(")", "")
	string = string.replace("'", "")
	return string


def get_filepath():
	global dir_list
	dir_list = os.listdir()
	files = []
	techSupports = []
	techSupportTimes = []
	for item in dir_list:
		if fnmatch.fnmatch(item, "*tech_support_complete*"):
			files.append(item)
			techSupports.append(item)
			filetime = os.path.getmtime(item)
			print(item)
			print(filetime)
			#Convert from epoch to datetime
			techSupportTimes.append(datetime.datetime.fromtimestamp(filetime))
	files.sort(key=os.path.getmtime,reverse=True)
	#Display options
	match len(techSupports):
		case 0:
			print("There are no files or directories containing 'tech_support_complete' in this directory")
			quit()
		case 1:
			print("There is 1 tech support file in this directory. Opening "+str(techSupports[0]))
			selectedTS = techSupports[0]
		case _:
			validSelection = False
			while validSelection == False:
				print("There are "+str(len(techSupports))+" tech support files or directories:")
				counter = 0
				for listing in techSupports:
					print("["+str(counter+1)+"] "+str(techSupports[counter])+" - "+str(techSupportTimes[counter]))
					counter +=1
				print("[0] Exit program")
				selection = input("Which would you like to use?")
				if not selection.isdigit():
					print("Invalid Selection, please enter a number")
					continue
				if selection == "0":
					quit()
				if int(selection) <= len(techSupports) and int(selection) > 0:
					selectedTS = techSupports[int(selection)-1]
					#print(selectedTS)
					validSelection = True
				else:
					print("Invalid Selection")
	#Extract TS to dir if necessary
	TSDirName = ""
	if not os.path.isdir(selectedTS):
		TSDirName = str(selectedTS.replace(".tar",""))
		try:
			os.mkdir('./'+TSDirName)
			print("Made directory at "+str('./'+TSDirName))
		except FileExistsError:
			print("Dir already exists at "+str('./'+TSDirName))
		#extract first TS
		with tarfile.open(selectedTS, "r") as tar:
			for member in tar.getmembers():
				if member.isdir():
					os.mkdir(TSDirName+"/"+member.name)
			tar.extractall('./'+TSDirName)
	filepath = selectedTS
	print(filepath)
	return filepath

def process_logs(conn,cursor,chassis_selection):
	if (chassis_selection == "1" or chassis_selection == "all") and SwlogDir1 != "":
		for file in os.listdir(SwlogDir1):
				if ('swlog_chassis1' or 'swlog_localConsole') in file:
					SwlogFiles1.append(file)
	if (chassis_selection == "2" or chassis_selection == "all") and SwlogDir2 != "":
		for file in os.listdir(SwlogDir2):
				if ('swlog_chassis2' or 'swlog_localConsole') in file:
					SwlogFiles2.append(file)
	if (chassis_selection == "3" or chassis_selection == "all") and SwlogDir3 != "":
		for file in os.listdir(SwlogDir3):
				if ('swlog_chassis3' or 'swlog_localConsole') in file:
					SwlogFiles3.append(file)
	if (chassis_selection == "4" or chassis_selection == "all") and SwlogDir4 != "":
		for file in os.listdir(SwlogDir4):
				if ('swlog_chassis4' or 'swlog_localConsole') in file:
					SwlogFiles4.append(file)
	if (chassis_selection == "5" or chassis_selection == "all") and SwlogDir5 != "":
		for file in os.listdir(SwlogDir5):
				if ('swlog_chassis5' or 'swlog_localConsole') in file:
					SwlogFiles5.append(file)
	if (chassis_selection == "6" or chassis_selection == "all") and SwlogDir6 != "":
		for file in os.listdir(SwlogDir6):
				if ('swlog_chassis6' or 'swlog_localConsole') in file:
					SwlogFiles6.append(file)
	if (chassis_selection == "7" or chassis_selection == "all") and SwlogDir7 != "":
		for file in os.listdir(SwlogDir7):
				if ('swlog_chassis7' or 'swlog_localConsole') in file:
					SwlogFiles7.append(file)
	if (chassis_selection == "8" or chassis_selection == "all") and SwlogDir8 != "":
		for file in os.listdir(SwlogDir8):
				if ('swlog_chassis8' or 'swlog_localConsole') in file:
					SwlogFiles8.append(file)
	LogByLine = []
	if SwlogFiles1 != []:
		for logfile in SwlogFiles1:
			with open(str(SwlogDir1)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 1"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)
	if SwlogFiles2 != []:
		for logfile in SwlogFiles2:
			with open(str(SwlogDir2)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 2"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)
	if SwlogFiles3 != []:
		for logfile in SwlogFiles3:
			with open(str(SwlogDir3)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 3"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)
	if SwlogFiles4 != []:
		for logfile in SwlogFiles4:
			with open(str(SwlogDir4)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 4"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)
	if SwlogFiles5 != []:
		for logfile in SwlogFiles5:
			with open(str(SwlogDir5)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 5"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)
	if SwlogFiles6 != []:
		for logfile in SwlogFiles6:
			with open(str(SwlogDir6)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 6"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)
	if SwlogFiles7 != []:
		for logfile in SwlogFiles7:
			with open(str(SwlogDir7)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 7"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)
	if SwlogFiles8 != []:
		for logfile in SwlogFiles8:
			with open(str(SwlogDir8)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
				LogByLine = file.readlines()
			Filename = str(logfile)
			ChassisID = "Chassis 8"
			ReadandParse(LogByLine,conn,cursor,Filename,ChassisID)

def ReadandParse(LogByLine,conn,cursor,Filename,ChassisID):
	for line in LogByLine:
		TSCount = TSImportedNumber
		#debug prints
		#print(len(line))
		#print(Filename)
		#print(line)
		#skip empty lines
		if len(line) < 2:
			continue
		#Remove null characters
		line = line.replace('\0',"")
		#8.10.R03 removed the year in console logs. This hardcodes 2025 if we do not have a year
		if line[0].isdigit() == False:
			line = "2025 "+line
		line = line.replace("  ", " ")
		parts = line.split(" ")
		partsSize = len(parts)
		#Put all log fragments in LogMessage
		if partsSize < 6:
			line = line.replace("2025 ","")
			cursor.execute("insert into Logs (TSCount, ChassisID, Filename, LogMessage) values ('"+str(TSCount)+"','"+ChassisID+"','"+Filename+"','"+line+"')")
			continue
		#Format Timestamp as ISO8601 strings ("YYYY-MM-DD HH:MM:SS.SSS")
		Year = parts[0]
		Month = parts[1]
		match Month:
			case "Jan":
				Month = "01"
			case "Feb":
				Month = "02"
			case "Mar":
				Month = "03"
			case "Apr":
				Month = "04"	
			case "May":
				Month = "05"
			case "Jun":
				Month = "06"
			case "Jul":
				Month = "07"
			case "Aug":
				Month = "08"
			case "Sep":
				Month = "09"
			case "Oct":
				Month = "10"
			case "Nov":
				Month = "11"
			case "Dec":
				Month = "12"
		Date = parts[2]
		if len(Date) == 1:
			Date = "0"+str(Date)
		Time = parts[3]
		Timestamp = str(Year)+"-"+Month+"-"+str(Date)+" "+str(Time)
		SwitchName = parts[4]
		Source = parts[5]
		#print(Filename)
		#print(line)
		#parser for different sources
		match Source:
			case "swlogd":
				if partsSize > 6:
					Appid = parts[6]
					if Appid == "^^" or Appid == "Task":
						LogMessage = ""
						LogPartsCounter = 6
						while LogPartsCounter < partsSize:
							LogMessage += parts[LogPartsCounter]+" "
							LogPartsCounter += 1
						LogMessage = LogMessage.strip()
						#single quotes break the function
						LogMessage = LogMessage.replace("'","")
						LogMessage = LogMessage.encode('utf-8')
						LogMessage = str(LogMessage)
						LogMessage = LogMessage.replace("b'","")
						LogMessage = LogMessage.replace("'","")
						cursor.execute("insert into Logs (TSCount,Timestamp,SwitchName,Source,LogMessage,Filename,ChassisID) values ('"+str(TSCount)+"','"+Timestamp+"','"+SwitchName+"','"+Source+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")
						continue
				if partsSize > 7:
					#Several Subapps contain a space. This section fixes it.
					if parts[7] == "Power":
						parts[7] = "Power Mgr"
						parts.pop(8)
						partsSize -= 1
					if parts[7] == "CS":
						parts[7] = "CS Main"
						parts.pop(8)
						partsSize -= 1
					if parts[7] == "fan":
						print(line)
						print(parts)
						parts[7] = "fan & temp Mgr"
						parts.pop(8)
						parts.pop(8)
						parts.pop(8)
						partsSize -= 3
						print(parts)
					if parts[7] == "SharedMem":
						parts[7] = "SharedMem Sync"
						parts.pop(8)
						partsSize -= 1
					#svcCmm mGR has an additional space. This section removes it.
					if parts[7] == "mGR" and parts[6] == "svcCmm":
						parts.pop(8)
						partsSize -= 1
					Subapp = parts[7]
				if partsSize > 8:
					Priority = parts[8]
					LogMessage = ""
				if partsSize > 9:
					LogPartsCounter = 9
					while LogPartsCounter < partsSize:
						LogMessage += parts[LogPartsCounter]+" "
						LogPartsCounter += 1
					LogMessage = LogMessage.strip()
					#single quotes break the function
					LogMessage = LogMessage.replace("'","")
					LogMessage = LogMessage.encode('utf-8')
					LogMessage = str(LogMessage)
					LogMessage = LogMessage.replace("b'","")
					LogMessage = LogMessage.replace("'","")
				cursor.execute("insert into Logs (TSCount,Timestamp,SwitchName,Source,Appid,Subapp,Priority,LogMessage,Filename,ChassisID) values ('"+str(TSCount)+"','"+Timestamp+"','"+SwitchName+"','"+Source+"','"+Appid+"','"+Subapp+"','"+Priority+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")
			case _:
				Model = parts[6]
				if Model == "ConsLog":
					LogMessage = ""
					LogPartsCounter = 7
					while LogPartsCounter < partsSize:
						LogMessage += parts[LogPartsCounter]+" "
						LogPartsCounter += 1
					LogMessage = LogMessage.strip()
					#single quotes break the function
					LogMessage = LogMessage.replace("'","")
					LogMessage = LogMessage.encode('utf-8')
					LogMessage = str(LogMessage)
					LogMessage = LogMessage.replace("b'","")
					LogMessage = LogMessage.replace("'","")
					cursor.execute("insert into Logs (TSCount,Timestamp,SwitchName,Source,Model,LogMessage,Filename,ChassisID) values ('"+str(TSCount)+"','"+Timestamp+"','"+SwitchName+"','"+Source+"','"+Model+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")
				else:
					LogMessage = ""
					LogPartsCounter = 5
					while LogPartsCounter < partsSize:
						LogMessage += parts[LogPartsCounter]+" "
						LogPartsCounter += 1
					LogMessage = LogMessage.strip()
					#single quotes break the function
					LogMessage = LogMessage.replace("'","")
					LogMessage = LogMessage.encode('utf-8')
					LogMessage = str(LogMessage)
					LogMessage = LogMessage.replace("b'","")
					LogMessage = LogMessage.replace("'","")
					#print(Filename)
					cursor.execute("insert into Logs (TSCount,Timestamp,SwitchName,Source,LogMessage,Filename,ChassisID) values ('"+str(TSCount)+"','"+Timestamp+"','"+SwitchName+"','"+Source+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")

def load_logs1(conn,cursor,dirpath,chassis_selection):
	global SwlogDir1,SwlogDir1B,SwlogDir2,SwlogDir2B,SwlogDir3,SwlogDir4,SwlogDir5,SwlogDir6,SwlogDir7,SwlogDir8
	#Enumerate mnt to check for logs
	hasChassis = []
	if os.path.isdir("./"+dirpath+"/mnt"):
		mntchassis = []
		for item in os.listdir("./"+dirpath+"/mnt"):
			mntchassis.append(item)
		#print (mntchassis)
		if "chassis1_CMMA" in mntchassis and "1" not in hasChassis:
			#print("Chassis 1 in mnt")
			hasChassis.append("1")
			SwlogDir1 = "./"+dirpath+"/mnt/chassis1_CMMA/flash"
		if "chassis1_CMMB" in mntchassis and "1" not in hasChassis:
			#print("Chassis 1B in mnt")
			hasChassis.append("1B")
			SwlogDir1B = "./"+dirpath+"/mnt/chassis1_CMMB/flash"
		if "chassis2_CMMA" in mntchassis and "2" not in hasChassis:
			#print("Chassis 2 in mnt")
			hasChassis.append("2")
			SwlogDir2 = "./"+dirpath+"/mnt/chassis2_CMMA/flash"
		if "chassis2_CMMB" in mntchassis and "2" not in hasChassis:
			#print("Chassis 2B in mnt")
			hasChassis.append("2B")
			SwlogDir2B = "./"+dirpath+"/mnt/chassis2_CMMB/flash"
		if "chassis3_CMMA" in mntchassis and "3" not in hasChassis:
			#print("Chassis 3 in mnt")
			hasChassis.append("3")
			SwlogDir3 = "./"+dirpath+"/mnt/chassis3_CMMA/flash"
		if "chassis4_CMMA" in mntchassis and "4" not in hasChassis:
			#print("Chassis 4 in mnt")
			hasChassis.append("4")
			SwlogDir4 = "./"+dirpath+"/mnt/chassis4_CMMA/flash"
		if "chassis5_CMMA" in mntchassis and "5" not in hasChassis:
			#print("Chassis 5 in mnt")
			hasChassis.append("5")
			SwlogDir5 = "./"+dirpath+"/mnt/chassis5_CMMA/flash"
		if "chassis6_CMMA" in mntchassis and "6" not in hasChassis:
			#print("Chassis 6 in mnt")
			hasChassis.append("6")
			SwlogDir6 = "./"+dirpath+"/mnt/chassis6_CMMA/flash"
		if "chassis7_CMMA" in mntchassis and "7" not in hasChassis:
			#print("Chassis 7 in mnt")
			hasChassis.append("7")
			SwlogDir7 = "./"+dirpath+"/mnt/chassis7_CMMA/flash"
		if "chassis8_CMMA" in mntchassis and "8" not in hasChassis:
			#print("Chassis 8 in mnt")
			hasChassis.append("8")
			SwlogDir8 = "./"+dirpath+"/mnt/chassis8_CMMA/flash"
	#print(hasChassis)
	#Check and extract second TS in Flash
	ts2dir = "./"+dirpath+"/flash"
	logdir = ""
	hasdir = False
	for item in os.listdir(ts2dir):
		if os.path.isdir(item):
			logdir = os.path.dirname(str(ts2dir)+"/"+item)
			hasdir = True
	if hasdir == False:
	#	extract_tar_files(str("./"+TSDirName))
		logdir = os.path.dirname(str(ts2dir)+"/flash/flash")
	FolderChassis = []
	for file in os.listdir(logdir):
		#print(file)
		if fnmatch.fnmatch(file, "*chassis1*") and "1" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("1")
		if fnmatch.fnmatch(file, "*chassis2*") and "2" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("2")
		if fnmatch.fnmatch(file, "*chassis3*") and "3" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("3")
		if fnmatch.fnmatch(file, "*chassis4*") and "4" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("4")
		if fnmatch.fnmatch(file, "*chassis5*") and "5" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("5")
		if fnmatch.fnmatch(file, "*chassis6*") and "6" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("6")
		if fnmatch.fnmatch(file, "*chassis7*") and "7" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("7")
		if fnmatch.fnmatch(file, "*chassis8*") and "8" not in FolderChassis:
			#print("Downloading "+file)
			FolderChassis.append("8")
	#print("FolderChassis is "+str(FolderChassis))
	if len(FolderChassis) > 1:
		TimestampCheck = {}
		for chassis in FolderChassis:
			TimestampCheck[os.path.getmtime(logdir+"/swlog_chassis"+chassis)] = chassis
		#print(TimestampCheck)
		SortedTimestamps = dict(sorted(TimestampCheck.items(),reverse=True))
		#print(SortedTimestamps)
		MostRecent = next(iter(SortedTimestamps.values()))
		hasChassis.append(MostRecent)
		#print("MostRecent is "+str(MostRecent))
		match MostRecent:
			case "1":
				SwlogDir1 = logdir
				#print("SwlogDir1 is "+str(SwlogDir1))
			case "2":
				SwlogDir2 = logdir
			case "3":
				SwlogDir3 = logdir
			case "4":
				SwlogDir4 = logdir
			case "5":
				SwlogDir5 = logdir
			case "6":
				SwlogDir6 = logdir
			case "7":
				SwlogDir7 = logdir
			case "8":
				SwlogDir8 = logdir
	else:
		hasChassis.append(FolderChassis[0])
		match FolderChassis[0]:
			case "1":
				SwlogDir1 = logdir
				#print("SwlogDir1 is "+str(SwlogDir1))
			case "2":
				SwlogDir2 = logdir
			case "3":
				SwlogDir3 = logdir
			case "4":
				SwlogDir4 = logdir
			case "5":
				SwlogDir5 = logdir
			case "6":
				SwlogDir6 = logdir
			case "7":
				SwlogDir7 = logdir
			case "8":
				SwlogDir8 = logdir
	print("This switch has logs for chassis: "+str(sorted(hasChassis,key=str.lower)))
	print(chassis_selection)
	if chassis_selection == "all":
		print("Grabbing logs for all chassis")
	if chassis_selection in hasChassis:
		print("Grabbing logs for Chassis "+str(chassis_selection))
	if chassis_selection in hasChassis and chassis_selection != "all":
		print("Invalid selection. The validation options are: "+str(sorted(hasChassis,key=str.lower))+" or 'all' and the AI provided "+chassis_selection)
		exit()
	#FirstLoad
	try:
		cursor.execute("create table Logs(id integer primary key autoincrement, TSCount Text, ChassisID Text, Filename Text, Timestamp Text, SwitchName Text, Source Text, Model Text, AppID Text, Subapp Text, Priority text, LogMessage text)")
	except:
		pass
	process_logs(conn,cursor,chassis_selection)
	cursor.execute("select count(*) from Logs")
	count = CleanOutput(str(cursor.fetchall()))
	cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
	NewestLog = CleanOutput(str(cursor.fetchall()))
	TimeDesync = False
	cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
	OldestLog = CleanOutput(str(cursor.fetchall()))
	if ("1970" or "1969") in OldestLog:
		TimeDesync = True
		cursor.execute("select Timestamp from Logs where Timestamp > '%2010%'  order by Timestamp limit 1")
		OldestLog = CleanOutput(str(cursor.fetchall()))
	print("There are "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
	return OldestLog,NewestLog

def load_logs2(conn,cursor,chassis_selection):
	ArchiveLogByLine = []	   
	gzipcount = 0
	if (chassis_selection == "1" or chassis_selection == "all") and SwlogDir1 != "":
		for file in reversed(os.listdir(SwlogDir1+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir1+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						Filename = str(file)
						#print("STARTING NEW FILE: "+Filename)
						ArchiveLogByLine = log.readlines()
						ChassisID = "Chassis 1"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if (chassis_selection == "2" or chassis_selection == "all") and SwlogDir2 != "":
			for file in reversed(os.listdir(SwlogDir2+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir2+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						ArchiveLogByLine = log.readlines()
						Filename = str(file)
						ChassisID = "Chassis 2"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if (chassis_selection == "3" or chassis_selection == "all") and SwlogDir3 != "":
			for file in reversed(os.listdir(SwlogDir3+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir3+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						ArchiveLogByLine = log.readlines()
						Filename = str(file)
						ChassisID = "Chassis 3"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if (chassis_selection == "4" or chassis_selection == "all") and SwlogDir4 != "":
			for file in reversed(os.listdir(SwlogDir4+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir4+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						ArchiveLogByLine = log.readlines()
						Filename = str(file)
						ChassisID = "Chassis 4"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if (chassis_selection == "5" or chassis_selection == "all") and SwlogDir5 != "":
			for file in reversed(os.listdir(SwlogDir5+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir5+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						ArchiveLogByLine = log.readlines()
						Filename = str(file)
						ChassisID = "Chassis 5"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if (chassis_selection == "6" or chassis_selection == "all") and SwlogDir6 != "":
			for file in reversed(os.listdir(SwlogDir6+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir6+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						ArchiveLogByLine = log.readlines()
						Filename = str(file)
						ChassisID = "Chassis 6"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if (chassis_selection == "7" or chassis_selection == "all") and SwlogDir7 != "":
			for file in reversed(os.listdir(SwlogDir7+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir7+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						ArchiveLogByLine = log.readlines()
						Filename = str(file)
						ChassisID = "Chassis 7"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if (chassis_selection == "8" or chassis_selection == "all") and SwlogDir8 != "":
			for file in reversed(os.listdir(SwlogDir8+"/swlog_archive")):
				 #print(file)
				#swlog.time errors out, so we skip it
				if fnmatch.fnmatch(file, "swlog.time"):
					continue
				if fnmatch.fnmatch(file, "*.gz"):
					gzipcount += 1
					with gzip.open(SwlogDir8+"/swlog_archive/"+file, "rt",errors='ignore') as log:
						#print(log)
						ArchiveLogByLine = log.readlines()
						Filename = str(file)
						ChassisID = "Chassis 8"
						ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
	if gzipcount == 0:
		print("There are no log files in the swlog_archive")
	cursor.execute("select count(*) from Logs")
	count = CleanOutput(str(cursor.fetchall()))
	cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
	NewestLog = CleanOutput(str(cursor.fetchall()))
	TimeDesync = False
	cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
	OldestLog = CleanOutput(str(cursor.fetchall()))
	if ("1970" or "1969") in OldestLog:
		TimeDesync = True
		cursor.execute("select Timestamp from Logs where Timestamp > '%2010%'  order by Timestamp limit 1")
		OldestLog = CleanOutput(str(cursor.fetchall()))
	print("There are "+count+" logs ranging from "+OldestLog+" to "+NewestLog)

def analysis_menu(conn,cursor):
	cursor.execute("select count(*) from Logs")
	count = CleanOutput(str(cursor.fetchall()))
	cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
	NewestLog = CleanOutput(str(cursor.fetchall()))
	TimeDesync = False
	cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
	OldestLog = CleanOutput(str(cursor.fetchall()))
	if ("1970" or "1969") in OldestLog:
		TimeDesync = True
		cursor.execute("select Timestamp from Logs where Timestamp > '%2010%'  order by Timestamp limit 1")
		OldestLog = CleanOutput(str(cursor.fetchall()))
	validSelection = False
	while validSelection == False:
		print("")
		print("There are "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
		if TimeDesync == True:
			print("There is a time desync present in the logs where the timestamp is much older than expected. Use 'Look for problems' and 'Locate time desyncs' to determine where")
		print("[1] - Export to xlsx - Limit 1,000,000 rows")
		print("[2] - Search for log messages by keyword")
		print("[3] - Filter by time - WIP")
		print("[4] - Add logs from another Switch")
		print("[5] - Look for problems - WIP")
		print("[6] - Find most common logs")
		print("[7] - Direct Query")
		print("[8] - Change switch name for saved logfiles - Currently: "+PrefSwitchName)
		print("[9] - Remove unneeded logs")
		print("[AI] - Return the result for AI analysis")
		print("[0] - Exit")
		selection = input("What would you like to do with the logs?  ")
		match selection:
			case "1":
				if PrefSwitchName != "None":
					OutputFileName = PrefSwitchName+"-SwlogsParsed-Unfiltered-tsbuddy.xlsx"
				else:
					OutputFileName = "SwlogsParsed-Unfiltered-tsbuddy.xlsx"
				if TSImportedNumber > 1:
					query = "SELECT TSCount,ChassisID, Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs order by Timestamp,Filename limit 1048576"
				else:
					query = "SELECT ChassisID, Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs order by Timestamp,Filename limit 1048576"
				ExportXLSX(conn,cursor,query,OutputFileName)
			case "2":
				SearchKeyword(conn,cursor)
			case "3":
				SearchTime(conn,cursor,NewestLog,OldestLog)
			case "4":
				validSelection = True
				ImportAnother(conn,cursor)
				break
			case "5":
				LogAnalysis(conn,cursor)
			case "6":
				CommonLog(conn,cursor)
			case "7":
				DirectQuery(conn,cursor)
			case "8":
				ChangeSwitchName()
			case "9":
				RemoveLogs(conn,cursor)
			case "0":
				validSelection = True
				break
			case _:
				print("Invalid Selection")

def DirectQuery(conn,cursor):
	print("The table is named Logs")
	print("Columns: id, TSCount, ChassisID, Filename, Timestamp, SwitchName, Source, Model, AppID, Subapp, Priority, LogMessage")
	print("Example: (select * from Logs where LogMessage like '%auth%' group by LogMessage order by Timestamp,Filename desc limit 5)")
	#New line
	print("")
	query = input("Enter the SQL query. Do not include a ; at the end. Enter nothing to exit. Query: ")
	print(query)
	try:
		if query == "":
			return
		cursor.execute(query)
		Output = cursor.fetchall()
		ValidSelection = False
		while ValidSelection == False:
			print("The output is "+str(len(Output))+" lines.")
			print("[1] - Export to XLSX - Limit 1,000,000 Rows")
			print("[2] - Display in console")
			print("[3] - Run another query")
			print("[0] - Go back")
			selection = input("What would you like to do?  ")
			match selection:
				case "1":
					if len(Output) > 1000000:
						print("The result is too long to export. Please refine your search and try again")
						continue
					if PrefSwitchName != "None":
						OutputFileName = PrefSwitchName+"-SwlogsParsed-CustomQuery-tsbuddy.xlsx"
					else:
						OutputFileName = "SwlogsParsed-CustomQuery-tsbuddy.xlsx"
					ExportXLSX(conn,cursor,query,OutputFileName)
				case "2":
					for line in Output:
						print(CleanOutput(str(line)))
				case "3":
					ValidSelection = True
					DirectQuery(conn,cursor)
					return
				case "0":
					ValidSelection = True
					return
				case _:
					print("Invalid Selection")
	except:
		print("Unable to run "+query+", please check your syntax and try again")
		#New line
		print("")
		DirectQuery(conn,cursor)
	else:
		return

def RemoveLogs(conn,cursor):
	ValidSelection = False
	while ValidSelection == False:
		cursor.execute("select count(*) from Logs")
		count = CleanOutput(str(cursor.fetchall()))
		cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
		NewestLog = CleanOutput(str(cursor.fetchall()))
		cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
		OldestLog = CleanOutput(str(cursor.fetchall()))
		print("There are "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
		print("[1] - Remove unused logs")
		print("[2] - Remove logs based on a specific timeframe")
		print("[0] - Return to Main Menu")
		Selection = input("What logs would you like to remove? [0]  ") or "0"
		match Selection:
			case "1":
				if UnusedInitialized == False:
					AnalysisSelector(conn,cursor,"Unused")
				cursor.execute("select count(*) from logs where category like '%Unused%'")
				output = cursor.fetchall()
				UnusedCount = CleanOutput(str(output))
				if UnusedCount == "0":
					print("There are no Unused logs in the log database. Returning to previous menu.")
					continue
				ValidSubselection = False
				while ValidSubselection == False:
					print("There are "+UnusedCount+" logs in the Unused category")
					Subselection = input("Please confirm that you would like to remove them from the Log Database. [Yes]  ") or "Yes"
					if "yes" in Subselection or "Yes" in Subselection or "y" in Subselection or "Y"in Subselection :
						cursor.execute("delete from logs where category like '%Unused%'")
						cursor.execute("select count(*) from Logs")
						count = CleanOutput(str(cursor.fetchall()))
						cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
						NewestLog = CleanOutput(str(cursor.fetchall()))
						cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
						OldestLog = CleanOutput(str(cursor.fetchall()))
						print(UnusedCount+" logs have been removed. There are now "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
						ValidSubselection = True
						continue
					if "no" in Subselection or "No" in Subselection or "n" in Subselection or "N"in Subselection :
						print("Canceling delete request")
						ValidSubselection = True
						continue
					else:
						print("Invalid input, please answer 'Yes' or 'No'")
			case "2":
				print("")
				print("The logs contain the time range of "+OldestLog+" to "+NewestLog)
				ValidTimeSelection = False
				while ValidTimeSelection == False:
					timerequested1 = input("What is first time in your search range? Please use part of the format yyyy-mm-dd hh:mm:ss:  ")
					if timerequested1 == "":
						ValidTimeSelection == True
						return
					timerequested2 = input("What is second time in your search range? Please use part of the format yyyy-mm-dd hh:mm:ss:  ")
					if timerequested1 == timerequested2:
						print("Those are the same times, please insert two different times")
						continue
					PaddingTime = "2000-01-01 00:00:00"
					Time1Len = len(timerequested1)
					Time2Len = len(timerequested2)
					#print(timerequested1)
					#print(Time1Len)
					Time1Full = timerequested1+PaddingTime[Time1Len:19]
					#print(Time1Full)
					Time2Full = timerequested2+PaddingTime[Time2Len:19]
					format_string = "%Y-%m-%d %H:%M:%S"
					try:
						Time1 = datetime.datetime.strptime(Time1Full,format_string)
						Time2 = datetime.datetime.strptime(Time2Full,format_string)
					except:
						print("Provided times do not match the format yyyy-mm-dd hh:mm:ss")
						continue
					#print(Time1)
					#print(Time2)
					try:
						if Time1 > Time2:
							cursor.execute("Select count(*) from Logs where TimeStamp >= '"+str(Time2)+"' and TimeStamp <= '"+str(Time1)+"'")
							TimeSwap = Time1
							Time1 = Time2
							Time2 = TimeSwap
							ValidTimeSelection = True
						if Time2 > Time1:
							cursor.execute("Select count(*) from Logs where TimeStamp >= '"+str(Time1)+"' and TimeStamp <= '"+str(Time2)+"'")
							ValidTimeSelection = True
					except:
						print("Unable to run the command. Check your syntax and try again.")
				TimeCount = CleanOutput(str(cursor.fetchall()))
				ValidSubselection = False
				while ValidSubselection == False:
					print("")
					print("There are "+str(TimeCount)+" logs between "+str(Time1)+" and "+str(Time2))
					print("[1] - Remove all logs outside this timeframe")
					print("[2] - Remove all logs within this timeframe")
					print("[0] - Return to previous menu with no changes")
					Subselection = input("What would you like to do with the logs? [0]  ") or "0"
					match Subselection:
						case "1":
							cursor.execute("select count(*) from Logs where TimeStamp <= '"+str(Time1)+"'")
							OutTime1Count = CleanOutput(str(cursor.fetchall()))
							cursor.execute("select count(*) from Logs where TimeStamp >= '"+str(Time2)+"'")
							OutTime2Count = CleanOutput(str(cursor.fetchall()))
							OutTimeCount = int(OutTime1Count)+int(OutTime2Count)
							cursor.execute("delete from Logs where TimeStamp >= '"+str(Time2)+"'")
							cursor.execute("delete from Logs where TimeStamp <= '"+str(Time1)+"'")
							cursor.execute("select count(*) from Logs")
							count = CleanOutput(str(cursor.fetchall()))
							cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
							NewestLog = CleanOutput(str(cursor.fetchall()))
							cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
							OldestLog = CleanOutput(str(cursor.fetchall()))
							print(str(OutTimeCount)+" logs have been removed. There are now "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
							ValidSubselection = True
						case "2":
							cursor.execute("delete from Logs where TimeStamp >= '"+str(Time1)+"' and TimeStamp <= '"+str(Time2)+"'")
							cursor.execute("select count(*) from Logs")
							count = CleanOutput(str(cursor.fetchall()))
							cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
							NewestLog = CleanOutput(str(cursor.fetchall()))
							cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
							OldestLog = CleanOutput(str(cursor.fetchall()))
							print(TimeCount+" logs have been removed. There are now "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
							print("")
							ValidSubselection = True
						case "0":
							ValidSubselection = True
						case _:
							print("Invalid selection, please enter '1', '2', or '0'")
			case "0":
				ValidSelection = True

def CommonLog(conn,cursor):
	ValidSelection = False
	while ValidSelection == False:
		print("")
		print("[1] - All Logs")
		print("[2] - Per Chassis")
		print("[3] - For a given timerange - Not Implemented")
		print("[0] - Return to main menu")
		Selection = input("What filtering criteria do you want to use? [0]  ") or "0"
		match Selection:
			case "1":
				cursor.execute("select count(*) from Logs group by logmessage order by count(*) desc")
				output = cursor.fetchall()
				ValidSubselection = False
				while ValidSubselection == False:
					print("")
					print("There are "+str(len(output))+" unique logs.")
					print("[1] - Export to XLSX - Limit 1,000,000 rows")
					print("[2] - Display the most common logs in console")
					print("[0] - Return to previous menu")
					Subselection = input("What would you like to do with the unique logs? [0]  ") or "0"
					match Subselection:
						case "1":
							if PrefSwitchName != "None":
								OutputFileName = PrefSwitchName+"-SwlogsParsed-UniqueLogs-All-tsbuddy.xlsx"
							else:
								OutputFileName = "SwlogsParsed-UniqueLogs-All-tsbuddy.xlsx"
							query = "select count(*),logmessage from Logs group by logmessage order by count(*) desc"
							ExportXLSX(conn,cursor,query,OutputFileName)
						case "2":
							ValidCountSelection = False
							while ValidCountSelection == False:
								countselection = input("How many logs would you like to diplay in the console? There are "+str(len(output))+" total unique logs. [All]  ") or "All"
								if not int(countselection) and not "All":
									print("Invalid number. Please insert a number")
									continue
								if int(countselection) > len(output):
									print("There are few logs than you are requesting. Printing all of them")
									countselection = "All"
								if countselection == "All":
									cursor.execute("select count(*),logmessage from Logs group by logmessage order by count(*) desc")
									UniqueLogs = cursor.fetchall()
									print("")
									print("Log Count, Log Message")
									print("----------------------")
									for line in UniqueLogs:
										line = str(line)
										line = line.replace("(","")
										line = line.replace(")","")
										print(line)
									ValidCountSelection = True
								else:
									cursor.execute("select count(*),logmessage from Logs group by logmessage order by count(*) desc limit "+countselection)
									UniqueLogs = cursor.fetchall()
									print("")
									print("Log Count, Log Message")
									print("----------------------")
									for line in UniqueLogs:
										line = str(line)
										line = line.replace("(","")
										line = line.replace(")","")
										print(line)
									ValidCountSelection = True
						case "0":
							ValidSubselection = True
			case "2":
				cursor.execute("select chassisid,count(*) from Logs group by chassisid,logmessage order by count(*) desc")
				output = cursor.fetchall()
				ValidSubselection = False
				while ValidSubselection == False:
					print("")
					print("There are "+str(len(output))+" unique logs across all chassis.")
					print("[1] - Export to XLSX - Limit 1,000,000 rows")
					print("[2] - Display the most common logs in console")
					print("[0] - Return to previous menu")
					Subselection = input("What would you like to do with the unique logs? [0]  ") or "0"
					match Subselection:
						case "1":
							if PrefSwitchName != "None":
								OutputFileName = PrefSwitchName+"-SwlogsParsed-UniqueLogs-PerChassis-tsbuddy.xlsx"
							else:
								OutputFileName = "SwlogsParsed-UniqueLogs-PerChassis-tsbuddy.xlsx"
							query = "select ChassisID,count(*),logmessage from Logs group by ChassisID,logmessage order by count(*) desc"
							ExportXLSX(conn,cursor,query,OutputFileName)
						case "2":
							ValidCountSelection = False
							while ValidCountSelection == False:
								countselection = input("How many logs would you like to diplay in the console? There are "+str(len(output))+" total unique logs. [All]  ") or "All"
								if not int(countselection) and not "All":
									print("Invalid number. Please insert a number")
									continue
								#FIX, this does not work. Looking for is number
								if int(countselection) > len(output):
									print("There are few logs than you are requesting. Printing all of them")
									countselection = "All"
								if countselection == "All":
									cursor.execute("select chassisid from logs group by chassisid")
									ChassisCount = len(cursor.fetchall())
									counter = 1
									while counter <= ChassisCount:
										cursor.execute("select count(*),logmessage from Logs where chassisid = 'Chassis "+str(counter)+"'group by logmessage order by count(*) desc")
										UniqueLogs = cursor.fetchall()
										print("")
										print("Chassis "+str(counter))
										print("Log Count, Log Message")
										print("----------------------")
										for line in UniqueLogs:
											line = str(line)
											line = line.replace("(","")
											line = line.replace(")","")
											print(line)
										counter += 1
									ValidCountSelection = True
								else:
									cursor.execute("select chassisid from logs group by chassisid")
									ChassisCount = len(cursor.fetchall())
									counter = 1
									while counter <= ChassisCount:
										cursor.execute("select count(*),logmessage from Logs where chassisid = 'Chassis "+str(counter)+"'group by logmessage order by count(*) desc limit "+countselection)
										UniqueLogs = cursor.fetchall()
										print("")
										print("Chassis "+str(counter))
										print("Log Count, Log Message")
										print("----------------------")
										for line in UniqueLogs:
											line = str(line)
											line = line.replace("(","")
											line = line.replace(")","")
											print(line)
										counter += 1
									ValidCountSelection = True
						case "0":
							ValidSubselection = True
			case "3":
				pass
			case "0":
				ValidSelection = True
				return
			case _:
				print("Invalid Selection, please try again")

def TimeDesyncFinder(conn,cursor,api=False):
	cursor.execute("select id from Logs where TimeStamp < '2010'")
	Output = cursor.fetchall()
	print("There are "+str(len(Output))+" logs with desynced timestamps.")
	DesyncIDs = []
	for id in Output:
		id = CleanOutput(str(id))
		DesyncIDs.append(int(id))
	if DesyncIDs != []:
		counter = 0
		DesyncLeftEdges = []
		LastGoodTimes = []
		DesyncRightEdges = []
		FirstGoodTimes = []
		DesyncIDsSorted = sorted(DesyncIDs)
		FirstLeftEdge = DesyncIDsSorted[0]
		DesyncLeftEdges.append(FirstLeftEdge)
		while counter < len(DesyncIDsSorted)-1:
			if DesyncIDsSorted[counter+1] - DesyncIDsSorted[counter] == 1:
				counter += 1
				continue
			else:
				DesyncLeftEdges.append(DesyncIDsSorted[counter+1])
				DesyncRightEdges.append(DesyncIDsSorted[counter])
				counter += 1
		LastRightEdge = DesyncIDsSorted[-1]
		DesyncRightEdges.append(LastRightEdge)
	else:
		print("There are no desyncs in this capture, returning to menu")
		return
	#print("There are "+str(len(DesyncLeftEdges))+" continuous ranges of logs in epoch time:")
	#print(DesyncLeftEdges)
	#print(DesyncRightEdges)
	while counter < len(DesyncLeftEdges):
		#print(counter)
		print(str(DesyncLeftEdges[counter])+" through "+str(DesyncRightEdges[counter]))
		counter += 1
	for id in DesyncLeftEdges:
		LastGoodTime = id-1
		cursor.execute("select timestamp from Logs where ID = "+str(LastGoodTime))
		Output = cursor.fetchall()
		Time = CleanOutput(str(Output))
		LastGoodTimes.append(Time)
	for id in DesyncRightEdges:
		FirstGoodTime = id+1
		cursor.execute("select timestamp from Logs where ID = "+str(FirstGoodTime))
		Output = cursor.fetchall()
		Time = CleanOutput(str(Output))
		FirstGoodTimes.append(Time)
	print("There are "+str(len(LastGoodTimes))+" continuous ranges of logs in epoch time:")
	counter = 0
	while counter < len(LastGoodTimes):
		print("Last normal timestamp: "+str(FirstGoodTimes[counter])+" recovered at "+str(LastGoodTimes[counter]))
		counter += 1

def SearchKeyword(conn,cursor):
	keyword = input("Enter a keyword to search through the logs: ")
	########Add input validation
	cursor.execute("select count(*) from Logs where LogMessage like '%"+keyword+"%'")
	logcount = cursor.fetchall()
	logcount = CleanOutput(str(logcount))
	if int(logcount) > int(0):
		print("There are "+str(logcount)+" logs with that keyword.")
		if int(logcount) >= int(5):
			print("Here are the 5 most recent examples:")
			cursor.execute("select Filename,Timestamp,LogMessage from Logs where LogMessage like '%"+keyword+"%' order by Timestamp,Filename desc limit 5")
			output = cursor.fetchall()
			for line in output:
				print(CleanOutput(str(line)))
		else:
			print("Here are the logs containing '"+keyword+"':")
			cursor.execute("select Filename,Timestamp,LogMessage from Logs where LogMessage like '%"+keyword+"%' order by Timestamp,Filename desc limit 5")
			output = cursor.fetchall()
			for line in output:
				print(CleanOutput(str(line)))
		ValidSelection = False
		while ValidSelection == False:
			print("[1] Export to XLSX - Limit 1,000,000 rows")
			print("[2] Find unique logs")
			print("[3] Run another search")
			print("[0] Return to main menu")
			#####Add a "refine further"
			selection = input("What would you like to do with these logs? [1]") or "1"
			match selection:
				case "1":
					if PrefSwitchName != "None":
						OutputFileName = PrefSwitchName+"-SwlogsParsed-"+keyword+"-tsbuddy.xlsx"
					else:
						OutputFileName = "SwlogsParsed-"+keyword+"-tsbuddy.xlsx"
					query = "select Filename,Timestamp,LogMessage from Logs where LogMessage like '%"+keyword+"%' order by Timestamp,Filename desc"
					ExportXLSX(conn,cursor,query,OutputFileName)
				case "2":
					cursor.execute("select count(*) from Logs where LogMessage like '%"+keyword+"%' group by LogMessage")
					logcount = cursor.fetchall()
					logcount = len(logcount)
					print("There are "+str(logcount)+" unique log messages.")
					if int(logcount) >= int(10):
						print("Here are the 10 most common log messages:")
						cursor.execute("select LogMessage, count(*) from Logs where LogMessage like '%"+keyword+"%' group by LogMessage order by count(*) desc limit 10")
						output = cursor.fetchall()
						for line in output:
							print(CleanOutput(str(line))+" times")
					if int(logcount) < int(10):
						cursor.execute("select LogMessage, count(*) from Logs where LogMessage like '%"+keyword+"%' group by LogMessage order by count(*) desc limit 10")
						output = cursor.fetchall()
						for line in output:
							print(CleanOutput(str(line))+" times")
					ValidSubselection = False
					while ValidSubselection == False:
						print("[1] Export to XLSX - Limit 1,000,000 rows")
						print("[2] Run another search")
						print("[3] Return to main menu")
						#####Add a "refine further"
						selection = input("What would you like to do with these logs? [1]") or "1"
						match selection:
							case "1":
								ValidSubselection = True
								context = keyword+"-Unique"
								if PrefSwitchName != "None":
									OutputFileName = PrefSwitchName+"-SwlogsParsed-"+context+"-tsbuddy.xlsx"
								else:
									OutputFileName = "SwlogsParsed-"+context+"-tsbuddy.xlsx"
								if TSImportedNumber > 1:
									query = "select TSCount,ChassisID, Filename, Timestamp as FirstTimestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs where LogMessage like '%"+keyword+"%' group by LogMessage order by Timestamp,Filename limit 1048576"
								else:
									query = "select ChassisID, Filename, Timestamp as FirstTimestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs where LogMessage like '%"+keyword+"%' group by LogMessage order by Timestamp,Filename limit 1048576"
								ExportXLSX(conn,cursor,query,OutputFileName)
							case "2":
								ValidSubselection = True
								SearchKeyword(conn,cursor)
							case "3":
								ValidSubselection = True
							case _:
								print("Invalid input.")
				case "3":
					ValidSelection = True
					SearchKeyword(conn,cursor)
				case "0":
					ValidSelection = True
				case _:
					print("Invalid input.")
				
			
	else:
		print("No matching logs found.")
		ValidSelection = False
		while ValidSelection == False:
			selection = input("Would you like to try another search? [y]") or "y"
			match selection:
				case "y":
					ValidSelection = True
					SearchKeyword(conn,cursor)
				case "n":
					ValidSelection = True
				case _:
					print("Invalid input, please input 'y' or 'n'")

def ChangeSwitchName():
	EnteredName = input("What name would you like to use for these logs?  ")
	global PrefSwitchName
	PrefSwitchName = CleanOutput(EnteredName)
	print("Exported files will use the name: "+PrefSwitchName+". ie: "+PrefSwitchName+"SwlogsParsed-Unfiltered-tsbuddy.xlsx")

def AnalysisInit(conn,cursor):
	print("Initializing log analysis")
	cursor.execute("alter table Logs add LogMeaning text")
	cursor.execute("alter table Logs add Category text")
	src_dir = os.path.dirname(os.path.abspath(__file__))
	data = pd.read_csv(src_dir+"/loglist-master.csv")
	data.to_sql('Analysis', conn, index=True)
	global AnalysisInitialized
	AnalysisInitialized = True

def LogAnalysis(conn,cursor,api=False):
	ValidSelection = False
	while ValidSelection == False:
		print("")
		print("[1] - Reboots")
		print("[2] - VC Issues - Not Implemented")
		print("[3] - Interface Status")
		print("[4] - OSPF - Not Implemented")
		print("[5] - SPB - Not Implemented")
		print("[6] - Health - Not Implemented")
		print("[7] - Connectivity - Not Implemented")
		print("[8] - Locate time desyncs - WIP")
		print("[9] - Critical Logs")
		print("[10] - Unused logs")
		print("[RCA] - Provide Root Cause Analysis - WIP")
		print("[All] - Analyze all known logs - Long Operation")
		print("[0] - Return to Main Menu")
		selection = input("What would you like to look for? [0]  ") or "0"
		match selection:
			case "1":
				RebootAnalysis(conn,cursor,api)
			case "2":
				AnalysisSelector(conn,cursor,"VC",api)
			case "3":
				AnalysisSelector(conn,cursor,"Interface",api)
			case "4":
				AnalysisSelector(conn,cursor,"OSPF",api)
			case "5":
				AnalysisSelector(conn,cursor,"SPB",api)
			case "6":
				AnalysisSelector(conn,cursor,"Health",api)
			case "7":
				AnalysisSelector(conn,cursor,"Connectivity",api)
			case "8":
				TimeDesyncFinder(conn,cursor,api)
			case "9":
				AnalysisSelector(conn,cursor,"Critical",api)
			case "10":
				AnalysisSelector(conn,cursor,"Unused",api)
			case "RCA":
				RootCauseAnalysis(conn,cursor,api)
			case "All":
				AllKnownLogs(conn,cursor,api)
			case "0":
				ValidSelection = True
				return
			case _:
				print("Invalid Selection")

def AnalysisSelector(conn,cursor,request,api=False):
	print("Starting Analysis for "+request)
	match request:
		case "Reboot":
			AnalysisOutput = RebootAnalysis(conn,cursor,api)
		case "VC":
			AnalysisOutput = VCAnalysis(conn,cursor,api)
		case "Interface":
			AnalysisOutput = InterfaceAnalysis(conn,cursor,api)
		case "OSPF":
			AnalysisOutput = OSPFAnalysis(conn,cursor,api)
		case "SPB":
			AnalysisOutput = SPBAnalysis(conn,cursor,api)
		case "Health":
			AnalysisOutput = HealthAnalysis(conn,cursor,api)
		case "Connectivity":
			AnalysisOutput = ConnectivityAnalysis(conn,cursor,api)
		case "Critical":
			AnalysisOutput = CriticalAnalysis(conn,cursor,api)
		case "Hardware":
			AnalysisOutput = HardwareAnalysis(conn,cursor,api)
		case "Upgrades":
			AnalysisOutput = UpgradesAnalysis(conn,cursor,api)
		case "General":
			AnalysisOutput = GeneralAnalysis(conn,cursor,api)
		case "MACLearning":
			AnalysisOutput = MACLearningAnalysis(conn,cursor,api)
		case "Unused":
			AnalysisOutput = UnusedAnalysis(conn,cursor,api)
		case "STP":
			AnalysisOutput = STPAnalysis(conn,cursor,api)
		case "Security":
			AnalysisOutput = SecurityAnalysis(conn,cursor,api)
		case "Unclear":
			AnalysisOutput = UnclearAnalysis(conn,cursor,api)
		case "Unknown":
			AnalysisOutput = UnknownAnalysis(conn,cursor,api)
	return AnalysisOutput

def RebootAnalysis(conn,cursor,api=False):
	print("Checking the logs for reboots")
	global AnalysisInitialized
	if AnalysisInitialized == False:
		AnalysisInit(conn,cursor)
		AnalysisInitialized = True
	global RebootsInitialized
	if RebootsInitialized == False:
		RebootsInitialized = True
		cursor.execute("select LogMessage,Category,LogMeaning from Analysis where category like '%Reboot%'")
		Analysis = cursor.fetchall()
		LogDictionary = []
		LogMeaning = []
		for line in Analysis:
			Message = line[0]
			Meaning = line[2]
			Message.strip()
			Meaning.strip()
			#print(Message)
			#print(Meaning)
			LogDictionary.append(Message)
			LogMeaning.append(Meaning)
		counter = 0
		DictionaryLength = len(LogDictionary)
		while counter < DictionaryLength:
			query = "update Logs set LogMeaning = '"+LogMeaning[counter]+"', Category = 'Reboot' where LogMessage like '%"+LogDictionary[counter]+"%'"
			#print(query)
			cursor.execute(query)
			#cursor.execute("update Logs (LogMeaning, Category) values ("+LogMeaning[counter]+", "+Category[counter]+") where LogMessage like '%"+LogDictionary[counter]+"%'")
			counter += 1
	AnyReboots = False
	"""
	cursor.execute("select Logs.ID,Logs.ChassisID,Logs.Timestamp from Logs,Reboot where (((InStr([Logs].[LogMessage],[Reboot].[LogMessage]))>0)) order by Logs.ChassisID,Logs.Timestamp")
	"""
	cursor.execute("select ID,ChassisID,Timestamp from Logs where Category like '%Reboot%' order by ChassisID,Timestamp")
	Output = cursor.fetchall()
	#print(Output)
	Chassis1ListTime = []
	Chassis2ListTime = []
	Chassis3ListTime = []
	Chassis4ListTime = []
	Chassis5ListTime = []
	Chassis6ListTime = []
	Chassis7ListTime = []
	Chassis8ListTime = []
	Chassis1ListID = []
	Chassis2ListID = []
	Chassis3ListID = []
	Chassis4ListID = []
	Chassis5ListID = []
	Chassis6ListID = []
	Chassis7ListID = []
	Chassis8ListID = []
	AnalysisOutput = []
	for line in Output:
		#print(line)
		line = str(line)
		line = line.replace("[", "")
		line = line.replace("]", "")
		line = line.replace("(", "")
		line = line.replace(")", "")
		line = line.replace("' ", "")
		line = line.replace("'", "")
		parts = line.split(",")
		#print(parts)
		ID = parts[0].strip()
		ChassisID = parts[1].strip()
		Timestamp = parts [2].strip()
		#print("ID: "+ID)
		#print("ChassisID: "+ChassisID)
		#print("Timestamp: "+Timestamp)
		match ChassisID:
			case "Chassis 1":
				Chassis1ListTime.append(Timestamp)
				Chassis1ListID.append(ID)
			case "Chassis 2":
				Chassis2ListTime.append(Timestamp)
				Chassis2ListID.append(ID)
			case "Chassis 3":
				Chassis3ListTime.append(Timestamp)
				Chassis3ListID.append(ID)
			case "Chassis 4":
				Chassis4ListTime.append(Timestamp)
				Chassis4ListID.append(ID)
			case "Chassis 5":
				Chassis5ListTime.append(Timestamp)
				Chassis5ListID.append(ID)
			case "Chassis 6":
				Chassis6ListTime.append(Timestamp)
				Chassis6ListID.append(ID)
			case "Chassis 7":
				Chassis7ListTime.append(Timestamp)
				Chassis7ListID.append(ID)
			case "Chassis 8":
				Chassis8ListTime.append(Timestamp)
				Chassis8ListID.append(ID)

	#print(len(Chassis1ListTime))
	#print(len(Chassis2ListTime))
	#print(len(Chassis3ListTime))
	#print(len(Chassis4ListTime))
	#print(len(Chassis5ListTime))
	#print(len(Chassis6ListTime))
	#print(len(Chassis7ListTime))
	#print(len(Chassis8ListTime))
	Chassis1RebootEvent = []
	Chassis2RebootEvent = []
	Chassis3RebootEvent = []
	Chassis4RebootEvent = []
	Chassis5RebootEvent = []
	Chassis6RebootEvent = []
	Chassis7RebootEvent = []
	Chassis8RebootEvent = []
	format_string = "%Y-%m-%d %H:%M:%S"
	if Chassis1ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis1ListTime[0]
		Chassis1RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis1ListTime):
			#print("counter = "+str(counter))
			#print("Chassis1ListTime size: "+str(len(Chassis1ListTime)))
			Time1 = Chassis1ListTime[counter]
			Time2 = Chassis1ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis1RebootEvent.append(Time2)
			counter += 1
		if len(Chassis1RebootEvent) == 1:
			print("Chassis 1 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 1 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 1 rebooted "+str(len(Chassis1RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 1 rebooted "+str(len(Chassis1RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis1RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		#print(AnalysisOutput)
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if Chassis2ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis2ListTime[0]
		Chassis2RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis2ListTime):
			#print("counter = "+str(counter))
			#print("Chassis2ListTime size: "+str(len(Chassis2ListTime)))
			Time1 = Chassis2ListTime[counter]
			Time2 = Chassis2ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis2RebootEvent.append(Time2)
			counter += 1
		if len(Chassis2RebootEvent) == 1:
			print("Chassis 2 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 2 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 2 rebooted "+str(len(Chassis2RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 2 rebooted "+str(len(Chassis2RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis2RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if Chassis3ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis3ListTime[0]
		Chassis3RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis3ListTime):
			#print("counter = "+str(counter))
			#print("Chassis3ListTime size: "+str(len(Chassis3ListTime)))
			Time1 = Chassis3ListTime[counter]
			Time2 = Chassis3ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis3RebootEvent.append(Time2)
			counter += 1
		if len(Chassis3RebootEvent) == 1:
			print("Chassis 3 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 3 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 3 rebooted "+str(len(Chassis3RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 3 rebooted "+str(len(Chassis3RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis3RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if Chassis4ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis4ListTime[0]
		Chassis4RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis4ListTime):
			#print("counter = "+str(counter))
			#print("Chassis4ListTime size: "+str(len(Chassis4ListTime)))
			Time1 = Chassis4ListTime[counter]
			Time2 = Chassis4ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis4RebootEvent.append(Time2)
			counter += 1
		if len(Chassis4RebootEvent) == 1:
			print("Chassis 4 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 4 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 4 rebooted "+str(len(Chassis4RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 4 rebooted "+str(len(Chassis4RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis4RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if Chassis5ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis5ListTime[0]
		Chassis5RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis5ListTime):
			#print("counter = "+str(counter))
			#print("Chassis5ListTime size: "+str(len(Chassis5ListTime)))
			Time1 = Chassis5ListTime[counter]
			Time2 = Chassis5ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis5RebootEvent.append(Time2)
			counter += 1
		if len(Chassis5RebootEvent) == 1:
			print("Chassis 5 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 5 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 5 rebooted "+str(len(Chassis5RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 5 rebooted "+str(len(Chassis5RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis5RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if Chassis6ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis6ListTime[0]
		Chassis6RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis6ListTime):
			#print("counter = "+str(counter))
			#print("Chassis6ListTime size: "+str(len(Chassis6ListTime)))
			Time1 = Chassis6ListTime[counter]
			Time2 = Chassis6ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis6RebootEvent.append(Time2)
			counter += 1
		if len(Chassis6RebootEvent) == 1:
			print("Chassis 6 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 6 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 6 rebooted "+str(len(Chassis6RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 6 rebooted "+str(len(Chassis6RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis6RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if Chassis7ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis7ListTime[0]
		Chassis7RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis7ListTime):
			#print("counter = "+str(counter))
			#print("Chassis7ListTime size: "+str(len(Chassis7ListTime)))
			Time1 = Chassis7ListTime[counter]
			Time2 = Chassis7ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis7RebootEvent.append(Time2)
			counter += 1
		if len(Chassis7RebootEvent) == 1:
			print("Chassis 7 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 7 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 7 rebooted "+str(len(Chassis7RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 7 rebooted "+str(len(Chassis7RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis7RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if Chassis8ListTime != []:
		AnyReboots = True
		FirstReboot = Chassis8ListTime[0]
		Chassis8RebootEvent.append(FirstReboot)
		counter = 0
		while counter+1 < len(Chassis8ListTime):
			#print("counter = "+str(counter))
			#print("Chassis8ListTime size: "+str(len(Chassis8ListTime)))
			Time1 = Chassis8ListTime[counter]
			Time2 = Chassis8ListTime[counter+1]
			#print(Time1)
			#print(Time2)
			#remove subseconds
			parts1 = Time1.split(".")
			Time1 = parts1[0]
			parts2 = Time2.split(".")
			Time2 = parts2[0]
			Time1 = datetime.datetime.strptime(Time1,format_string)
			Time2 = datetime.datetime.strptime(Time2,format_string)
			TimeDiff = Time2-Time1
			#print(Time1)
			#print(Time2)
			#print(TimeDiff)
			#If logs are more than 5 minutes apart
			if TimeDiff >= datetime.timedelta(minutes=5):
				#print("Reboot event!")
				Chassis8RebootEvent.append(Time2)
			counter += 1
		if len(Chassis8RebootEvent) == 1:
			print("Chassis 8 rebooted 1 time. Here is when the reboot happened:")
			AnalysisOutput.append("Chassis 8 rebooted 1 time. Here is when the reboot happened:")
		else:
			print("Chassis 8 rebooted "+str(len(Chassis8RebootEvent))+" times. Here is when the reboots happened:")
			AnalysisOutput.append("Chassis 8 rebooted "+str(len(Chassis8RebootEvent))+" times. Here is when the reboots happened:")
		TimeDesync = False
		for line in Chassis8RebootEvent:
			print(line)
			AnalysisOutput.append(str(line))
			if ("1970" or "1969") in str(line):
				TimeDesync = True
		if TimeDesync == True:
			print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
	if AnyReboots == False:
		AnalysisOutput = "There are no reboots in the logs."
		return AnalysisOutput
	if api == True:
		return AnalysisOutput
	ValidSubSelection = False
	if AnyReboots == False:
		print("There are no reboots in the logs. Returning to Analysis menu.")
		ValidSubSelection = True
	while ValidSubSelection == False:
		print("[1] - Export reboot logs to xlsx - Limit 1,000,000 rows")
		print("[2] - Display reboot logs")
		print("[3] - Show logs around each reboot - Not Implemented")
		print("[4] - Look for reboot reason - Not Implemented")
		print("[0] - Go back")
		selection = input("What would you like to do? [0] ") or "0"
		match selection:
			case "1":
				if PrefSwitchName != "None":
					OutputFileName = PrefSwitchName+"-SwlogsParsed-LogAnalysis-Reboots-tsbuddy.xlsx"
				else:
					OutputFileName = "SwlogsParsed-LogAnalysis-Reboots-tsbuddy.xlsx"
				if TSImportedNumber > 1:
					query = "select TSCount,ChassisID,Filename,Timestamp,SwitchName,Source,Model,AppID,Subapp,Priority,LogMessage from Logs where category like '%Reboot%' order by Timestamp"
				else:
					query = "select ChassisID,Filename,Timestamp,SwitchName,Source,Model,AppID,Subapp,Priority,LogMessage from Logs where category like '%Reboot%' order by Timestamp"
				ExportXLSX(conn,cursor,query,OutputFileName)

			case "2":
				cursor.execute("select TSCount,ChassisID,Filename,Timestamp,SwitchName,Source,Model,AppID,Subapp,Priority,LogMessage from Logs where category like '%Reboot%' order by Timestamp")
				Output = cursor.fetchall()
				for line in Output:
					print(line)
			case "3":
				pass
			case "4":
				pass
			case "0":
				ValidSubSelection = True

def InterfaceAnalysis(conn,cursor,api=False):
	print("Checking the logs for Interface issues")
	global AnalysisInitialized
	if AnalysisInitialized == False:
		AnalysisInit(conn,cursor)
		AnalysisInitialized = True
	global InterfaceInitialized
	if InterfaceInitialized == False:
		InterfaceInitialized = True
		cursor.execute("select LogMessage,Category,LogMeaning from Analysis where category like '%Interface%'")
		Analysis = cursor.fetchall()
		LogDictionary = []
		LogMeaning = []
		for line in Analysis:
			Message = line[0]
			Meaning = line[2]
			Message.strip()
			Meaning.strip()
			#print(Message)
			#print(Meaning)
			LogDictionary.append(Message)
			LogMeaning.append(Meaning)
		counter = 0
		DictionaryLength = len(LogDictionary)
		while counter < DictionaryLength:
			query = "update Logs set LogMeaning = '"+LogMeaning[counter]+"', Category = 'Interface' where LogMessage like '%"+LogDictionary[counter]+"%'"
			#print(query)
			cursor.execute(query)
			#cursor.execute("update Logs (LogMeaning, Category) values ("+LogMeaning[counter]+", "+Category[counter]+") where LogMessage like '%"+LogDictionary[counter]+"%'")
			counter += 1
	global InterfaceRan
	if InterfaceRan == False:
		InterfaceRan = True
		cursor.execute("create table Interface(id integer primary key autoincrement, TSCount Text, ChassisID Text, Filename Text, Timestamp Text, LogMessage text, Interface text, Status text)")
		#For log "pmnHALLinkStatusCallback:208 LINKSTS 1/1/13 DOWN gport 0xc Speed 0 Duplex HALF"
		cursor.execute("select TScount,TimeStamp,ChassisID,Filename,LogMessage from Logs where category like '%Interface%' and LogMessage like '%LINKSTS %/%/%' order by ChassisID,TimeStamp")
		Output = cursor.fetchall()
		for line in Output:
			#print(line)
			TSCount = line[0]
			TimeStamp = line[1]
			ChassisID = line[2]
			Filename = line[3]
			LogMessage = line[4]
			#print(LogMessage)
			Parts = LogMessage.split(" ")
			Interface = Parts[3]
			Status = Parts[4]
			cursor.execute("insert into Interface (TSCount, TimeStamp, ChassisID, Filename, LogMessage, Interface, Status) values ('"+str(TSCount)+"','"+TimeStamp+"','"+ChassisID+"','"+Filename+"','"+LogMessage+"','"+Interface+"','"+Status+"')")
		#For log "CUSTLOG CMM Link 1/1/13 Alias r.202D_j.104A.2.1-062A operationally up""
		cursor.execute("select TScount,TimeStamp,ChassisID,Filename,LogMessage from Logs where category like '%Interface%' and LogMessage like '%LINK %/%/%' order by ChassisID,TimeStamp")
		Output = cursor.fetchall()
		for line in Output:
			#print(line)
			TSCount = line[0]
			TimeStamp = line[1]
			ChassisID = line[2]
			Filename = line[3]
			LogMessage = line[4]
			#print(LogMessage)
			Parts = LogMessage.split(" operationally ")
			Status = Parts[1]
			"""
			Parts = LogMessage.split(" ")
			Interface = Parts[3]
			if Parts[4] == "Alias":
				Status = Parts[7]
			else:
				Status = Parts[5]
			"""
			if Status == "up":
				Status = "UP"
			if Status == "down":
				Status = "DOWN"
			cursor.execute("insert into Interface (TSCount, TimeStamp, ChassisID, Filename, LogMessage, Interface, Status) values ('"+str(TSCount)+"','"+TimeStamp+"','"+ChassisID+"','"+Filename+"','"+LogMessage+"','"+Interface+"','"+Status+"')")
	#Most Flapped interfaces
	AnalysisOutput = []
	cursor.execute("select count(*),ChassisID as ReportingChassis, Interface from Interface where Status = 'DOWN' group by Interface order by count(*) desc limit 10")
	TopFlap = cursor.fetchall()
	print("")
	print(str(len(TopFlap))+" different interfaces flapped in the logs.")
	if len(TopFlap) >= 10:
		print("The 10 interfaces with the most flaps are:")
		AnalysisOutput.append("The 10 interfaces with the most flaps are:")
	print("Flap Count - ReportingChassis - Interface")
	AnalysisOutput.append(str(len(TopFlap))+" different interfaces flapped in the logs.")
	AnalysisOutput.append("Flap Count - ReportingChassis - Interface")
	ThresholdReached = False
	for line in TopFlap:
		count = line[0]
		if count > 50:
			ThresholdReached = True
		chassis = line[1]
		interface = line[2]
		print(str(count)+" - "+chassis+" - "+interface)
		AnalysisOutput.append(str(count)+" - "+chassis+" - "+interface)
	if ThresholdReached == True:
		print("")
		print("There are an abnormally high number of interface flaps. It is recommended to investigate the interfaces with the most flaps for possible link/SFP issues.")
		AnalysisOutput.append("There are an abnormally high number of interface flaps. It is recommended to investigate the interfaces with the most flaps for possible link/SFP issues.")
	if api == True:
		return AnalysisOutput
	ValidSelection = False
	while ValidSelection == False:
		print("")
		print("[1] - Export to XLSX - Limit 1,000,000 rows")
		print("[2] - Show all flap logs for a particular interface - Not Implemented")
		print("[3] - Show interface flaps for a given time period - Not Implemented")
		print("[0] - Return to Analysis Menu")
		Selection = input("What would you like to do with the Number of Flaps per Interface logs? [0]  ") or "0"
		match Selection:
			case "1":
				if PrefSwitchName != "None":
					OutputFileName = PrefSwitchName+"-SwlogsParsed-LogAnalysis-FlapsPerInterface-tsbuddy.xlsx"
				else:
					OutputFileName = "SwlogsParsed-LogAnalysis-FlapsPerInterface-tsbuddy.xlsx"
				if TSImportedNumber > 1:
					query = "select tscount,count(*),ChassisID as ReportingChassis, Interface from Interface where Status = 'DOWN' group by tscount,Interface order by count(*) desc"
				else:
					query = "select count(*),ChassisID as ReportingChassis, Interface from Interface where Status = 'DOWN' group by Interface order by count(*) desc"
				ExportXLSX(conn,cursor,query,OutputFileName)
			case "2":
				ValidInterfaceSelection = False
				while ValidInterfaceSelection == False:
					print("The 10 interfaces with the most flaps are:")
					print("Flap Count - ReportingChassis - Interface")
					for line in TopFlap:
						count = line[0]
						chassis = line[1]
						interface = line[2]
						print(str(count)+" - "+chassis+" - "+interface)
					InterfaceSelection = input("Which interface would you like to see the flaps for? Leave this blank to exit  ") or "NOTHING"
					if InterfaceSelection == "NOTHING":
						ValidInterfaceSelection = True
						continue
					else:
						try:
							cursor.execute("select TSCount, TimeStamp, ChassisID, Filename, Interface, Status,LogMessage from Interface where Interface = '"+InterfaceSelection+"'")
							Output = cursor.fetchall()
						except:
							print("Invalid interface. Please try again")
							continue
						if len(Output) < 1:
							print("There are no logs for that interface, please enter another interface")
							print("")
							continue
						else:
							ValidSubSelection = False
							while ValidSubSelection == False:
								print("There are "+str(len(Output))+" flap logs for that interface")
								print("[1] - Export to XLSX, limit 1,000,000 rows")
								print("[2] - Display logs in console - Not Implemented")
								print("[3] - Filter the logs by timestamp - Not Implemented")
								print("[4] - Show how long the interface down was for - Not Implemented")
								print("[0] - Return to Interface analysis menu")
								ValidSubSelection = input("What would you like to do with the logs for "+InterfaceSelection+"? [0]  ")
								match ValidSubSelection:
									case "1":
										pass
									case "2":
										pass
									case "3":
										pass
									case "4":
										pass
									case "0":
										ValidSubSelection = True
			case "3":
				pass
			case "0":
				ValidSelection = True
				return

def UnusedAnalysis(conn,cursor,api=False):
	print("Checking the logs for Unused logs")
	AnalysisOutput = ""
	global AnalysisInitialized
	if AnalysisInitialized == False:
		AnalysisInit(conn,cursor)
		AnalysisInitialized = True
	global UnusedInitialized
	if UnusedInitialized == False:
		UnusedInitialized = True
		cursor.execute("select LogMessage,Category,LogMeaning from Analysis where category like '%Unused%'")
		Analysis = cursor.fetchall()
		LogDictionary = []
		LogMeaning = []
		for line in Analysis:
			Message = line[0]
			Meaning = line[2]
			Message.strip()
			Meaning.strip()
			#print(Message)
			#print(Meaning)
			LogDictionary.append(Message)
			LogMeaning.append(Meaning)
		counter = 0
		DictionaryLength = len(LogDictionary)
		while counter < DictionaryLength:
			query = "update Logs set LogMeaning = '"+LogMeaning[counter]+"', Category = 'Unused' where LogMessage like '%"+LogDictionary[counter]+"%'"
			#print(query)
			cursor.execute(query)
			#cursor.execute("update Logs (LogMeaning, Category) values ("+LogMeaning[counter]+", "+Category[counter]+") where LogMessage like '%"+LogDictionary[counter]+"%'")
			counter += 1
	cursor.execute("select count(*) from logs where category like '%Unused%'")
	output = cursor.fetchall()
	UnusedCount = CleanOutput(str(output))
	if UnusedCount == "0":
		print("There are no Unused logs in the log database. Returning to previous menu.")
		return
	ValidSubselection = False
	while ValidSubselection == False:
		print("There are "+UnusedCount+" logs in the Unused category")
		if api == False:
			Subselection = input("Please confirm that you would like to remove them from the Log Database. [Yes]  ") or "Yes"
		if api == True:
			Subselection = "Yes"
		if "yes" in Subselection or "Yes" in Subselection or "y" in Subselection or "Y" in Subselection:
			cursor.execute("delete from logs where category like '%Unused%'")
			cursor.execute("select count(*) from Logs")
			count = CleanOutput(str(cursor.fetchall()))
			cursor.execute("select Timestamp from Logs order by Timestamp desc limit 1")
			NewestLog = CleanOutput(str(cursor.fetchall()))
			cursor.execute("select Timestamp from Logs order by Timestamp limit 1")
			OldestLog = CleanOutput(str(cursor.fetchall()))
			print(UnusedCount+" logs have been removed. There are now "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
			if api == True:
				OutputFileName = "SwlogsParsed-CleanLogs-tsbuddy.xlsx"
				query = "SELECT TSCount,ChassisID, Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs order by Timestamp,Filename limit 1048576"
				ExportXLSX(conn,cursor,query,OutputFileName)
				AnalysisOutput = (UnusedCount+" logs have been removed. There are now "+count+" logs ranging from "+OldestLog+" to "+NewestLog+". The clean logs have been exported to "+OutputFileName)
				return AnalysisOutput
			ValidSubselection = True
			continue
		if "no" in Subselection or "No" in Subselection or "n" in Subselection or "N"in Subselection :
			print("Canceling delete request")
			ValidSubselection = True
			continue
		else:
			print("Invalid input, please answer 'Yes' or 'No'")

def CriticalAnalysis(conn,cursor,api=False):
	print("Checking the logs for Interface issues")
	global AnalysisInitialized
	if AnalysisInitialized == False:
		AnalysisInit(conn,cursor)
		AnalysisInitialized = True
	global CriticalInitialized
	if CriticalInitialized == False:
		CriticalInitialized = True
		cursor.execute("select LogMessage,Category,LogMeaning from Analysis where category like '%Critical%'")
		AnalysisOutput = cursor.fetchall()
		LogDictionary = []
		LogMeaning = []
		for line in AnalysisOutput:
			Message = line[0]
			Meaning = line[2]
			Message.strip()
			Meaning.strip()
			#print(Message)
			#print(Meaning)
			LogDictionary.append(Message)
			LogMeaning.append(Meaning)
		counter = 0
		DictionaryLength = len(LogDictionary)
		while counter < DictionaryLength:
			query = "update Logs set LogMeaning = '"+LogMeaning[counter]+"', Category = 'Critical' where LogMessage like '%"+LogDictionary[counter]+"%'"
			#print(query)
			cursor.execute(query)
			#cursor.execute("update Logs (LogMeaning, Category) values ("+LogMeaning[counter]+", "+Category[counter]+") where LogMessage like '%"+LogDictionary[counter]+"%'")
			counter += 1
	cursor.execute("select count(*) from Logs where Category like '%Critical%'")
	Output = cursor.fetchall()
	count = CleanOutput(str(Output))
	ValidSelection = False
	while ValidSelection == False:
		print("")
		print("There are "+count+" Critical logs")
		print("")
		print("[1] - Export to XLSX - Limit 1,000,000 Rows")
		print("[2] - Display Critical logs in the console")
		print("[3] - Provide Root Cause Analysis")
		print("[0] - Return to Analysis Menu")
		Selection = input("What would you like to do with the logs? [0]  ") or "0"
		match Selection:
			case "1":
				if PrefSwitchName != "None":
					OutputFileName = PrefSwitchName+"-SwlogsParsed-CriticalLogs-tsbuddy.xlsx"
				else:
					OutputFileName = "SwlogsParsed-CriticalLogs-tsbuddy.xlsx"
				if TSImportedNumber > 1:
					query = "select tscount,ChassisID,Timestamp,LogMessage,LogMeaning from Logs where category like '%Critical%' order by timestamp"
				else:
					query = "select ChassisID,Timestamp,LogMessage,LogMeaning from Logs where category like '%Critical%' order by timestamp"
				ExportXLSX(conn,cursor,query,OutputFileName)
			case "2":
				ValidCountSelection = False
				while ValidCountSelection == False:
					countselection = input("How many logs would you like to diplay in the console? There are "+count+" total Critical logs. [All]  ") or "All"
					if countselection == "All":
						countselection = int(count)
					if not str(countselection).isnumeric():
						print("Invalid number. Please insert a number")
						continue
					if int(countselection) > int(count):
						print("There are few logs than you are requesting. Printing all of them")
						cursor.execute("select ChassisID,TimeStamp,LogMessage,LogMeaning from Logs where category like '%Critical%' order by Timestamp")
						CriticalLogs = cursor.fetchall()
						print("")
						print("ChassisID, Timestamp, LogMessage, LogMeaning")
						print("----------------------")
						for line in CriticalLogs:
							line = str(line)
							line = line.replace("(","")
							line = line.replace(")","")
							print(line)
						ValidCountSelection = True
					else:
						cursor.execute("select ChassisID,TimeStamp,LogMessage,LogMeaning from Logs where category like '%Critical%' order by Timestamp limit "+str(countselection))
						CriticalLogs = cursor.fetchall()
						print("")
						print("ChassisID, Timestamp, LogMessage, LogMeaning")
						print("----------------------")
						for line in CriticalLogs:
							line = str(line)
							line = line.replace("(","")
							line = line.replace(")","")
							print(line)
						ValidCountSelection = True
			case "3":
				RootCauseAnalysis(conn,cursor)
			case "0":
				ValidSelection = True
			case _:
				print("Invalid selection")

def RootCauseAnalysis(conn,cursor,api=False):
	MACFlaps = []
	isMACFlapProblem = False
	ArpInfoOverwrite = []
	isArpInfoOverwriteProblem = False
	Reboots = []
	isRebootProblem = False
	Health = []
	isHealthProblem = False
	PortFlaps = []
	isPortFlapsProblem = False
	Floods = []
	isFloodProblem = []
	VC = []
	isVCProblem = False

def AllKnownLogs(conn,cursor,api=False):
	global AnalysisInitialized
	if AnalysisInitialized == False:
		AnalysisInit(conn,cursor)
		AnalysisInitialized = True
	#Count of categories
	CategoryList = ["Reboot","Critical","Hardware","Connectivity","Health","SPB","VC","Interface","Upgrades","General","MACLearning","Unused","STP","Security","Unclear","Unknown","OSPF"]
	RebootCount = 0
	CriticalCount = 0
	HardwareCount = 0
	ConnectivityCount = 0
	HealthCount = 0
	SPBCount = 0
	VCCount = 0
	InterfaceCount = 0
	UpgradesCount = 0
	GeneralCount = 0
	MACLearningCount = 0
	UnusedCount = 0
	STPCount = 0
	SecurityCount = 0
	UnclearCount = 0
	UnknownCount = 0
	OSPFCount = 0
###This whole thing can be done better if we can compare all Logs.LogMessage against Analysis.LogMessage in SQL. This must support wildcards.
	#Initialize all Categories
	global AllLogsInitialized
	global UnusedInitialized
	global RebootsInitialized
	global VCInitialized
	global InterfaceInitialized
	global OSPFInitialized
	global SPBInitialized
	global HealthInitialized
	global ConnectivityInitialized
	global CriticalInitialized
	global OSPFInitialized
	if AllLogsInitialized == False:
		AllLogsInitialized = True
		RebootsInitialized = True
		VCInitialized = True
		InterfaceInitialized = True
		OSPFInitialized = True
		SPBInitialized = True
		HealthInitialized = True
		ConnectivityInitialized = True
		CriticalInitialized = True
		UnusedInitialized = True
		OSPFInitialized = True
		cursor.execute("select LogMessage,Category,LogMeaning from Analysis")
		AnalysisOutput = cursor.fetchall()
		Category = []
		LogDictionary = []
		LogMeaning = []
		for line in AnalysisOutput:
			Message = line[0]
			Meaning = line[2]
			Message.strip()
			Meaning.strip()
			#print(Message)
			#print(Meaning)
			Category.append(line[1])
			LogDictionary.append(Message)
			LogMeaning.append(Meaning)
		counter = 0
		DictionaryLength = len(LogDictionary)
		while counter < DictionaryLength:
			query = "update Logs set LogMeaning = '"+LogMeaning[counter]+"', Category = '"+Category[counter]+"' where LogMessage like '%"+LogDictionary[counter]+"%'"
			#print(query)
			cursor.execute(query)
			#cursor.execute("update Logs (LogMeaning, Category) values ("+LogMeaning[counter]+", "+Category[counter]+") where LogMessage like '%"+LogDictionary[counter]+"%'")
			counter += 1
		cursor.execute("update Logs set Category = 'Unknown' where Category is NULL")
	#Group by category
	for category in CategoryList:
		cursor.execute("select count(*) from Logs where category like '%"+category+"%'")
		line = cursor.fetchall()
		match category:
			case "Reboot":
				RebootCount += int(CleanOutput(str(line[0])))
			case "Critical":
				CriticalCount += int(CleanOutput(str(line[0])))
			case "Hardware":
				HardwareCount += int(CleanOutput(str(line[0])))
			case "Connectivity":
				ConnectivityCount += int(CleanOutput(str(line[0])))
			case "Health":
				HealthCount += int(CleanOutput(str(line[0])))
			case "SPB":
				SPBCount += int(CleanOutput(str(line[0])))
			case "VC":
				VCCount += int(CleanOutput(str(line[0])))
			case "Interface":
				InterfaceCount += int(CleanOutput(str(line[0])))
			case "Upgrades":
				UpgradesCount += int(CleanOutput(str(line[0])))
			case "General":
				GeneralCount += int(CleanOutput(str(line[0])))
			case "MACLearning":
				MACLearningCount += int(CleanOutput(str(line[0])))
			case "Unused":
				UnusedCount += int(CleanOutput(str(line[0])))
			case "STP":
				STPCount += int(CleanOutput(str(line[0])))
			case "Security":
				SecurityCount += int(CleanOutput(str(line[0])))
			case "Unclear":
				UnclearCount += int(CleanOutput(str(line[0])))
			case "Unknown":
				UnknownCount += int(CleanOutput(str(line[0])))
			case "OSPF":
				OSPFCount += int(CleanOutput(str(line[0])))
	AllCategoryCounts = {OSPFCount: "OSPF", UnclearCount: "Unclear", RebootCount: "Reboot", CriticalCount: "Critical", HardwareCount: "Hardware", ConnectivityCount: "Connectivity", HealthCount: "Health", SPBCount: "SPB", VCCount: "VC", InterfaceCount: "Interface", UpgradesCount: "Upgrades", GeneralCount: "General", MACLearningCount: "MAC Learning", UnusedCount: "Unused", STPCount: "STP", SecurityCount: "Security", UnknownCount: "Unknown"}
	AllCategoryCountsSorted = dict(sorted(AllCategoryCounts.items(),reverse=True))
	KeysInterator = iter(AllCategoryCountsSorted.keys())
	ValuesInterator = iter(AllCategoryCountsSorted.values())
	Category1 = next(ValuesInterator)
	Count1 = next(KeysInterator)
	while Category1 == "Unknown" or Category1 == "Unused":
		Category1 = next(ValuesInterator)
		Count1 = next(KeysInterator)
	Category2 = next(ValuesInterator)
	Count2 = next(KeysInterator)
	while Category2 == "Unknown" or Category2 == "Unused":
		Category2 = next(ValuesInterator)
		Count2 = next(KeysInterator)
	Category3 = next(ValuesInterator)
	Count3 = next(KeysInterator)
	while Category3 == "Unknown" or Category3 == "Unused":
		Category3 = next(ValuesInterator)
		Count3 = next(KeysInterator)
	print(AllCategoryCountsSorted)
	cursor.execute("select count(*) from Logs")
	AllLogCount = CleanOutput(str(cursor.fetchall()))
	print("")
	print("Out of all of the "+AllLogCount+" logs:")
	print("The category with the most logs is "+Category1+" with "+str(Count1)+" logs")
	print("The category with the next most logs is "+Category2+" with "+str(Count2)+" logs")
	print("The category with the third most logs is "+Category3+" with "+str(Count3)+" logs")
	print("It is recommended to run the Analysis tool for "+Category1)
	print("*Note that some logs will fall under several categories")
	print("")
	print("There are "+str(CriticalCount)+" Critical logs.")
	if CriticalCount > 0:
		print("It is recommended to view any Critical logs")
	cursor.execute("select count(*) from Logs where LogMeaning is not null")
	Output = cursor.fetchall()
	#print(Output)
	KnownLogCount = CleanOutput(str(Output))
	ValidSubSelection = False
	while ValidSubSelection == False:
		print("")
		print("There are "+KnownLogCount+" logs with a known explanation.")
		print("[1] - Export to XLSX - Limit 1,000,000 Rows")
		print("[2] - Review the Critical Logs")
		print("[3] - Run an Analysis on "+Category1)
		print("[4] - Run an Analysis on "+Category2)
		print("[5] - Run an Analysis on "+Category3)
		print("[0] - Return to Analysis Menu")
		SubSelection = input("What would you like to do with the logs? [0]  ") or "0"
		match SubSelection:
			case "1":
				if PrefSwitchName != "None":
					OutputFileName = PrefSwitchName+"-SwlogsParsed-AllKnownLogs-tsbuddy.xlsx"
				else:
					OutputFileName = "SwlogsParsed-AllKnownLogs-tsbuddy.xlsx"
				if TSImportedNumber > 1:
					query = "select TSCount,ChassisID,Timestamp,Category,LogMessage,LogMeaning from Logs where LogMeaning is not Null order by Timestamp"
				else:
					query = "select ChassisID,Timestamp,Category,LogMessage,LogMeaning from Logs where LogMeaning is not Null order by Timestamp"
				ExportXLSX(conn,cursor,query,OutputFileName)
			case "2":
				AnalysisSelector(conn,cursor,"Critical")
			case "3":
				ValidSubSelection = True
				AnalysisSelector(conn,cursor,Category1)
			case "4":
				ValidSubSelection = True
				AnalysisSelector(conn,cursor,Category2)
			case "5":
				ValidSubSelection = True
				AnalysisSelector(conn,cursor,Category3)
			case "Top":
				if PrefSwitchName != "None":
					OutputFileName = PrefSwitchName+"-SwlogsParsed-TopLogswithCategory-tsbuddy.xlsx"
				else:
					OutputFileName = "SwlogsParsed-TopLogswithCategory-tsbuddy.xlsx"
				query = "select count(*),LogMessage,Category,Priority from Logs where Category not like '%Unused%' and Priority not like '%DBG%' group by LogMessage order by count(*) desc limit 200"
				ExportXLSX(conn,cursor,query,OutputFileName)
				os.startfile(OutputFileName)
			case "Pri":
				OutputFileName = "SwlogsParsed-TopUnknownLogsAboveInfo-tsbuddy.xlsx"
				query = "select count(*),Priority,LogMessage from logs where Priority not like '%INFO%' and Priority not like '%DBG%' and Category like '%Unknown%' group by LogMessage order by count(*) desc"
				ExportXLSX(conn,cursor,query,OutputFileName)
				os.startfile(OutputFileName)
			case "0":
				ValidSubSelection = True
				return

def CategoryLogs(conn,cursor,category):
	cursor.execute("select LogMessage,LogMeaning from Analysis where Category like '%"+category+"%'")
	Definitions = cursor.fetchall()
	LogDictionary = []
	LogMeaning = []
	for line in Definitions:
		LogDictionary.append(line[0])
		LogMeaning.append(line[1])
	MatchedLogs = []
	counter = 0
	query = ""
	while counter < len(LogDictionary):
		query = query+"(select TSCount,ChassisID,Timestamp,LogMessage from Logs where LogMessage like '%"+LogDictionary[counter]+"%')"
		counter += 1
		if counter < len(LogDictionary):
			query += " UNION "
	cursor.execute(query)
	LoopOutput = cursor.fetchall()
	if len(LoopOutput) > 0:
		for line in LoopOutput:
			line.append(LogMeaning[counter])
			MatchedLogs.append(line)
		counter += 1
	ValidSelection = False
	while ValidSelection == False:
		print("There are "+str(len(MatchedLogs))+" "+category+" logs.")
		print("[1] - Export to XLSX - Limit 1,000,000 Rows")
		print("[2] - Display in console")
		if category != "Critical" and category != "Unused" and category != "Unknown" and category != "Unclear":
			print("[3] - Analyze these logs for problems")
		print("[0] - Return to Analysis Menu - WIP")
		Selection = input("What would you like to do with the logs? [0]  ") or "0"
		match Selection:
			case "1":
				if PrefSwitchName != "None":
					OutputFileName = PrefSwitchName+"-SwlogsParsed-CriticalLogs-tsbuddy.xlsx"
				else:
					OutputFileName = "SwlogsParsed-CriticalLogs-All-tsbuddy.xlsx"
				try:
					with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
						DataDict = {'TSCount': MatchedCount, 'ChassisID': MatchedCategories, 'Timestamp': MatchedLogs, 'LogMessage': MatchedMeanings}
						print("Exporting data to file. This may take a moment.")
						Filedata = pd.DataFrame(DataDict)
						Filedata.to_excel(writer, sheet_name="ConsolidatedLogs")
						workbook = writer.book
						worksheet = writer.sheets["ConsolidatedLogs"]
						text_format = workbook.add_format({'num_format': '@'})
						worksheet.set_column("H:H", None, text_format)
					print("Export complete. Your logs are in "+OutputFileName)
				except:
					print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
			case "2":
				ValidCountSelection = False
				while ValidCountSelection == False:
					countselection = input("How many logs would you like to diplay in the console? There are "+str(len(output))+" total unique logs. [All]  ") or "All"
				"""
					if not int(countselection) and not "All":
									print("Invalid number. Please insert a number")
									continue
								if int(countselection) > len(output):
									print("There are few logs than you are requesting. Printing all of them")
									countselection = "All"
								if countselection == "All":
									cursor.execute("select count(*),logmessage from Logs group by logmessage order by count(*) desc")
									UniqueLogs = cursor.fetchall()
									print("")
									print("Log Count, Log Message")
									print("----------------------")
									for line in UniqueLogs:
										line = str(line)
										line = line.replace("(","")
										line = line.replace(")","")
										print(line)
									ValidCountSelection = True
								else:
									cursor.execute("select count(*),logmessage from Logs group by logmessage order by count(*) desc limit "+countselection)
									UniqueLogs = cursor.fetchall()
									print("")
									print("Log Count, Log Message")
									print("----------------------")
									for line in UniqueLogs:
										line = str(line)
										line = line.replace("(","")
										line = line.replace(")","")
										print(line)
									ValidCountSelection = True
				"""
			case "3":
				pass
			case "0":
				ValidSelection = True
				return

def SearchTime(conn,cursor,NewestLog,OldestLog):
	ValidSelection = False
	while ValidSelection == False:
		print("The logs contain the time range of "+OldestLog+" to "+NewestLog)
		print("[1] - Show all logs between a time range")
		print("[2] - Show all logs for a specific day")
		print("[3] - Show all logs for a specific hour - Not implemented")
		print("[4] - Show all logs for a specific minute - Not implemented")
		print("[0] - Exit")
		#newline
		print("")
		selection = input("What time range would you like to filter by? [0] ") or "0"
		match selection:
			case "1":
				ValidSubselection = False
				while ValidSubselection == False:
					timerequested1 = input("What is first time in your search range? Please use part of the format yyyy-mm-dd hh:mm:ss:  ")
					if timerequested1 == "":
						ValidSelection == True
						return
					timerequested2 = input("What is second time in your search range? Please use part of the format yyyy-mm-dd hh:mm:ss:  ")
					if timerequested1 == timerequested2:
						print("Those are the same times, please insert two different times")
						continue
					PaddingTime = "2000-01-01 00:00:00"
					Time1Len = len(timerequested1)
					Time2Len = len(timerequested2)
					#print(timerequested1)
					#print(Time1Len)
					Time1Full = timerequested1+PaddingTime[Time1Len:19]
					#print(Time1Full)
					Time2Full = timerequested2+PaddingTime[Time2Len:19]
					format_string = "%Y-%m-%d %H:%M:%S"
					Time1 = datetime.datetime.strptime(Time1Full,format_string)
					Time2 = datetime.datetime.strptime(Time2Full,format_string)
					#print(Time1)
					#print(Time2)
					command = ""
					try:
						if Time1 > Time2:
							cursor.execute("Select count(*) from Logs where TimeStamp >= '"+str(Time2)+"' and TimeStamp <= '"+str(Time1)+"'")
							TimeSwap = Time1
							Time1 = Time2
							Time2 = TimeSwap
						if Time2 > Time1:
							cursor.execute("Select count(*) from Logs where TimeStamp >= '"+str(Time1)+"' and TimeStamp <= '"+str(Time2)+"'")
					except:
						print("Unable to run the command. Check your syntax and try again.")
					count = CleanOutput(str(cursor.fetchall()))
					print(count)
					print("")
					print("There are "+str(count)+" logs between "+str(Time1)+" and "+str(Time2)+". What would you like to do?")
					print("[1] - Export logs to xlsx - Limit 1,000,000 rows")
					print("[2] - Show the number of logs by hour - Not implemented")						
					print("[3] - Show the most common logs - Not implemented")
					print("[4] - Run another search by time - Not implemented")
					print("[0] - Return to Main Menu")
					Subselection = input("What would you like to do with the logs?")
					match Subselection:
						case "1":
							if PrefSwitchName != "None":
								OutputFileName = PrefSwitchName+"-SwlogsParsed-TimeRange-tsbuddy.xlsx"
							else:
								OutputFileName = "SwlogsParsed-TimeRange-tsbuddy.xlsx"
							if TSImportedNumber > 1:
								query = "SELECT TScount,ChassisID, Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs where TimeStamp >= '"+str(Time1)+"' and TimeStamp <= '"+str(Time2)+"' order by timestamp"
							else:
								query = "SELECT ChassisID, Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs where TimeStamp >= '"+str(Time1)+"' and TimeStamp <= '"+str(Time2)+"' order by timestamp"
							ExportXLSX(conn,cursor,query,OutputFileName)
						case "2":
							pass
						case "3":
							pass
						case "4":
							pass
						case "0":
							ValidSubselection = True
							ValidSelection = True
							return
			case "2":
				ValidSubselection = False
				while ValidSubselection == False:
					timerequested = input("What day do you want logs for? Please use the format yyyy-mm-dd:  ")
					try:
						cursor.execute("Select count(*) from Logs where TimeStamp like '%"+timerequested+"%'")
					except:
						print("Unable to run the command. Check your syntax and try again.")
					else:
						count = CleanOutput(str(cursor.fetchall()))
						print("")
						print("There are "+str(count)+" logs for "+timerequested+". What would you like to do?")
						print("[1] - Export logs to xlsx - Limit 1,000,000 rows")
						print("[2] - Show the number of logs by hour - Not implemented")
						print("[3] - Show the most common logs - Not implemented")
						print("[4] - Run another search by time - Not implemented")
						print("[0] - Return to Main Menu")
						Subselection = input("What would you like to do with the logs?")
						match Subselection:
							case "1":
								if PrefSwitchName != "None":
									OutputFileName = PrefSwitchName+"-SwlogsParsed-"+timerequested+"-tsbuddy.xlsx"
								else:
									OutputFileName = "SwlogsParsed-"+timerequested+"-tsbuddy.xlsx"
								query = "Select * from Logs where TimeStamp like '%"+timerequested+"%' order by TimeStamp"
								ExportXLSX(conn,cursor,query,OutputFileName)
							case "2":
								pass
							case "3":
								pass
							case "4":
								pass
							case "0":
								ValidSubselection = True
								ValidSelection = True
								return


			case "3":
				pass
			case "4":
				pass
			case "0":
				ValidSelection = True
				return

def extract_tar_files(base_path='.'):
	print("Extracting all files for "+str(base_path))
	extracttar.extract_archives(base_path)

def ExportXLSX(conn,cursor,query,OutputFileName):
	try:
		with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
			print("Exporting data to file. This may take a moment.")
			Output = pd.read_sql(query, conn)
			Output.to_excel(writer, sheet_name="ConsolidatedLogs")
			workbook = writer.book
			worksheet = writer.sheets["ConsolidatedLogs"]
			text_format = workbook.add_format({'num_format': '@'})
			worksheet.set_column("H:H", None, text_format)
		print("Export complete. Your logs are in "+OutputFileName)
	except:
		print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")


def main(filename='',request="",chassis_selection='all',time='',api=True):
	parser = argparse.ArgumentParser()
	parser.add_argument('--filename', required=False)
	parser.add_argument('--request', required=False, choices=['All Logs','Reboot','VC','Interface','OSPF','SPB','Health','Connectity','Critical','Hardware','Upgrades','General','MACLearning','Unused','STP','Security','Unclear','Unknown'])
	parser.add_argument('--chassis_selection', required=False)
	parser.add_argument('--time', required=False)
	parser.add_argument('--api',required=False, action="store_true")
	args = parser.parse_args()
	#print(args)
	if args.filename is not None:
		filename = args.filename
	if args.request is not None:
		request = args.request
	if args.chassis_selection is not None:
		chassis_selection = args.chassis_selection
	if args.time is not None:
		time = args.time
	api = args.api
	AnalysisOutput = ""
	global TSImportedNumber
	TSImportedNumber += 1
	with sqlite3.connect(':memory:') as conn:
		cursor = conn.cursor()
		if filename == '':
			filename = get_filepath()
			TSDirName = filename
		if not os.path.isdir(filename):
			TSDirName = str(filename.replace(".tar",""))
			try:
				os.mkdir('./'+TSDirName)
				print("Made directory at "+str('./'+TSDirName))
			except FileExistsError:
				print("Dir already exists at "+str('./'+TSDirName))
			#extract first TS
			with tarfile.open(filename, "r") as tar:
				for member in tar.getmembers():
					if member.isdir():
						os.mkdir(TSDirName+"/"+member.name)
				tar.extractall('./'+TSDirName)
		extract_tar_files(str("./"+TSDirName))
		#dirpath = os.path.dirname(str(TSDirName))
		print("Dirpath = "+str(TSDirName))
		OldestLog,NewestLog = load_logs1(conn,cursor,TSDirName,chassis_selection)
		load2 = False
		if time == '':
			load2 = True
		if time != '':
			PaddingTime = "2000-01-01 00:00:00"
			format_string = "%Y-%m-%d %H:%M:%S"
			timeLen = len(time)
			OldestLogLen = len(OldestLog)
			NewestLogLen = len(NewestLog)
			timeFull = time+PaddingTime[timeLen:19]
			OldestLogFull = OldestLog+PaddingTime[OldestLogLen:19]
			NewestLogFull = NewestLog+PaddingTime[NewestLogLen:19]
			time = datetime.datetime.strptime(timeFull[:19],format_string)
			OldestLog = datetime.datetime.strptime(OldestLogFull[:19],format_string)
			NewestLog = datetime.datetime.strptime(NewestLogFull[:19],format_string)
			print(time)
			print(OldestLog)
			print(NewestLog)
			if time < OldestLog:
				load2 = True
			if time > NewestLog:
				AnalysisOutput = "The time you have requested is not present in the logs. These logs only go up to "+NewestLog
				return AnalysisOutput
		if load2 == True:
			print("Loading archive swlogs")
			load_logs2(conn,cursor,chassis_selection)
		if request != "":
			print("api is "+str(api))
			AnalysisOutput = AnalysisSelector(conn,cursor,request,api)
			print("AnalysisOutput = "+str(AnalysisOutput))
		else:
			analysis_menu(conn,cursor)
		return AnalysisOutput

if __name__ == "__main__":
	main()
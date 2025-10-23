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
Unused
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

def AnalysisInit(conn,cursor):
	print("Initializing log analysis")
	cursor.execute("alter table Logs add LogMeaning text")
	cursor.execute("alter table Logs add Category text")
	src_dir = os.path.dirname(os.path.abspath(__file__))
	data = pd.read_csv(src_dir+"/loglist-master.csv")
	data.to_sql('Analysis', conn, index=True)
	global AnalysisInitialized
	AnalysisInitialized = True

def RebootAnalysis(conn,cursor,api):
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
				###### After option select	
				try:
					with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
						print("Exporting data to file. This may take a moment.")
						if TSImportedNumber > 1:
							Output = pd.read_sql("select TSCount,ChassisID,Filename,Timestamp,SwitchName,Source,Model,AppID,Subapp,Priority,LogMessage from Logs where category like '%Reboot%' order by Timestamp", conn)
						else:
							Output = pd.read_sql("select ChassisID,Filename,Timestamp,SwitchName,Source,Model,AppID,Subapp,Priority,LogMessage from Logs where category like '%Reboot%' order by Timestamp", conn)
						Output.to_excel(writer, sheet_name="ConsolidatedLogs")
						workbook = writer.book
						worksheet = writer.sheets["ConsolidatedLogs"]
						text_format = workbook.add_format({'num_format': '@'})
						worksheet.set_column("H:H", None, text_format)
					print("Export complete. Your logs are in "+OutputFileName)
				except:
					print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
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

def InterfaceAnalysis(conn,cursor,api):
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
				try:
					with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
						print("Exporting data to file. This may take a moment.")
						if TSImportedNumber > 1:
							Output = pd.read_sql("select tscount,count(*),ChassisID as ReportingChassis, Interface from Interface where Status = 'DOWN' group by tscount,Interface order by count(*) desc", conn)
						else:
							Output = pd.read_sql("select count(*),ChassisID as ReportingChassis, Interface from Interface where Status = 'DOWN' group by Interface order by count(*) desc", conn)	
						Output.to_excel(writer, sheet_name="ConsolidatedLogs")
						workbook = writer.book
						worksheet = writer.sheets["ConsolidatedLogs"]
						text_format = workbook.add_format({'num_format': '@'})
						worksheet.set_column("H:H", None, text_format)
					print("Export complete. Your logs are in "+OutputFileName)
				except:
					print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
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

def AnalysisSelector(conn,cursor,request,api):
	match request:
		case "Reboot":
			AnalysisOutput = RebootAnalysis(conn,cursor,api)
		case "VC":
			VCAnalysis(conn,cursor,api)
		case "Interface":
			AnalysisOutput = InterfaceAnalysis(conn,cursor,api)
		case "OSPF":
			OSPFAnalysis(conn,cursor,api)
		case "SPB":
			SPBAnalysis(conn,cursor,api)
		case "Health":
			HealthAnalysis(conn,cursor,api)
		case "Connectivity":
			ConnectivityAnalysis(conn,cursor,api)
		case "Critical":
			CriticalAnalysis(conn,cursor,api)
		case "Hardware":
			HardwareAnalysis(conn,cursor,api)
		case "Upgrades":
			UpgradesAnalysis(conn,cursor,api)
		case "General":
			GeneralAnalysis(conn,cursor,api)
		case "MACLearning":
			MACLearningAnalysis(conn,cursor,api)
		case "Unused":
			UnusedAnalysis(conn,cursor,api)
		case "STP":
			STPAnalysis(conn,cursor,api)
		case "Security":
			SecurityAnalysis(conn,cursor,api)
		case "Unclear":
			UnclearAnalysis(conn,cursor,api)
		case "Unknown":
			UnknownAnalysis(conn,cursor,api)
	return AnalysisOutput

def extract_tar_files(base_path='.'):
	print("Extracting all files for "+str(base_path))
	extracttar.extract_archives(base_path)

def main(filename='',request="",chassis_selection='all',time='',api=True):
	parser = argparse.ArgumentParser()
	parser.add_argument('--filename', required=False)
	parser.add_argument('--request', required=False, choices=['All Logs','Reboot','VC','Interface','OSPF','SPB','Health','Connectity','Critical','Hardware','Upgrades','General','MACLearning','Unused','STP','Security','Unclear','Unknown'])
	parser.add_argument('--chassis_selection', required=False)
	parser.add_argument('--time', required=False)
	parser.add_argument('--api',required=False)
	args = parser.parse_args()
	print(args)
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
		AnalysisOutput = AnalysisSelector(conn,cursor,request,api)
		print("AnalysisOutput = "+str(AnalysisOutput))
		return AnalysisOutput

if __name__ == "__main__":
	main()
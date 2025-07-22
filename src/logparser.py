
import csv
import json
import os


SwlogFiles1 = []
SwlogFiles2 = []
SwlogFiles3 = []
SwlogFiles4 = []
SwlogFiles5 = []
SwlogFiles6 = []
SwlogFiles7 = []
SwlogFiles8 = []
ConsoleFiles = []
dir_list = os.listdir()

#Opens specified file, grabs the data, formats it, and exports it as a CSV
def ReadandParse(OutputFilePath,LogByLine):
	with open(OutputFilePath, 'w', newline='') as csvfile:
		OutputFile = csv.writer(csvfile)
		OutputFile.writerow(['Year', 'Month', 'Day', 'Time', 'SwitchName', 'Source', 'AppID', 'Subapp', 'Priority', 'LogMessage'])
		for line in LogByLine:
			line = line.replace("  ", " ")
			parts = line.split(" ")
			partsSize = len(parts)
			Year = parts[0]
			Month = parts[1]
			Date = parts[2]
			Time = parts[3]
			SwitchName = parts[4]
			Source = parts[5]
			if partsSize > 6:
				Appid = parts[6]
			if partsSize > 7:
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
			OutputFile.writerow([Year, Month, Date, Time, SwitchName, Source, Appid, Subapp, Priority, LogMessage])
		

def main():
#Find swlogs in current directory
	for file in dir_list:
		if 'swlog_chassis1' in file:
			SwlogFiles1.append(file)
		if 'swlog_chassis2' in file:
			SwlogFiles2.append(file)
		if 'swlog_chassis3' in file:
			SwlogFiles3.append(file)
		if 'swlog_chassis4' in file:
			SwlogFiles4.append(file)
		if 'swlog_chassis5' in file:
			SwlogFiles5.append(file)
		if 'swlog_chassis6' in file:
			SwlogFiles6.append(file)
		if 'swlog_chassis7' in file:
			SwlogFiles7.append(file)
		if 'swlog_chassis8' in file:
			SwlogFiles8.append(file)
		if 'swlog_localConsole' in file:
			ConsoleFiles.append(file)
	
	#Combine all log files
	
	#SwlogChassis1
	for logfile in SwlogFiles1:
		with open(logfile, 'r') as file:
			LogByLine = file.readlines()
	OutputFilePath = 'Chassis1SwlogsParsed.csv'
	ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
	with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
		data = list(csv.DictReader(csvfile))
	with open('Chassis1SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
		json.dump(data, jsonfile, indent=4)
	
	#SwlogChassis2
	if SwlogFiles2 != []:
		for logfile in SwlogFiles2:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'Chassis2SwlogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('Chassis2SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
		
	#SwlogChassis3
	if SwlogFiles3 != []:
		for logfile in SwlogFiles3:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'Chassis3SwlogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('Chassis3SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
	
	#SwlogChassis4
	if SwlogFiles4 != []:
		for logfile in SwlogFiles4:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'Chassis4SwlogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('Chassis4SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
	
	#SwlogChassis5
	if SwlogFiles5 != []:
		for logfile in SwlogFiles5:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'Chassis5SwlogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('Chassis5SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
	
	#SwlogChassis6
	if SwlogFiles6 != []:
		for logfile in SwlogFiles6:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'Chassis6SwlogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('Chassis6SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
	
	#SwlogChassis7
	if SwlogFiles7 != []:
		for logfile in SwlogFiles7:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'Chassis7SwlogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('Chassis7SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
	
	#SwlogChassis8
	if SwlogFiles8 != []:
		for logfile in SwlogFiles8:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'Chassis8SwlogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('Chassis8SwlogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
	
	#ConsoleFiles
	if ConsoleFiles != []:
		for logfile in ConsoleFiles:
			with open(logfile, 'r') as file:
				LogByLine = file.readlines()
		OutputFilePath = 'ConsoleLogsParsed.csv'
		ReadandParse(OutputFilePath,LogByLine)
	#Convert to JSON
		with open(OutputFilePath, mode='r', newline='', encoding='utf-8') as csvfile:
			data = list(csv.DictReader(csvfile))
		with open('ConsoleLogsParsed.json', mode='w', encoding='utf-8') as jsonfile:
			json.dump(data, jsonfile, indent=4)
	
	
main()

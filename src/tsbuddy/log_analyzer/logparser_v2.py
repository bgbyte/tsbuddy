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
#import tsbuddy


SEVEN_ZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"


#
#Limitations
#This application does not support switches in standalone mode

#
#TODO
#TODO: X logs before and after targetlog
#TODO: Add LogMeaning
#TODO: Integrate Tech Support downloader
#TODO: 9907s have per NI logs
#TODO: Can we make 7zip silent? Or remove it
#TODO: Add another TS? For comparing a timeline of multiple switches?
#TODO: Log Count per day/hour/minute


#Known issues:
#I/O Error on program close
#Main menu displays twice - Keyword, enter, export, exit, exit




#Enter IP to grab logs or use local tech support
#if local, search for tech-support and jump into it
    #The idea is that this can be run after ts-get with no cd necessary
#Search /flash and display which switches have logs
# prompt for which logs we want, include an All function
# download logs:
#Add all logs to database
##Use timestamp this time, it'll just be easier
#Print:
"""
The total number of logs is $count, ranging from $Newest_Time to $Oldest_Time".
Do you need the additional logs from the swlog archive?
"""
#If yes:
# Search /flash/swlog_archive  and download logs:
#if filename contains .tar, download, extract it, extract the gz files and add contents
#Add all logs to database
##Use timestamp this time, it'll just be easier
#Print:
"""
The total number of logs is $count, ranging from $Newest_Time to $Oldest_Time"
"What would you like to do?"
1. Export all logs to Excel (capped at 1 million)
2. Export all logs to JSON
3. Search for category*
4. Search for provided keyword*)
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






dir_list = os.listdir()

first_dir_list = os.listdir()

archive_checked = False

def extract_tar_files(base_path='.'):
    """
    Recursively extracts all .tar files under the given base_path using 7-Zip.
    """
    print("Extracting tar files with 7-Zip")
    for tar_file in Path(base_path).rglob('*.tar'):
        output_dir = tar_file.parent
        subprocess.run([
            SEVEN_ZIP_PATH,
            'x',                    # Extract command
            f'-o{output_dir}',      # Output to same directory
            '-sccUTF-8',            # Force UTF-8 encoding
            '-aos',                 # Skip overwriting existing files
            str(tar_file)
        ], check=True)
    """
    tsbuddy.extract.extract_all(base_path)
    """

def CleanOutput(string):
#Remove unneeded characters
    string = string.replace("[", "")
    string = string.replace("]", "")
    string = string.replace(",", "")
    string = string.replace("(", "")
    string = string.replace(")", "")
    string = string.replace("'", "")
    return string

def DirectQuery(conn,cursor):
    print("The table is named Logs")
    print("Columns: id, ChassisID, Filename, Timestamp, SwitchName, Source, Model, AppID, Subapp, Priority, LogMessage")
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
                    try:
                        with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
                            print("Exporting data to file. This may take a moment.")
                            OutputFile = pd.read_sql(query, conn)
                            OutputFile.to_excel(writer, sheet_name="ConsolidatedLogs")
                            workbook = writer.book
                            worksheet = writer.sheets["ConsolidatedLogs"]
                            text_format = workbook.add_format({'num_format': '@'})
                            worksheet.set_column("H:H", None, text_format)
                        print("Export complete. Your logs are in "+OutputFileName)
                    except:
                        print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
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

def collect_hosts():
    """Collects device details from the user and returns a list of hosts."""
    hosts = []
    validIP = False
    while validIP == False:
        print("\nEnter device details for the switch you want the logs from. Press Enter without an IP to use a tech support file in the current directory")
        ip = input("Enter device IP: ").strip()
        if not ip:
            validIP = True
            return hosts
        try: 
            socket.inet_aton(ip)
            validIP = True
        except:
            print("Invalid IP address, please try again.")
    username = input(f"Enter username for {ip} [admin]: ") or "admin"
    password = getpass(f"Enter password for {ip} [switch]: ") or "switch"
    hosts.append({"ip": ip, "username": username, "password": password})
    #print(hosts)
    return hosts

def grab_logs(hosts,conn,cursor):
    global SwlogDir1,SwlogDir1B,SwlogDir2,SwlogDir2B,SwlogDir3,SwlogDir4,SwlogDir5,SwlogDir6,SwlogDir7,SwlogDir8
    SFTPSwlogDir1 = ""
    SFTPSwlogDir1B = ""
    SFTPSwlogDir2B = ""
    SFTPSwlogDir2 = ""
    SFTPSwlogDir3 = ""
    SFTPSwlogDir4 = ""
    SFTPSwlogDir5 = ""
    SFTPSwlogDir6 = ""
    SFTPSwlogDir7 = ""
    SFTPSwlogDir8 = ""
    #paramiko.util.log_to_file("paramiko-tsbuddy.log")
    #print(hosts)
    hasChassis = []
    for host in hosts:
        ip = host["ip"]
        username = host["username"]
        password = host["password"]
        print("Connecting to "+str(ip))
        try:
            transport = paramiko.Transport((ip,22))
            transport.connect(None,username,password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            #Check for mnt chassis
            #print("checking mnt")
            try:
                sftp.stat('/mnt/')
                for file in sftp.listdir('/mnt/'):
                    if fnmatch.fnmatch(file, "chassis1_CMMA") and "1" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("1")
                        SFTPSwlogDir1 = "/mnt/chassis1_CMMA/"
                    if fnmatch.fnmatch(file, "chassis1_CMMB") and "1" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("1B")
                        SFTPSwlogDir1B = "/mnt/chassis1_CMMB/"
                    if fnmatch.fnmatch(file, "chassis2_CMMA") and "2" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("2")
                        SFTPSwlogDir2 = "/mnt/chassis2_CMMA/"
                    if fnmatch.fnmatch(file, "chassis2_CMMB") and "2" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("2B")
                        SFTPSwlogDir2B = "/mnt/chassis2_CMMB/"
                    if fnmatch.fnmatch(file, "chassis3_CMMA") and "3" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("3")
                        SFTPSwlogDir3 = "/mnt/chassis3_CMMA/"
                    if fnmatch.fnmatch(file, "chassis4_CMMA") and "4" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("4")
                        SFTPSwlogDir4 = "/mnt/chassis4_CMMA/"
                    if fnmatch.fnmatch(file, "chassis5_CMMA") and "5" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("5")
                        SFTPSwlogDir5 = "/mnt/chassis5_CMMA/"
                    if fnmatch.fnmatch(file, "chassis6_CMMA") and "6" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("6")
                        SFTPSwlogDir6 = "/mnt/chassis6_CMMA/"
                    if fnmatch.fnmatch(file, "chassis7_CMMA") and "7" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("7")
                        SFTPSwlogDir7 = "/mnt/chassis7_CMMA/"
                    if fnmatch.fnmatch(file, "chassis8_CMMA") and "8" not in hasChassis:
                        #print("Downloading "+file)
                        hasChassis.append("8")
                        SFTPSwlogDir8 = "/mnt/chassis8_CMMA/"
            except:
                print("There is no mnt folder on this switch")
                pass
            #Check for Flash chassis number
            FolderChassis = []
            for file in sftp.listdir('/flash/'):
                if fnmatch.fnmatch(file, "*chassis1_CMMB*") and "1" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("1B")
                    continue
                if fnmatch.fnmatch(file, "*chassis1*") and "1" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("1")
                    continue
                if fnmatch.fnmatch(file, "*chassis2_CMMB*") and "2" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("2B")
                    continue
                if fnmatch.fnmatch(file, "*chassis2*") and "2" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("2")
                    continue
                if fnmatch.fnmatch(file, "*chassis3*") and "3" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("3")
                if fnmatch.fnmatch(file, "*chassis4*") and "4" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("4")
                if fnmatch.fnmatch(file, "*chassis5*") and "5" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("5")
                if fnmatch.fnmatch(file, "*chassis6*") and "6" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("6")
                if fnmatch.fnmatch(file, "*chassis7*") and "7" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("7")
                if fnmatch.fnmatch(file, "*chassis8*") and "8" not in hasChassis:
                    #print("Downloading "+file)
                    FolderChassis.append("8")
            if len(FolderChassis) > 1:
                TimestampCheck = {}
                for chassis in FolderChassis:
                    utime = sftp.stat('/flash/swlog_chassis'+chassis).st_mtime
                    TimestampCheck[utime] = chassis
                #print(TimestampCheck)
                SortedTimestamps = dict(sorted(TimestampCheck.items(),reverse=True))
                #print(SortedTimestamps)
                MostRecent = next(iter(SortedTimestamps.values()))
                hasChassis.append(MostRecent)
                #print("MostRecent is "+str(MostRecent))
                match MostRecent:
                    case "1":
                        SFTPSwlogDir1 = "/flash/"
                    case "1B":
                        SFTPSwlogDir1B = "/flash/"
                    case "2":
                        SFTPSwlogDir2 = "/flash/"
                    case "2B":
                        SFTPSwlogDir2B = "/flash/"
                    case "3":
                        SFTPSwlogDir3 = "/flash/"
                    case "4":
                        SFTPSwlogDir4 = "/flash/"
                    case "5":
                        SFTPSwlogDir5 = "/flash/"
                    case "6":
                        SFTPSwlogDir6 = "/flash/"
                    case "7":
                        SFTPSwlogDir7 = "/flash/"
                    case "8":
                        SFTPSwlogDir8 = "/flash/"
            else:
                hasChassis.append(FolderChassis[0])
                match FolderChassis[0]:
                    case "1":
                        SFTPSwlogDir1 = "/flash/"
                    case "1B":
                        SFTPSwlogDir1B = "/flash/"
                    case "2":
                        SFTPSwlogDir2 = "/flash/"
                    case "2B":
                        SFTPSwlogDir2B = "/flash/"
                    case "3":
                        SFTPSwlogDir3 = "/flash/"
                    case "4":
                        SFTPSwlogDir4 = "/flash/"
                    case "5":
                        SFTPSwlogDir5 = "/flash/"
                    case "6":
                        SFTPSwlogDir6 = "/flash/"
                    case "7":
                        SFTPSwlogDir7 = "/flash/"
                    case "8":
                        SFTPSwlogDir8 = "/flash/"
            #Select chassis
            validSelection = False
            print("This switch has logs for chassis: "+str(sorted(hasChassis,key=str.lower)))
            while validSelection == False:
                chassis_selection = input("Which chassis would you like the logs for? [all] ") or "all"
                if chassis_selection == "all":
                    print("Grabbing logs for all chassis")
                    validSelection = True
                    continue
                if chassis_selection in hasChassis:
                    print("Grabbing logs for Chassis "+str(chassis_selection))
                    validSelection = True
                    continue
                else:
                    print("Invalid selection. The validation options are: "+str(sorted(hasChassis,key=str.lower))+" or 'all'")
            #Make Directory to save logs
            ##Get current time, trim it down to yyyymmddhhmmss
            currenttimeraw = str(datetime.datetime.now())
            parts = currenttimeraw.split(".")
            currenttimeraw = parts[0]
            currenttimeraw = currenttimeraw.replace(":","")
            currenttimeraw = currenttimeraw.replace("-","")
            currenttime = currenttimeraw.replace(" ","-")
            try:
                os.mkdir('./'+ip+"-"+currenttime+"-Logs-tsbuddy")
                print("Made directory at "+'./'+ip+"-"+currenttime+"-Logs-tsbuddy")
            except FileExistsError:
                print("Directory already exists at "+'./'+ip+"-"+currenttime+"-Logs-tsbuddy")
            ##Grab logs for selected chassis
            if (chassis_selection == "1" or chassis_selection == "all") and SFTPSwlogDir1 != "":
                SwlogDir1 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis1"
                os.mkdir(SwlogDir1)
                for file in sftp.listdir(SFTPSwlogDir1):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis1*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir1+file, SwlogDir1+"/"+file)
            if (chassis_selection == "1B" or chassis_selection == "all") and SFTPSwlogDir1B != "":
                SwlogDir1B = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis1B"
                os.mkdir(SwlogDir1B)
                for file in sftp.listdir(SFTPSwlogDir1B):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis1_CMMB*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir1B+file, SwlogDir1B+"/"+file)
            if (chassis_selection == "2" or chassis_selection == "all") and SFTPSwlogDir2 != "":
                SwlogDir2 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis2"
                os.mkdir(SwlogDir2)
                for file in sftp.listdir(SFTPSwlogDir2):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis2*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir2+file, SwlogDir2+"/"+file)
            if (chassis_selection == "2B" or chassis_selection == "all") and SFTPSwlogDir2B != "":
                SwlogDir2B = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis2B"
                os.mkdir(SwlogDir2B)
                for file in sftp.listdir(SFTPSwlogDir2B):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis2_CMMB*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir2B+file, SwlogDir2B+"/"+file)
            if (chassis_selection == "3" or chassis_selection == "all") and SFTPSwlogDir3 != "":
                SwlogDir3 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis3"
                os.mkdir(SwlogDir3)
                for file in sftp.listdir(SFTPSwlogDir3):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis3*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir3+file, SwlogDir3+"/"+file)
            if (chassis_selection == "4" or chassis_selection == "all") and SFTPSwlogDir4 != "":
                SwlogDir4 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis4"
                os.mkdir(SwlogDir4)
                for file in sftp.listdir(SFTPSwlogDir4):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis4*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir4+file, SwlogDir4+"/"+file)
            if (chassis_selection == "5" or chassis_selection == "all") and SFTPSwlogDir5 != "":
                SwlogDir5 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis5"
                os.mkdir(SwlogDir5)
                for file in sftp.listdir(SFTPSwlogDir5):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis5*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir5+file, SwlogDir5+"/"+file)
            if (chassis_selection == "6" or chassis_selection == "all") and SFTPSwlogDir6 != "":
                SwlogDir6 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis6"
                os.mkdir(SwlogDir6)
                for file in sftp.listdir(SFTPSwlogDir6):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis6*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir6+file, SwlogDir6+"/"+file)
            if (chassis_selection == "7" or chassis_selection == "all") and SFTPSwlogDir7 != "":
                SwlogDir7 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis7"
                os.mkdir(SwlogDir7)
                for file in sftp.listdir(SFTPSwlogDir7):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis7*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir7+file, SwlogDir7+"/"+file)
            if (chassis_selection == "8" or chassis_selection == "all") and SFTPSwlogDir8 != "":
                SwlogDir8 = './'+ip+"-"+currenttime+"-Logs-tsbuddy/Chassis8"
                os.mkdir(SwlogDir8)
                for file in sftp.listdir(SFTPSwlogDir8):
                    if fnmatch.fnmatch(file, "swlog_archive"):
                        #print("Skipping swlog_archive, at least as a file")
                        continue
                    if fnmatch.fnmatch(file, "*swlog_chassis8*"):
                        #print("Downloading "+file)
                        sftp.get(SFTPSwlogDir8+file, SwlogDir8+"/"+file)

            #print("Logdir = "+str(logdir))
            ###Load non-archive logs
            selection = first_load(conn,cursor,chassis_selection)
            if selection == "y":
                print("Gathering logs from swlog_archive")
                if (chassis_selection == "1" or chassis_selection == "all") and SFTPSwlogDir1 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir1+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir1)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir1)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir1)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 1")
                if (chassis_selection == "1B" or chassis_selection == "all") and SFTPSwlogDir1B != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir1B+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir1B)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir1B)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir1B)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 1B")
                if (chassis_selection == "2" or chassis_selection == "all") and SFTPSwlogDir2 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir2+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir2)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir2)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir2)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 2")
                if (chassis_selection == "2B" or chassis_selection == "all") and SFTPSwlogDir2B != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir2B+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir2B)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir2B)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir2B)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 2B")
                if (chassis_selection == "3" or chassis_selection == "all") and SFTPSwlogDir3 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir3+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir3)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir3)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir3)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 3")
                if (chassis_selection == "4" or chassis_selection == "all") and SFTPSwlogDir4 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir4+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir4)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir4)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir4)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 4")
                if (chassis_selection == "5" or chassis_selection == "all") and SFTPSwlogDir5 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir5+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir5)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir5)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir5)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 5")
                if (chassis_selection == "6" or chassis_selection == "all") and SFTPSwlogDir6 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir6+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir6)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir6)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir6)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 6")
                if (chassis_selection == "7" or chassis_selection == "all") and SFTPSwlogDir7 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir7+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir7)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir7)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir7)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 7")
                if (chassis_selection == "8" or chassis_selection == "all") and SFTPSwlogDir8 != "":
                    tarfilename = ""
                    #There are two swlogvc.tar files, but they're identical. We only want one.
                    tarcount = 0
                    for file in sftp.listdir(SFTPSwlogDir8+'/swlog_archive'):
                        #print(file)
                        #swlog.time errors out, so we skip it
                        if fnmatch.fnmatch(file, "swlog.time"):
                            continue
                        if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                            #print("Matched, downloading "+str(file))
                            sftp.get("/flash/swlog_archive/"+file, file)
                            tarcount += 1
                            tarfilename = file
                    if tarcount == 0:
                        print("There are no log files in the swlog_archive")
                        analysis_menu(conn,cursor)
                        return
                    with tarfile.open(tarfilename, "r") as tar:
                        ArchiveLogByLine = []
                        tar.extractall(str(SwlogDir8)+'/swlog_archive')
                        tardir = os.listdir(str(SwlogDir8)+'/swlog_archive')
                        for file in tardir:
                            #print(file)
                            with gzip.open(str(SwlogDir8)+'/swlog_archive/'+file, "rt") as log:
                                #print(log)
                                ArchiveLogByLine = log.readlines()
                                Filename = file
                                ReadandParse(ArchiveLogByLine,conn,cursor,Filename,"Chassis 8")
                    #print(len(ArchiveLogByLine))
                    #for subfile in tar:
                    #    print(subfile)
                    #    parts = str(subfile).split("'")
                    #    subfilename = parts[1]
                    #    print(subfilename)
                    #    with gzip.open(subfilename, "rt") as log:
                    #        output = log.read()
                    #        print(output)
                #archive_load(conn,cursor,ArchiveLogByLine)
            #filepath = "/flash/swlog_chassis1"
            #localpath = "swlog_chassis1"
            #sftp.get(filepath,localpath)
            if sftp: sftp.close()
            if transport: transport.close()
            analysis_menu(conn,cursor)


            """
            for file in sftp.listdir('/flash/'):
                if fnmatch.fnmatch(file, "swlog_archive"):
                    #print("Skipping swlog_archive, at least as a file")
                    continue
                if chassis_selection == "all":
                    if fnmatch.fnmatch(file, "*swlog*"):
                        #print("Downloading "+file)
                        sftp.get("/flash/"+file, file)
                        continue
                else:
                    if fnmatch.fnmatch(file, "*swlog_chassis"+CleanOutput(str(chassis_selection))+".*"):
                        #print("Downloading "+file)
                        sftp.get("/flash/"+file, file)
                        continue
                if fnmatch.fnmatch(file, "*Console*"):
                    #print("Downloading "+file)
                    sftp.get("/flash/"+file, file)
                    continue
            path = os.getcwd()
            selection = first_load(conn,cursor,path,chassis_selection)
            if selection == "y":
                tarfilename = ""
                print("Gathering logs from swlog_archive")
                #There are two swlogvc.tar files, but they're identical. We only want one.
                tarcount = 0
                for file in sftp.listdir('/flash/swlog_archive'):
                    #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.tar") and tarcount == 0:
                        #print("Matched, downloading "+str(file))
                        sftp.get("/flash/swlog_archive/"+file, file)
                        tarcount += 1
                        tarfilename = file
                if tarcount == 0:
                    print("There are no log files in the swlog_archive")
                    analysis_menu(conn,cursor)
                    return
                with tarfile.open(tarfilename, "r") as tar:
                    ArchiveLogByLine = []
                    tar.extractall('./swlog_archive')
                    tardir = os.listdir('./swlog_archive')
                    for file in tardir:
                        #print(file)
                        with gzip.open('./swlog_archive/'+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = file
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename)
                    #print(len(ArchiveLogByLine))
                    #for subfile in tar:
                    #    print(subfile)
                    #    parts = str(subfile).split("'")
                    #    subfilename = parts[1]
                    #    print(subfilename)
                    #    with gzip.open(subfilename, "rt") as log:
                    #        output = log.read()
                    #        print(output)
                #archive_load(conn,cursor,ArchiveLogByLine)
            #filepath = "/flash/swlog_chassis1"
            #localpath = "swlog_chassis1"
            #sftp.get(filepath,localpath)
            if sftp: sftp.close()
            if transport: transport.close()
            analysis_menu(conn,cursor)
            """
        except Exception as e:
            print(f"[{ip}] ERROR: {e}")
            quit()
            

def first_load(conn,cursor,chassis_selection):
    cursor.execute("create table Logs(id integer primary key autoincrement, ChassisID Text, Filename Text, Timestamp Text, SwitchName Text, Source Text, Model Text, AppID Text, Subapp Text, Priority text, LogMessage text)")
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
    if TimeDesync == True:
        print("Warning: There is a time desync present in the logs where the timestamp is much older than expected. Use 'Look for problems' and 'Locate time desyncs' to determine where")
    validSelection = False
    while validSelection == False:
        selection = input("Do you want to check for older logs in the swlog_archive? y or n? [n] ") or "n"
        if selection == "y":
            validSelection = True
            return selection
        if selection == "n":
            validSelection = True
            analysis_menu(conn,cursor)
            return selection
        else:
            print("Invalid Selection")

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
        print("There are "+count+" logs ranging from "+OldestLog+" to "+NewestLog)
        if TimeDesync == True:
            print("There is a time desync present in the logs where the timestamp is much older than expected. Use 'Look for problems' and 'Locate time desyncs' to determine where")
        print("[1] - Export to xlsx - Limit 1,000,000 rows")
        print("[2] - Search for log messages by keyword")
        print("[3] - Filter by time - WIP")
        print("[4] - Check for additional logs - Not implemented")
        print("[5] - Look for problems - WIP")
        print("[6] - Direct Query")
        print("[7] - Change switch name for saved logfiles - Currently: "+PrefSwitchName)
        print("[0] - Exit")
        selection = input("What would you like to do with the logs? [0] ") or "0"
        match selection:
            case "1":
                context = "Full"
                ExportXLSX(conn,cursor,context)
            case "2":
                SearchKeyword(conn,cursor)
            case "3":
                SearchTime(conn,cursor,NewestLog,OldestLog)
            case "5":
                LogAnalysis(conn,cursor)
            case "6":
                DirectQuery(conn,cursor)
            case "7":
                ChangeSwitchName()
            case "0":
                validSelection = True
                break
            case _:
                print("Invalid Selection")


def AnalysisInit(conn,cursor):
    print("Initializing log analysis")
    cursor.execute("create table Analysis(id integer primary key autoincrement, Source text, Category text, LogMessage text, LogMeaning text)")
    src_dir = os.path.dirname(os.path.abspath(__file__))
    with open(src_dir+"/loglist-master.csv", "rt") as DefFile:
        LogDefinitions = DefFile.readlines()
        for log in LogDefinitions:
            log = log.strip()
            parts = log.split(',')
            Source = parts[0]
            Category = parts[1]
            LogMessage = parts[2]
            LogMeaning = parts[3]
            #print("insert into Analysis(Source,Category,LogMessage,LogMeaning) values ('"+Source+"','"+Category+"','"+LogMessage+"','"+LogMeaning+"')")
            cursor.execute("insert into Analysis(Source,Category,LogMessage,LogMeaning) values ('"+Source+"','"+Category+"','"+LogMessage+"','"+LogMeaning+"')")
    #Remove the header row
    cursor.execute("delete from Analysis where id = 0")
    global AnalysisInitialized
    AnalysisInitialized = True

def CategoryInit(conn,cursor,category):
    print("Initializing log analysis for "+category)
    cursor.execute("create table "+category+"(id integer primary key autoincrement, Source text, Category text, LogMessage text, LogMeaning text)")
    cursor.execute("insert into "+category+"(Source,Category,LogMessage,LogMeaning) select Source,Category,LogMessage,LogMeaning from Analysis where Category like '%"+category+"%'")
    cursor.execute("select * from "+category)
    Output = cursor.fetchall()
    #print(Output)
    match category:
        case "Reboot":
            global RebootsInitialized
            RebootsInitialized = True
        case "VC":
            global VCInitialized
            VCInitialized = True
        case "Interface":
            global InterfaceInitialized
            InterfaceInitialized = True
        case "OSPF":
            global OSPFInitialized
            OSPFInitialized = True
        case "SPB":
            global SPBInitialized
            SPBInitialized = True
        case "Health":
            global HealthInitialized
            HealthInitialized = True
        case "Connectivity":
            global ConnectivityInitialized
            ConnectivityInitialized = True

def TimeDesyncFinder(conn,cursor):
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

#############WIP
def LogAnalysis(conn,cursor):
    if AnalysisInitialized == False:
        AnalysisInit(conn,cursor)
    ValidSelection = False
    while ValidSelection == False:
        print("[1] - Reboots")
        print("[2] - VC Issues - Not Implemented")
        print("[3] - Interface Status - Not Implemented")
        print("[4] - OSPF - Not Implemented")
        print("[5] - SPB - Not Implemented")
        print("[6] - Health - Not Implemented")
        print("[7] - Connectivity - Not Implemented")
        print("[8] - Locate time desyncs - WIP")
        print("[All] - Check for all known problem logs - Long Operation")
        print("[0] - Return to Main Menu")
        selection = input("What would you like to look for? [0]  ") or "0"
        match selection:
            case "1":
                print("Checking the logs for reboots")
                AnyReboots = False
                if RebootsInitialized == False:
                    CategoryInit(conn,cursor,"Reboot")
                cursor.execute("select Logs.ID,Logs.ChassisID,Logs.Timestamp from Logs,Reboot where (((InStr([Logs].[LogMessage],[Reboot].[LogMessage]))>0)) order by Logs.ChassisID,Logs.Timestamp")
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
                            Chassis1RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis1RebootEvent) == 1:
                        print("Chassis 1 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 1 rebooted "+str(len(Chassis1RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis1RebootEvent:
                        print(line)
                        if ("1970" or "1969") in str(line):
                            TimeDesync = True
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
                            Chassis2RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis2RebootEvent) == 1:
                        print("Chassis 2 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 2 rebooted "+str(len(Chassis2RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis2RebootEvent:
                        print(line)
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
                            Chassis3RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis3RebootEvent) == 1:
                        print("Chassis 3 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 3 rebooted "+str(len(Chassis3RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis3RebootEvent:
                        print(line)
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
                            Chassis4RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis4RebootEvent) == 1:
                        print("Chassis 4 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 4 rebooted "+str(len(Chassis4RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis4RebootEvent:
                        print(line)
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
                            Chassis5RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis5RebootEvent) == 1:
                        print("Chassis 5 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 5 rebooted "+str(len(Chassis5RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis5RebootEvent:
                        print(line)
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
                            Chassis6RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis6RebootEvent) == 1:
                        print("Chassis 6 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 6 rebooted "+str(len(Chassis6RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis6RebootEvent:
                        print(line)
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
                            Chassis7RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis7RebootEvent) == 1:
                        print("Chassis 7 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 7 rebooted "+str(len(Chassis7RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis7RebootEvent:
                        print(line)
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
                            Chassis8RebootEvent.append(Time1)
                        counter += 1
                    if len(Chassis8RebootEvent) == 1:
                        print("Chassis 8 rebooted 1 time. Here is when the reboot happened:")
                    else:
                        print("Chassis 8 rebooted "+str(len(Chassis8RebootEvent))+" times. Here is when the reboots happened:")
                    TimeDesync = False
                    for line in Chassis8RebootEvent:
                        print(line)
                        if ("1970" or "1969") in str(line):
                            TimeDesync = True
                    if TimeDesync == True:
                        print("Warning: There is a time desync present in the logs where the timestamp reads 1970 or 1969. Use 'Look for problems' and 'Locate time desyncs' to determine where")
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
                                    Output = pd.read_sql("select Logs.ChassisID,Logs.Filename,Logs.Timestamp,Logs.SwitchName,Logs.Source,Logs.Model,Logs.AppID,Logs.Subapp,Logs.Priority,Logs.LogMessage from Logs,Reboot where (((InStr([Logs].[LogMessage],[Reboot].[LogMessage]))>0)) order by Timestamp desc", conn)
                                    Output.to_excel(writer, sheet_name="ConsolidatedLogs")
                                    workbook = writer.book
                                    worksheet = writer.sheets["ConsolidatedLogs"]
                                    text_format = workbook.add_format({'num_format': '@'})
                                    worksheet.set_column("H:H", None, text_format)
                                print("Export complete. Your logs are in "+OutputFileName)
                            except:
                                print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
                        case "2":
                            cursor.execute("select Logs.ChassisID,Logs.Filename,Logs.Timestamp,Logs.SwitchName,Logs.Source,Logs.Model,Logs.AppID,Logs.Subapp,Logs.Priority,Logs.LogMessage from Logs,Reboot where (((InStr([Logs].[LogMessage],[Reboot].[LogMessage]))>0)) order by Timestamp desc")
                            Output = cursor.fetchall()
                            for line in Output:
                                print(line)
                        case "3":
                            pass
                        case "4":
                            pass
                        case "0":
                            ValidSubSelection = True
            case "2":
                if VCInitialized == False:
                    CategoryInit(conn,cursor,"VC")
            case "3":
                if InterfaceInitialized == False:
                    CategoryInit(conn,cursor,"Interface")
            case "4":
                if OSPFInitialized == False:
                    CategoryInit(conn,cursor,"OSPF")
            case "5":
                if SPBInitialized == False:
                    CategoryInit(conn,cursor,"SPB")
            case "6":
                if HealthInitialized == False:
                    CategoryInit(conn,cursor,"Health")
            case "7":
                if ConnectivityInitialized == False:
                    CategoryInit(conn,cursor,"Connectivity")
            case "8":
                TimeDesyncFinder(conn,cursor)
            case "All":
                if AnalysisInitialized == False:
                    AnalysisInit(conn,cursor)
                if PrefSwitchName != "None":
                    OutputFileName = PrefSwitchName+"-SwlogsParsed-LogAnalysis-All-tsbuddy.xlsx"
                else:
                    OutputFileName = "SwlogsParsed-LogAnalysis-All-tsbuddy.xlsx"
                try:
                    with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
                        print("Exporting data to file. This may take a moment.")
                        Output = pd.read_sql("select Logs.ChassisID,Logs.Filename,Logs.Timestamp,Logs.SwitchName,Logs.Source,Logs.Model,Logs.AppID,Logs.Subapp,Logs.Priority,Logs.LogMessage from Logs,Analysis where (((InStr([Logs].[LogMessage],[Analysis].[LogMessage]))>0)) order by Timestamp desc", conn)
                        #Output = pd.read_sql("select Logs.ChassisID,Logs.Filename,Logs.Timestamp,Logs.SwitchName,Logs.Source,Logs.Model,Logs.AppID,Logs.Subapp,Logs.Priority,Logs.LogMessage,Analysis.LogMeaning from Logs,Reboot where (((InStr([Logs].[LogMessage],[Reboot].[LogMessage]))>0)) order by Timestamp desc", conn)
                        Output.to_excel(writer, sheet_name="ConsolidatedLogs")
                        workbook = writer.book
                        worksheet = writer.sheets["ConsolidatedLogs"]
                        text_format = workbook.add_format({'num_format': '@'})
                        worksheet.set_column("H:H", None, text_format)
                    print("Export complete. Your logs are in "+OutputFileName)
                except:
                    print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
            case "0":
                ValidSelection = True
                return
            case _:
                print("Invalid Selection")

#############WIP
def SearchTime(conn,cursor,NewestLog,OldestLog):
    ValidSelection = False
    while ValidSelection == False:
        print("The logs contain the time range of "+OldestLog+" to "+NewestLog)
        print("[1] - Show all logs between a time range - Not implemented")
        print("[2] - Show all logs for a specific day")
        print("[3] - Show all logs for a specific hour - Not implemented")
        print("[4] - Show all logs for a specific minute - Not implemented")
        print("[0] - Exit")
        #newline
        print("")
        selection = input("What time range would you like to filter by? [0] ") or "0"
        match selection:
            case "1":
                pass
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
                                try:
                                    with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
                                        print("Exporting data to file. This may take a moment.")
                                        Output = pd.read_sql("Select * from Logs where TimeStamp like '%"+timerequested+"%' order by TimeStamp desc", conn)
                                        Output.to_excel(writer, sheet_name="ConsolidatedLogs")
                                        workbook = writer.book
                                        worksheet = writer.sheets["ConsolidatedLogs"]
                                        text_format = workbook.add_format({'num_format': '@'})
                                        worksheet.set_column("H:H", None, text_format)
                                    print("Export complete. Your logs are in "+OutputFileName)
                                    ValidSubselection = True
                                except:
                                    print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
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


def ChangeSwitchName():
    EnteredName = input("What name would you like to use for these logs?  ")
    global PrefSwitchName
    PrefSwitchName = CleanOutput(EnteredName)
    print("Exported files will use the name: "+PrefSwitchName+". ie: "+PrefSwitchName+"SwlogsParsed-Unfiltered-tsbuddy.xlsx")

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
            print("[4] Return to main menu")
            #####Add a "refine further"
            selection = input("What would you like to do with these logs? [1]") or "1"
            match selection:
                case "1":
                    ValidSelection = True
                    context = keyword
                    ExportXLSX(conn,cursor,context)
                    ValidSelection2 = False
                    while ValidSelection2 == False:
                        selection2 = input("Would you like to run another search? [n]") or "n"
                        match selection2:
                            case "y":
                                ValidSelection2 = True
                                SearchKeyword(conn,cursor)
                            case "n":
                                ValidSelection2 = True
                            case _:
                                print("Invalid input. Please enter 'y' or 'n'")
                case "2":
                    ValidSelection = True
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
                    ValidSelection = False
                    while ValidSelection == False:
                        print("[1] Export to XLSX - Limit 1,000,000 rows")
                        print("[2] Run another search")
                        print("[3] Return to main menu")
                        #####Add a "refine further"
                        selection = input("What would you like to do with these logs? [1]") or "1"
                        match selection:
                            case "1":
                                ValidSelection = True
                                context = keyword+"-Unique"
                                if PrefSwitchName != "None":
                                    OutputFileName = PrefSwitchName+"-SwlogsParsed-"+context+"-tsbuddy.xlsx"
                                else:
                                    OutputFileName = "SwlogsParsed-"+context+"-tsbuddy.xlsx"
                                try:
                                    with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
                                        print("Exporting data to file. This may take a moment.")
                                        Output = pd.read_sql("select ChassisID, Filename, Timestamp as FirstTimestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs where LogMessage like '%"+keyword+"%' group by LogMessage order by Timestamp,Filename desc limit 1048576", conn)
                                        Output.to_excel(writer, sheet_name="Logs with "+context)
                                        workbook = writer.book
                                        worksheet = writer.sheets["Logs with "+context]
                                        text_format = workbook.add_format({'num_format': '@'})
                                        worksheet.set_column("H:H", None, text_format)
                                    print("Export complete. Your logs are in SwlogsParsed-"+context+"-tsbuddy.xlsx")
                                except:
                                    print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
                                ValidSelection2 = False
                                while ValidSelection2 == False:
                                    selection2 = input("Would you like to run another search? [n]") or "n"
                                    match selection2:
                                        case "y":
                                            ValidSelection2 = True
                                            SearchKeyword(conn,cursor)
                                        case "n":
                                            ValidSelection2 = True
                                        case _:
                                            print("Invalid input. Please enter 'y' or 'n'")
                            case "2":
                                ValidSelection = True
                                SearchKeyword(conn,cursor)
                            case "3":
                                ValidSelection = True
                            case _:
                                print("Invalid input.")
                case "3":
                    ValidSelection = True
                    SearchKeyword(conn,cursor)
                case "4":
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

def ExportXLSX(conn,cursor,context):
    match context:
        case "Full":
            if PrefSwitchName != "None":
                OutputFileName = PrefSwitchName+"-SwlogsParsed-Unfiltered-tsbuddy.xlsx"
            else:
                OutputFileName = "SwlogsParsed-Unfiltered-tsbuddy.xlsx"
            try:
                with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
                    print("Exporting data to file. This may take a moment.")
                    Output = pd.read_sql("SELECT ChassisID, Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs order by Timestamp,Filename desc limit 1048576", conn)
                    #Output = pd.read_sql("SELECT Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs limit 1048576", conn)
                    Output.to_excel(writer, sheet_name="ConsolidatedLogs")
                    workbook = writer.book
                    worksheet = writer.sheets["ConsolidatedLogs"]
                    text_format = workbook.add_format({'num_format': '@'})
                    worksheet.set_column("H:H", None, text_format)
                print("Export complete. Your logs are in "+OutputFileName)
            except:
                print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")
        case _:
            if PrefSwitchName != "None":
                OutputFileName = PrefSwitchName+"-SwlogsParsed-"+context+"-tsbuddy.xlsx"
            else:
                OutputFileName = "SwlogsParsed-"+context+"-tsbuddy.xlsx"
            try:
                with pd.ExcelWriter(OutputFileName,engine="xlsxwriter", engine_kwargs={'options': {'strings_to_formulas': False}}) as writer:
                    print("Exporting data to file. This may take a moment.")
                    Output = pd.read_sql("select ChassisID, Filename, Timestamp, SwitchName, Source, AppID, SubApp, Priority, LogMessage from Logs where LogMessage like '%"+context+"%' order by Timestamp,Filename desc limit 1048576", conn)
                    Output.to_excel(writer, sheet_name="Logs with "+context)
                    workbook = writer.book
                    worksheet = writer.sheets["Logs with "+context]
                    text_format = workbook.add_format({'num_format': '@'})
                    worksheet.set_column("H:H", None, text_format)
                print("Export complete. Your logs are in SwlogsParsed-"+context+"-tsbuddy.xlsx")
            except:
                print("Unable to write the file. Check if a file named "+OutputFileName+" is already open")

"""
def archive_load(conn,cursor,ArchiveLogByLine):
    ArchiveLogByLine = []       
    gzipcount = 0
    for file in os.listdir(logdir+"/swlog_archive"):
        #print(file)
        #swlog.time errors out, so we skip it
        if fnmatch.fnmatch(file, "swlog.time"):
            continue
        if fnmatch.fnmatch(file, "*.gz"):
            gzipcount += 1
            with gzip.open(logdir+"/swlog_archive/"+file, "rt") as log:
                #print(log)
                ArchiveLogByLine += log.readlines()
                Filename = str(file)
                ReadandParse(ArchiveLogByLine,conn,cursor,Filename)
    if gzipcount == 0:
        print("There are no log files in the swlog_archive")
        analysis_menu(conn,cursor)
        return
    else:
        analysis_menu(conn,cursor)
    ReadandParse(ArchiveLogByLine,conn,cursor,filename)
    analysis_menu(conn,cursor)
"""

def process_logs(conn,cursor,chassis_selection):
    #dir_list = os.listdir()
    #print(str(chassis_selection))
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
    """
    match chassis_selection:
        case "1" | "all":
            for file in os.listdir(SwlogDir1):
                if ('swlog_chassis1' or 'swlog_localConsole') in file:
                    SwlogFiles1.append(file)
                    print(file)
        case "2" | "all":
            for file in os.listdir(SwlogDir2):
                if ('swlog_chassis2' or 'swlog_localConsole') in file:
                    SwlogFiles2.append(file)
        case "1" | "all":
            for file in os.listdir(SwlogDir1):
                if ('swlog_chassis1' or 'swlog_localConsole') in file:
                    SwlogFiles1.append(file)
        case "4" | "all":
            for file in os.listdir(SwlogDir4):
                if ('swlog_chassis4' or 'swlog_localConsole') in file:
                    SwlogFiles4.append(file)
        case "5" | "all":
            for file in os.listdir(SwlogDir5):
                if ('swlog_chassis5' or 'swlog_localConsole') in file:
                    SwlogFiles5.append(file)
        case "6" | "all":
            for file in os.listdir(SwlogDir6):
                if ('swlog_chassis6' or 'swlog_localConsole') in file:
                    SwlogFiles6.append(file)
        case "7" | "all":
            for file in os.listdir(SwlogDir7):
                if ('swlog_chassis7' or 'swlog_localConsole') in file:
                    SwlogFiles7.append(file)
        case "8" | "all":
            for file in os.listdir(SwlogDir8):
                if ('swlog_chassis8' or 'swlog_localConsole') in file:
                    SwlogFiles8.append(file)
    ###########
    for file in os.listdir(path):
        #print(file)
        if 'swlog_chassis1' in file and (chassis_selection == "1" or chassis_selection == "all"):
            SwlogFiles1.append(file)
        if 'swlog_chassis2' in file and (chassis_selection == "2" or chassis_selection == "all"):
            SwlogFiles2.append(file)
        if 'swlog_chassis3' in file and (chassis_selection == "3" or chassis_selection == "all"):
            SwlogFiles3.append(file)
        if 'swlog_chassis4' in file and (chassis_selection == "4" or chassis_selection == "all"):
            SwlogFiles4.append(file)
        if 'swlog_chassis5' in file and (chassis_selection == "5" or chassis_selection == "all"):
            SwlogFiles5.append(file)
        if 'swlog_chassis6' in file and (chassis_selection == "6" or chassis_selection == "all"):
            SwlogFiles6.append(file)
        if 'swlog_chassis7' in file and (chassis_selection == "7" or chassis_selection == "all"):
            SwlogFiles7.append(file)
        if 'swlog_chassis8' in file and (chassis_selection == "8" or chassis_selection == "all"):
            SwlogFiles8.append(file)
        if 'swlog_localConsole' in file:
            ConsoleFiles.append(file)
    """


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
    """
    if ConsoleFiles != []:
        #print(ConsoleFiles)
        for logfile in ConsoleFiles:
            with open(str(path)+"/"+str(logfile), 'rt', errors='ignore',encoding='utf-8') as file:
                LogByLine = file.readlines()
            Filename = str(logfile)
            ReadandParse(LogByLine,conn,cursor,Filename)
    """
    #
    

def ReadandParse(LogByLine,conn,cursor,Filename,ChassisID):
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
        #8.10.R03 removed the year in console logs. This hardcodes 2025 if we do not have a year
        if line[0].isdigit() == False:
            line = "2025 "+line
        line = line.replace("  ", " ")
        parts = line.split(" ")
        partsSize = len(parts)
        #Put all log fragments in LogMessage
        if partsSize < 6:
            line = line.replace("2025 ","")
            cursor.execute("insert into Logs (ChassisID, Filename, LogMessage) values ('"+ChassisID+"','"+Filename+"','"+line+"')")
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
        #parser for different sources
        match Source:
            case "swlogd":
                if partsSize > 6:
                    Appid = parts[6]
                    if Appid == "^^":
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
                        cursor.execute("insert into Logs (Timestamp,SwitchName,Source,LogMessage,Filename,ChassisID) values ('"+Timestamp+"','"+SwitchName+"','"+Source+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")
                        continue
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
                    #single quotes break the function
                    LogMessage = LogMessage.replace("'","")
                    LogMessage = LogMessage.encode('utf-8')
                    LogMessage = str(LogMessage)
                    LogMessage = LogMessage.replace("b'","")
                    LogMessage = LogMessage.replace("'","")
                cursor.execute("insert into Logs (Timestamp,SwitchName,Source,Appid,Subapp,Priority,LogMessage,Filename,ChassisID) values ('"+Timestamp+"','"+SwitchName+"','"+Source+"','"+Appid+"','"+Subapp+"','"+Priority+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")
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
                    cursor.execute("insert into Logs (Timestamp,SwitchName,Source,Model,LogMessage,Filename,ChassisID) values ('"+Timestamp+"','"+SwitchName+"','"+Source+"','"+Model+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")
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
                    cursor.execute("insert into Logs (Timestamp,SwitchName,Source,LogMessage,Filename,ChassisID) values ('"+Timestamp+"','"+SwitchName+"','"+Source+"','"+LogMessage+"','"+Filename+"','"+ChassisID+"')")
    
    
#Check
    #cursor.execute("select * from Logs")
    #output = cursor.fetchall()
    #print(output)

def local_logs(conn,cursor):
    global SwlogDir1,SwlogDir1B,SwlogDir2,SwlogDir2B,SwlogDir3,SwlogDir4,SwlogDir5,SwlogDir6,SwlogDir7,SwlogDir8
    techSupports = []
    techSupportTimes = []
    #Search for a TechSupport in the current directory
    for item in dir_list:
        if fnmatch.fnmatch(item, "*tech_support_complete*"):
            techSupports.append(item)
            filetime = os.path.getmtime(item)
            #Convert from epoch to datetime
            techSupportTimes.append(datetime.datetime.fromtimestamp(filetime))
    #Display options
    match len(techSupports):
        case 0:
            print("There are no files or directories containing 'tech_support_complete' in this directory")
            exit()
        case 1:
            print("There is 1 tech support file in this directory. Opening "+str(techSupports[0]))
            selectedTS = techSupports[0]
        case _:
            validSelection = False
            while validSelection == False:
                print("There are "+str(len(techSupports)+1)+" tech support files or directories:")
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
    ts2dir = ""
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
    else:
        TSDirName = str(selectedTS)
    #Enumerate mnt to check for logs
    hasChassis = []
    if os.path.isdir("./"+TSDirName+"/mnt"):
        mntchassis = []
        for item in os.listdir("./"+TSDirName+"/mnt"):
            mntchassis.append(item)
        #print (mntchassis)
        if "chassis1_CMMA" in mntchassis and "1" not in hasChassis:
            #print("Chassis 1 in mnt")
            hasChassis.append("1")
            SwlogDir1 = "./"+TSDirName+"/mnt/chassis1_CMMA/flash"
        if "chassis1_CMMB" in mntchassis and "1" not in hasChassis:
            #print("Chassis 1B in mnt")
            hasChassis.append("1B")
            SwlogDir1B = "./"+TSDirName+"/mnt/chassis1_CMMB/flash"
        if "chassis2_CMMA" in mntchassis and "2" not in hasChassis:
            #print("Chassis 2 in mnt")
            hasChassis.append("2")
            SwlogDir2 = "./"+TSDirName+"/mnt/chassis2_CMMA/flash"
        if "chassis2_CMMB" in mntchassis and "2" not in hasChassis:
            #print("Chassis 2B in mnt")
            hasChassis.append("2B")
            SwlogDir2B = "./"+TSDirName+"/mnt/chassis2_CMMB/flash"
        if "chassis3_CMMA" in mntchassis and "3" not in hasChassis:
            #print("Chassis 3 in mnt")
            hasChassis.append("3")
            SwlogDir3 = "./"+TSDirName+"/mnt/chassis3_CMMA/flash"
        if "chassis4_CMMA" in mntchassis and "4" not in hasChassis:
            #print("Chassis 4 in mnt")
            hasChassis.append("4")
            SwlogDir4 = "./"+TSDirName+"/mnt/chassis4_CMMA/flash"
        if "chassis5_CMMA" in mntchassis and "5" not in hasChassis:
            #print("Chassis 5 in mnt")
            hasChassis.append("5")
            SwlogDir5 = "./"+TSDirName+"/mnt/chassis5_CMMA/flash"
        if "chassis6_CMMA" in mntchassis and "6" not in hasChassis:
            #print("Chassis 6 in mnt")
            hasChassis.append("6")
            SwlogDir6 = "./"+TSDirName+"/mnt/chassis6_CMMA/flash"
        if "chassis7_CMMA" in mntchassis and "7" not in hasChassis:
            #print("Chassis 7 in mnt")
            hasChassis.append("7")
            SwlogDir7 = "./"+TSDirName+"/mnt/chassis7_CMMA/flash"
        if "chassis8_CMMA" in mntchassis and "8" not in hasChassis:
            #print("Chassis 8 in mnt")
            hasChassis.append("8")
            SwlogDir8 = "./"+TSDirName+"/mnt/chassis8_CMMA/flash"
    #print(hasChassis)
    #Check and extract second TS in Flash
    ts2dir = "./"+TSDirName+"/flash"
    logdir = ""
    #print("ts2dir: "+ts2dir)
    hasdir = False
    for item in os.listdir(ts2dir):
        if os.path.isdir(item):
            logdir = os.path.dirname(str(ts2dir)+"/"+item)
            hasdir = True
    if hasdir == False:
        extract_tar_files(str("./"+TSDirName))
        logdir = os.path.dirname(str(ts2dir)+"/flash/flash")
    else:
        #print("There is already a directory for the 2nd tar")
        pass
    #Check for Chassis Number
    FolderChassis = []
    for file in os.listdir(logdir):
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
    validSelection = False
    print("This switch has logs for chassis: "+str(sorted(hasChassis,key=str.lower)))
    while validSelection == False:
        chassis_selection = input("Which chassis would you like the logs for? [all] ") or "all"
        if chassis_selection == "all":
            print("Grabbing logs for all chassis")
            validSelection = True
            continue
        if chassis_selection in hasChassis:
            print("Grabbing logs for Chassis "+str(chassis_selection))
            validSelection = True
            continue
        else:
            print("Invalid selection. The validation options are: "+str(sorted(hasChassis,key=str.lower))+" or 'all'")
    #print("Logdir = "+str(logdir))
    ###Load non-archive logs
    selection = first_load(conn,cursor,chassis_selection)
    ###Check for archived logs
    if selection == "y":
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
                        with gzip.open(SwlogDir1+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
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
                        with gzip.open(SwlogDir2+"/swlog_archive/"+file, "rt") as log:
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
                        with gzip.open(SwlogDir3+"/swlog_archive/"+file, "rt") as log:
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
                        with gzip.open(SwlogDir4+"/swlog_archive/"+file, "rt") as log:
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
                        with gzip.open(SwlogDir5+"/swlog_archive/"+file, "rt") as log:
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
                        with gzip.open(SwlogDir6+"/swlog_archive/"+file, "rt") as log:
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
                        with gzip.open(SwlogDir7+"/swlog_archive/"+file, "rt") as log:
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
                        with gzip.open(SwlogDir8+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 8"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
        """
        match chassis_selection:
            case "1" | "all":
                for file in os.listdir(SwlogDir1+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir1+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 1"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
            case "2" | "all":
                for file in os.listdir(SwlogDir2+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir2+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 2"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
            case "3" | "all":
                for file in os.listdir(SwlogDir3+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir3+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 3"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
            case "4" | "all":
                for file in os.listdir(SwlogDir4+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir4+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 4"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
            case "5" | "all":
                for file in os.listdir(SwlogDir5+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir5+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 5"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
            case "6" | "all":
                for file in os.listdir(SwlogDir6+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir6+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 6"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
            case "7" | "all":
                for file in os.listdir(SwlogDir7+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir7+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 7"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
            case "8" | "all":
                for file in os.listdir(SwlogDir8+"/swlog_archive"):
                     #print(file)
                    #swlog.time errors out, so we skip it
                    if fnmatch.fnmatch(file, "swlog.time"):
                        continue
                    if fnmatch.fnmatch(file, "*.gz"):
                        gzipcount += 1
                        with gzip.open(SwlogDir8+"/swlog_archive/"+file, "rt") as log:
                            #print(log)
                            ArchiveLogByLine = log.readlines()
                            Filename = str(file)
                            ChassisID = "Chassis 8"
                            ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
        """
        if gzipcount == 0:
            print("There are no log files in the swlog_archive")
            analysis_menu(conn,cursor)
            return
        else:
            analysis_menu(conn,cursor)
            return
"""
        for file in os.listdir(logdir+"/swlog_archive"):
            #print(file)
            #swlog.time errors out, so we skip it
            if fnmatch.fnmatch(file, "swlog.time"):
                continue
            if fnmatch.fnmatch(file, "*.gz"):
                gzipcount += 1
                with gzip.open(logdir+"/swlog_archive/"+file, "rt") as log:
                    #print(log)
                    ArchiveLogByLine = log.readlines()
                    Filename = str(file)
                    ReadandParse(ArchiveLogByLine,conn,cursor,Filename,ChassisID)
        if gzipcount == 0:
            print("There are no log files in the swlog_archive")
            analysis_menu(conn,cursor)
            return
        else:
            analysis_menu(conn,cursor)
"""



def main():
    with sqlite3.connect(':memory:') as conn:
        cursor = conn.cursor()
        hosts = collect_hosts()
        if hosts != []:
            #Erase existing log files in the directory
            for file in first_dir_list:
                if 'swlog_chassis' in file:
                    os.remove(file)
                if 'swlog_localConsole' in file:
                    os.remove(file)
            grab_logs(hosts,conn,cursor)
        else:
            local_logs(conn,cursor)




            #first_load(conn,cursor)
        #If there's logs at all
        



















if __name__ == "__main__":
    main()
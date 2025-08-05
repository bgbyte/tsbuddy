import os
import paramiko
from getpass import getpass
import fnmatch
import time

first_dir_list = os.listdir()

def main():
#Testing the new stuff
	hosts = collect_hosts()
	if hosts != []:
		#Erase existing log files in the directory
		for file in first_dir_list:
			if 'tech_support_complete' in file:
				os.remove(file)
		grab_tech_support(hosts)
		print("Grab logs finished")
		#Grab new dir_list
	
def collect_hosts():
	"""Collects device details from the user and returns a list of hosts."""
	hosts = []
	print("\nEnter device details for the switch you want the logs from. Press Enter without an IP to use logs in current directory")
	ip = input("Enter device IP: ").strip()
	if not ip:
		return hosts
	username = input(f"Enter username for {ip} [admin]: ") or "admin"
	password = getpass(f"Enter password for {ip} [switch]: ") or "switch"
	hosts.append({"ip": ip, "username": username, "password": password})
	#print(hosts)
	return hosts

def grab_tech_support(hosts):
	paramiko.util.log_to_file("paramiko.log")
	#SSH portion
	for host in hosts:
		ip = host["ip"]
		username = host["username"]
		password = host["password"]
		print("Connecting to "+str(ip)+" via SSH to run the tech support command")
		try:
			client = paramiko.SSHClient()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect(ip, 22, username, password, timeout=10)
			shell = client.invoke_shell()
			shell.send("show tech-support eng complete\n")
			time.sleep(1)
			shell.recv(1024)
			print("Command sent to switch")
		except Exception as e:
			print(f"[{ip}] SSH ERROR: {e}")
			exit()

	#SFTP portion
	filesize = 0
	finished = False
	for host in hosts:
		ip = host["ip"]
		username = host["username"]
		password = host["password"]
		print("Connecting to "+str(ip)+" via SFTP to download the file.")
		try:
			transport = paramiko.Transport((ip,22))
			transport.connect(None,username,password)
			sftp = paramiko.SFTPClient.from_transport(transport)
			for file in sftp.listdir('/flash/'):
				if fnmatch.fnmatch(file, "tech_support_complete.tar"):
					while finished == False:
						file_attributes = sftp.stat('/flash/tech_support_complete.tar')
						#print(file_attributes)
							#print("Found "+file)
						#print("It is "+str(file_attributes.st_size))
						newfilesize = file_attributes.st_size
						if newfilesize == filesize:
							print("The tech support files is ready. Beginning download")
							sftp.get("/flash/"+file, file)
							finished = True
						else:
							print("File sizes are different, the file is still generating. Trying again in a few seconds. Old:"+str(filesize)+". New: "+str(newfilesize))
							filesize = newfilesize
							time.sleep(5)
							continue
			if sftp: sftp.close()
			if transport: transport.close()
		except Exception as e:
			print(f"[{ip}]SFTP ERROR: {e}")

if __name__ == "__main__":
	main()
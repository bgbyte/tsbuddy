tcpdump can be run on OmniSwitches from su, however it has several limitations.
1. tcpdump can only be run at the IP level, per IP interface.
2. The format the output file is not recognized by Wireshark


In order to run tcpdump on the switch:
1. From the su menu, run "ifconfig". Locate the name of the interface with the IP you want to capture.
2. Run tcpdump. Here is an example command: "tcpdump -i alv40002 host 10.1.2.3 -w /flash/tcpdump.pcap"
	"-i alv40002" will be the name of the interface to capture
	"host 10.1.2.3" is a filter.
	"-w /flash/tcpdump.pcap" will write the output of tcpdump to a file. In order for tcpdumpreader.py to read the file, the file must be named "tcpdump.pcap"
3. FTP to the switch and download the pcap file.
4. Run tcpdumpreader.py from the directory that contains tcpdump.pcap. 
5. It will create "tcpdump-readable.pcap". Wireshark can read this file.


Explanation:
The pcap file created by tcpdump will not be readable by Wireshark for two reasons:
1. There is a 12 byte header added at the beginning of each packet
2. The Ethertype field is missing

tcpdumpreader.py is a script that will remove that 12 byte header and add an Ethertype of IPv4.







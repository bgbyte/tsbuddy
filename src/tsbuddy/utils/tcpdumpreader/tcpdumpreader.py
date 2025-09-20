import scapy.all
#
#Need to:
#1. Convert pcap to hex
#2. Remove the first 12 bytes
#3. Add IPv4 (0x0800) after byte 12 (the dst and src MACs) or 24 characters (each hex character is 4 bits)
#4. Convert hex to pcap


#Look for and open tcpdump.pcap
try:
    orig_pcap = scapy.all.rdpcap("tcpdump.pcap")
    #Define the list that will contain all packets
    packets = []
    #Modify each packet from the tcpdump
    for packet in orig_pcap:
        #read the data as hex
        hex_string = bytes(packet).hex()
        #Convert the hex to a string so it can be modified
        line = str(hex_string)
        #Remove the first 24 characters. This is the unknown header that the switch adds
        line = line[:0] + line[24:]
        #Add 0800, or IPv4, as the Ethertype
        line = line[:24]+"0800"+line[24:]
        #Convert the string into bytes
        raw_bytes = bytes.fromhex(line)
        #Create a packet from each line
        packet = scapy.all.Ether(raw_bytes)
        #Add the completed packet to the list of packets to write
        packets.append(packet)
    #Save the modified packets as a pcap
    scapy.all.wrpcap("tcpdump-readable.pcap", packets)
except:
    print("Unable to open 'tcpdump.pcap'. Please run this program from a directory containing 'tcpdump.cap'")


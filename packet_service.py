import packet
import struct
from main import PKT_DIR_INCOMING, PKT_DIR_OUTGOING
class Packet_Service(object):

	def __init__(self):
		self.protocol_to_int = {"tcp": 6, "udp": 17}


	def packet_to_data(self, packet):
		total_pkt = ""
		total_pkt = self.craft_ip(packet)
		proto = packet.protocol
		if proto == "TCP":
			total_pkt += self.craft_tcp(packet)
		elif proto == "UDP":
			total_pkt +=  self.craft_udp(packet)
			if packet.is_DNS == False:
				print "BAD RECONTSTRUCT"
			total_pkt += self.craft_dns(packet)
		return total_pkt

	def data_to_packet(self, pkt, pkt_dir):
		packet = Packet()
        header_len = self.ip_header_length(pkt)
        if header_len < 5:
            return None
        proto_dec = self.get_protocol(pkt)
        packet.set_protocol(proto_dec)
        src = dst = None
        try:
            src = self.get_src(pkt)
            dst = self.get_dst(pkt)
        except:
            return
        if src == None or dst == None:
            return None
        packet.src_ip = src
        packet.dest_ip = dst

        start_trans_header = header_len * 4
        
        if packet.protocol == "tcp":
            try:
                packet.src_port = int(self.get_src_port_std(pkt, start_trans_header))
                packet.dst_port = int(self.get_dst_port_std(pkt, start_trans_header))
            except:
                return None

        elif packet.protocol == "udp":
            try:
                packet.src_port = int(self.get_src_port_std(pkt, start_trans_header))
                packet.dst_port = int(self.get_dst_port_std(pkt, start_trans_header))
            except:
                return None
            if pkt_dir == PKT_DIR_OUTGOING and packet.dst_port == 53:
                try:
                    result = self.parse_dns(pkt, start_trans_header + 8)
                    if result != None:
                        packet.dns_query = result
                        packet.is_DNS = True
                except:
                    return None
        elif packet.protocol == "icmp":
            try:
                packet.icmp_type = self.get_icmp_type(pkt, start_trans_header)
            except:
                return
        else:
            return None

        return packet


#MARK PARSING
    #returns a big endian version of pkt
    def ip_header_length(self, pkt):
        byte0 = pkt[0]
        unpacked_byte = struct.unpack("!B", byte0)[0]
        header_len = unpacked_byte & 0x0F
        return header_len

    def ttl(self, pkt):
    	ttl_byte = pkt[8]
    	unpacked_byte = struct.unpack("!B", ttl_byte)[0]
    	return unpacked_byte

    def ack_number(self, pkt):
    	ack_byte = pkt[8:12]
    	unpacked_byte = struct.unpack("!L", ack_byte)[0]
    	return unpacked_byte

    def seq_number(self, pkt):
    	seq_byte = pkt[4:8]
    	unpacked_byte = struct.unpack("!L", seq_byte)[0]
    	return seq_byte

    def version(self, pkt):
        byte0 = pkt[0]
        unpacked_byte = struct.unpack("!B", byte0)[0]
        version = unpacked_byte & 0xF0
        return version

    def total_length(self, pkt):
        total_byte = pkt[2:4]
        unpacked_byte = struct.unpack("!H", total_byte)[0]
        return unpacked_byte

    def udp_length(self, pkt, offset):
        length_byte = pkt[(offset + 4): (offset + 6)]
        unpacked_byte = struct.unpack("!H", length_byte)[0]
        return unpacked_byte

    def get_src_port_std(self, pkt, offset):
        dst_bytes = pkt[offset: offset + 2]
        unpacked_byte = struct.unpack("!H", dst_bytes)[0]
        return unpacked_byte

    def get_dst_port_std(self, pkt, offset):
        dst_bytes = pkt[offset + 2: offset + 4]
        unpacked_byte = struct.unpack("!H", dst_bytes)[0]
        return unpacked_byte

    #get icmp type -- firsty byte of icmp header
    def get_icmp_type(self, pkt, offset):
        type_byte = pkt[offset]
        unpacked_byte = struct.unpack("!B", type_byte)[0]
        icmp_type = unpacked_byte
        return icmp_type

    #return the decimal protocol from pkt
    def get_protocol(self, pkt):
        proto_byte = pkt[9]
        unpacked_byte = struct.unpack("!B", proto_byte)[0]
        return unpacked_byte

    def get_src(self, pkt):
        address_byte = pkt[12:16]
        unpacked_byte = struct.unpack("!I", address_byte)[0]
        return unpacked_byte

    def get_dst(self, pkt):
        address_byte = pkt[16:20]
        unpacked_byte = struct.unpack("!I", address_byte)[0]
        return unpacked_byte

    def parse_dns(self, pkt, offset):
        dns_header = pkt[offset:offset+12]
        qd_count_byte = dns_header[4:6]
        qd_count = struct.unpack("!H", qd_count_byte)[0]
        if qd_count != 1:
            return None
        offset = offset + 12

        question = pkt[offset:]
        qname_end = 0
        byte_val = struct.unpack("!B", question[qname_end])[0]
        q_name = []
        while byte_val != 0x00:
            length = byte_val
            string = ""
            qname_end += 1
            while length > 0:
                char_byte = struct.unpack("!B", question[qname_end])[0]
                string += chr(char_byte)
                length -= 1
                qname_end += 1

            q_name.append(string)
            byte_val = struct.unpack("!B", question[qname_end])[0]

        q_type_byte = question[qname_end + 1 : qname_end + 3]
        q_class_byte = question[qname_end + 3: qname_end + 5]

        q_type = struct.unpack("!H", q_type_byte)[0]
        q_class = struct.unpack("!H", q_class_byte)[0]

        if q_type != 28 and q_type != 1:
            return None

        if q_class != 1:
            return None

        return q_name

#MARK CONSTRUCTING
	def craft_tcp(self, packet):
		source = packet.dst_port
		dest = packet.src_port
		sequence_num = 0
		ack = self.seq_num + 1
		res_off = 5
		flag = 20
		window = 1
		urgent_pointer = 0
		check_sum = 0
		tcp_header = struct.pack("!HHLLBBHHH", source, dest, seq, ack, res_off, flag, window, check_sum, urgent_pointer)
		check_sum = self.checksum_calc(tcp_header)
		tcp_header = struct.pack("!HHLLBBHHH", source, dest, seq, ack, res_off, flag, window, check_sum, urgent_pointer)
		return tcp_header

	def checksum_calc(packet_string, num_bytes):
		index = 0;
		sum = 0;
		for i in range(0,num_bytes/2):
			index = i*2
			header_bytes = struct.unpack("!H", packet_string[index:index+2])[0]
			sum = short_carry_add(sum,header_bytes)
		return ~sum & 0xffff

	def short_carry_add(a,b):
		sum = a + b
		return (sum & 0xffff) + (sum >> 16)

	def short_carry_add(self,a,b):
		sum = a + b
		return (sum & ffff) + (sum >> 16)


	def get_ip_id(self, pkt):
		id_bytes = pkt[4:6]
		unpacked = struct.unpack("!H",id_byte)[0]
		return unpacked

	def cracft_ip(self, packet):
		version = 4
		header_len = 5 << 4
		first_byte = version | header_len
		tos = 0
		total_length = 40
		identification = self.identification
		fragment_offset = 1 << 1
		ttl = 64
		protocol = self.protocol_to_int[packet.protocol]
		header_checksum = 0
		source_address = packet.dst_ip
		destination_address = packet.src_ip

		ip_header = struct.pack("!BBHHHBBHLL", first_byte, tos, total_length, identification, fragment_offset, ttl, protocol, header_checksum, source_address, destination_address)

		header_checksum = self.checksum_calc(ip_header)

		ip_header = struct.pack("!BBHHHBBHLL", first_byte, tos, total_length, identification, fragment_offset, ttl, protocol, header_checksum, source_address, destination_address)
		return ip_header

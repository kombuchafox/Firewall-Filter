#!/usr/bin/env python        
import socket, struct
from main import PKT_DIR_INCOMING, PKT_DIR_OUTGOING

# TODO: Feel free to import any Python standard moduless as necessary.
# (http://docs.python.org/2/library/)
# You must NOT use any 3rd-party libraries, though.

def ip2int(ip):
    try:
        packedIP = socket.inet_aton(ip)
        return struct.unpack("!I", packedIP)[0]
    except Exception, e:
        return None
class Firewall:
    def __init__(self, config, iface_int, iface_ext):
        self.iface_int = iface_int
        self.iface_ext = iface_ext

        with open("geoipdb.txt") as file:
            geoipdb_content = file.read()
        with open(config['rule']) as file:
            rule_content = file.read()
        fw_rules = FireWall_Rules(rule_content,geoipdb_content)

        self.fw_rules = fw_rules

    # @pkt_dir: either PKT_DIR_INCOMING or PKT_DIR_OUTGOING
    # @pkt: the actual data of the IPv4 packet (including IP header)
    def handle_packet(self, pkt_dir, pkt):
        # TODO: Your main firewall code will be here.
        packet = Packet()
        header_len = self.ip_header_length(pkt)
        if header_len < 5:
            return
        proto_dec = self.get_protocol(pkt)
        packet.set_protocol(proto_dec)
        src = dst = None
        try:
            src = self.get_src(pkt)
            dst = self.get_dst(pkt)
        except:
            return
        if src == None or dst == None:
            return
        packet.src_ip = src
        packet.dest_ip = dst

        start_trans_header = header_len * 4
        
        if packet.protocol == "tcp":
            try:
                packet.src_port = int(self.get_src_port_std(pkt, start_trans_header))
                packet.dst_port = int(self.get_dst_port_std(pkt, start_trans_header))
            except:
                return

        elif packet.protocol == "udp":
            try:
                packet.src_port = int(self.get_src_port_std(pkt, start_trans_header))
                packet.dst_port = int(self.get_dst_port_std(pkt, start_trans_header))
            ## UDP and the destination port is going to be 53
            except:
                return
            if pkt_dir == PKT_DIR_OUTGOING and packet.dst_port == 53:
                try:
                    result = self.parse_dns(pkt, start_trans_header + 8)
                    if result != None:
                        packet.dns_query = result
                        packet.is_DNS = True
                except Exception, e:
                    return

        elif packet.protocol == "icmp":
            try:
                packet.icmp_type = self.get_icmp_type(pkt, start_trans_header)
            except:
                return
        else:
            self.send_pkt(pkt_dir, pkt)
            return
        verdict = self.fw_rules.check_rules(packet, pkt_dir)
        if verdict == "pass":
            self.send_pkt(pkt_dir, pkt)


        return

    #sends packet to respected location
    def send_pkt(self, pkt_dir, pkt):
        if pkt_dir == PKT_DIR_INCOMING:
            self.iface_int.send_ip_packet(pkt)
        elif pkt_dir == PKT_DIR_OUTGOING:
            self.iface_ext.send_ip_packet(pkt)

    #returns a big endian version of pkt
    def ip_header_length(self, pkt):
        byte0 = pkt[0]
        unpacked_byte = struct.unpack("!B", byte0)[0]
        header_len = unpacked_byte & 0x0F
        return header_len

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

    #return int
    def ip2int(self, ip):
        packedIP = socket.inet_aton(ip)
        return struct.unpack("!I", packedIP)[0]

    def bst_geo_array(self, int_ip, min_index, max_index):

        if min_index == (max_index - 1):
            return self.geo_array[min_index]
        total = min_index + max_index
        mid = 0
        if total % 2 != 0:
            mid = total / 2 + 1
        else:
            mid = total / 2

        g_node = self.geo_array[mid]
        if g_node.min_ip > int_ip:
            # go down
            return self.bst_geo_array(int_ip, min_index, mid)
        else:
            return self.bst_geo_array(int_ip, mid, max_index)
            #go up

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


        

##main function will be "check_rules"
##will be initialized when the firewall is    
## will also store the geoipdb info
class FireWall_Rules(object):

    def __init__(self, rules_str, geoipdb_str):

        self.rule_dictionary = self.ingest_rules(rules_str)
        for key, rules in self.rule_dictionary.iteritems():
            for rule in rules:
                rule.parent = self
 
        self.geo_array = []

        for line in geoipdb_str.split("\n"):
            elements = line.split(" ")
            if (len(elements) == 3):
                g_node = self.GeoIPNode(elements[2], ip2int(elements[0]), ip2int(elements[1]))
                self.geo_array.append(g_node)

    #@pkt Packet class object
    #@dir either PKT_DIR_INCOMING, PKT_DIR_OUTGOING
    #@return True or False
    def check_rules(self, pkt, dir):
        #depending on packet type
        #
        ext_port = None
        ext_ip = None
        verdict = "pass"
        if dir == PKT_DIR_OUTGOING:
            ext_port = pkt.dst_port
            ext_ip = pkt.dest_ip
        else: 
            ext_port = pkt.src_port
            ext_ip = pkt.src_ip

        if pkt.protocol == "icmp":
            ext_port = pkt.icmp_type
        if pkt.protocol not in self.rule_dictionary:
            return "pass"
        rule_list = self.rule_dictionary[pkt.protocol]
        print "rule list: ", rule_list
        for rule in rule_list:
            condition1 = False
            condition2 = False
            print 
            if rule.protocol != "dns":
                if rule.check_port(ext_port):
                    condition1 = True
                if rule.check_ip(ext_ip):
                    condition2 = True
                if condition1 and condition2:
                    verdict = rule.verdict
                # print "verdict:", verdict
                # print "current ext port:", ext_port
                # print "port Rule: ", rule.port_rule
                # print "port option: ", rule.ext_port_case
            else: #rule is a DNS_rule
                print "is dns? ", pkt.is_DNS
                print "dns_query: ", pkt.dns_query
                print "rule DNS_query: ", rule.dns_query
                if pkt.is_DNS and rule.check_dns_query(pkt.dns_query):
                    verdict = rule.verdict
                    print "hit here!"
                print "verdict: ", verdict

        return verdict



    # TODO: Also do some initialization if needed.
    #function to initialize the rules dictionary
    #input: the whole str contents of rules.conf
    #output, dictionary of proper form
        # i.e. {dns: [[verdict, domain],
        #             [vertict, domain]],
        #         tcp: [[verdict, ip1, ip2]]
        #         }
    def ingest_rules(self,rules_str):
        ret_dict = dict()

        for line in rules_str.split("\n"):
            if line == '' or line[0] == "%":
                continue
            elements = line.split(" ")
            protocol = elements[1].lower()
            rule = None
            if protocol == "dns":
                protocol = "udp"
                #do dns things
                rule = self.DNS_Rule()
                rule.verdict = elements[0].lower()
                rule.dns_query = elements[2].split(".")
            else:
                rule = self.Rule(protocol)
                rule.set_verdict(elements[0].lower())
                rule.set_ip_rule(elements[2])
                rule.set_port_rule(elements[3])
            if protocol not in ret_dict:
                ret_dict[protocol] = []
          
            ret_dict[protocol].append(rule)

        return ret_dict
    class DNS_Rule(object):
        def __init__(self):
            self.verdict = None
            self.dns_query = None
            self.protocol = "dns"
            #self.dns_query = ["*", "google", "com"] -> ["com", "google", "www"]
            #pkt_dns = ["www", "google", "com"] -> ["com", "google"]
        def check_dns_query(self, pkt_dns):
            rev_pkt_dns = pkt_dns[::-1]
            dns_query = self.dns_query[::-1]
            index = 0
            for el in rev_pkt_dns:
                if index < len(dns_query) and el == dns_query[index]:
                    index += 1
                    continue
                elif index < len(dns_query) and dns_query[index] == "*":
                    break
                else:
                    return False
            return True

    class Rule(object):
        def __init__(self, protocol):
            self.parent = None
            self.verdict = None
            self.protocol = protocol
            self.ext_port_case = None
            self.ext_ip_case = None
            self.port_rule = None
            self.ip_rule = None
            
        def set_verdict(self, verd):
            self.verdict = verd

        def set_port_rule(self,ext_port_str):
            if ext_port_str.lower() == "any":
                    self.ext_port_case = 0
            elif "-" in ext_port_str:
                self.port_rule = [int(i) for i in ext_port_str.split("-")]
                self.ext_port_case = 2
            else:
                self.port_rule = int(ext_port_str)
                self.ext_port_case = 1

        def set_ip_rule(self,ext_ip_str):
            if ext_ip_str.lower() == "any":
                self.ext_ip_case = 0
            elif "/" in ext_ip_str:
                self.ext_ip_case = 3
                elements = ext_ip_str.split("/")
                #turns "1.1.1.0/28" into [16843008,28]
                self.ip_rule = [ip2int(elements[0]),int(elements[1])]
            elif "." in ext_ip_str:
                self.ext_ip_case = 2
                self.ip_rule = ip2int(ext_ip_str)
            else:
                self.ip_rule = ext_ip_str
                self.ext_ip_case = 1


        def check_port(self, pkt_port):
            #could be any
            if self.ext_port_case == 0:
                return True
            elif self.ext_port_case == 1:
                return (pkt_port == self.port_rule)
            else:
                return ((pkt_port >= self.port_rule[0]) and (pkt_port <= self.port_rule[1]))

        #@should be receiving pkt_ip as integer
        def check_ip(self, pkt_ip):

            if self.ext_ip_case == 0:
                return True
            elif self.ext_ip_case == 1:
                response = self.parent.get_country(pkt_ip)
                if response == None:
                   return False
                return self.ip_rule.lower() == response.lower()
            elif self.ext_ip_case == 2:
                return self.ip_rule == pkt_ip
            else:
                ## figure out difference between 32 and second
                difference = 32 - self.ip_rule[1]
                ## bit shift both right that many
                return ((pkt_ip >> difference) == (self.ip_rule[0] >> difference))

    '''
    A GeoIPNode is an object holding the a two character string @param country.
    @param min -- an int corresponding to the smaller ip
    @param max -- an int corresponding to the larger ip
    '''
    class GeoIPNode(object):
        def __init__(self, country, min, max):
            self.min_ip = min
            self.max_ip = max
            self.country = country

        def in_range(self, ip_int):
            if ip_int < self.min_ip or ip_int > self.max_ip:
                return False
            return True



    def get_country(self, ip):
        result = self.bst_geo_array(ip,0,len(self.geo_array))
        if result.in_range(ip):
            return result.country
        else:
            return None

    def bst_geo_array(self, int_ip, min_index, max_index):
        if self.geo_array == []:
            return None
        if min_index == (max_index - 1):
            return self.geo_array[min_index]
        total = min_index + max_index
        mid = 0
        if total % 2 != 0:
            mid = total / 2 + 1
        else:
            mid = total / 2

        g_node = self.geo_array[mid]
        if g_node.min_ip > int_ip:
            # go down
            return self.bst_geo_array(int_ip, min_index, mid)
        else:
            return self.bst_geo_array(int_ip, mid, max_index)



class Packet(object):
    def __init__(self):
        self.src_ip = None
        self.dest_ip = None
        self.src_port = None
        self.dst_port = None
        self.dir = None
        self.is_DNS = False
        self.protocol = "unknown"
        self.icmp_type = None
        self.dns_query = None

    def set_protocol(self,decimal_value):
        if decimal_value == 17:
            self.protocol = "udp"
        elif decimal_value == 1:
            self.protocol = "icmp"
        elif decimal_value == 6:
            self.protocol = "tcp"

    def set_src_port(self, decimal_value):
        self.src_port = decimal_value

    def set_dst_port(self, decimal_value):
        self.dst_port = decimal_value

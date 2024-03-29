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
    def __init__(self, config = None, iface_int = None, iface_ext = None):
        self.iface_int = iface_int
        self.iface_ext = iface_ext

        with open("geoipdb.txt") as file:
            geoipdb_content = file.read()
        with open("rules.conf") as file:
            rule_content = file.read()

        fw_rules = FireWall_Rules(rule_content,geoipdb_content)
        self.fw_rules = fw_rules
        # TODO: Load the firewall rules (from rule_filename) here.
        # print 'I am supposed to load rules from %s, but I am feeling lazy.' % \
        #         config['rule']


        # TODO: Load the GeoIP DB ('geoipdb.txt') as well
        direction = PKT_DIR_INCOMING
        # testing TCP
        packet_test1 = Packet()
        packet_test1.protocol = "tcp"
        packet_test1.src_port = 1234
        packet_test1.src_ip = ip2int("1.0.0.15")
        verdict = fw_rules.check_rules(packet_test1, direction)
        print "packet1", verdict

        # #testing ICMP
        packet_test2 = Packet()
        packet_test2.protocol = "icmp"
        packet_test2.type = 9
        packet_test2.src_ip = 1234
        verdict = fw_rules.check_rules(packet_test2, direction)
        print "packet2 should pass ==", verdict

        #testing UDP
        packet_test4 = Packet()
        packet_test4.protocol = "udp"
        packet_test4.src_port = 53
        packet_test4.dns_query = ["www", "stanford", "edu"]
        packet_test4.src_ip = ip2int("8.8.8.8")
        verdict = fw_rules.check_rules(packet_test4, direction)
        print "packet4", verdict


        # #testing DNS
        # packet_test3 = Packet()
        # packet_test3.protocol = "udp"
        # packet_test3.dst_port = 53
        # packet_test3.src_ip = 1234
        # packet_test3.is_DNS = True
        # packet_test3.dns_query = ["www", "google", "com"]
        # verdict = fw_rules.check_rules(packet_test3, direction)
        # print "packet3", verdict

        # #test port range

        # packet_test1 = Packet()
        # packet_test1.protocol = "tcp"
        # packet_test1.src_port = 3000
        # packet_test1.src_ip = 1234
        # verdict = fw_rules.check_rules(packet_test1, direction)
        # if "pass" == verdict:
        #     print "passed range test"
        # else:
        #     print "failed range test"

        # packet_test1 = Packet()
        # packet_test1.protocol = "tcp"
        # packet_test1.src_port = 4000
        # packet_test1.src_ip = 1234
        # verdict = fw_rules.check_rules(packet_test1, direction)
        # if "pass" == verdict:
        #     print "passed range test"
        # else:
        #     print "failed range test"

        # packet_test1 = Packet()
        # packet_test1.protocol = "tcp"
        # packet_test1.src_port = 3500
        # packet_test1.src_ip = 1234
        # verdict = fw_rules.check_rules(packet_test1, direction)
        # if "pass" == verdict:
        #     print "passed range test"
        # else:
        #     print "failed range test"

        # packet_test1 = Packet()
        # packet_test1.protocol = "tcp"
        # packet_test1.src_port = 4001
        # packet_test1.src_ip = 1234
        # verdict = fw_rules.check_rules(packet_test1, direction)
        # if "drop" == verdict:
        #     print "passed range test"
        # else:
        #     print "failed range test"

        # #test ip option 4 1.1.1.1/15
        # packet_test1 = Packet()
        # packet_test1.protocol = "udp"
        # packet_test1.src_port = 53
        # packet_test1.src_ip = ip2int("9.2.2.15")
        # verdict = fw_rules.check_rules(packet_test1, direction)
        # if "pass" == verdict:
        #     print "passed ip prefix test"
        # else:
        #     print "failed ip prefix test"


        # packet_test3 = Packet()
        # packet_test3.protocol = "udp"
        # packet_test3.dst_port = 53
        # packet_test3.src_ip = 1
        # packet_test3.is_DNS = True
        # packet_test3.dns_query = ["www", "google", "com"]
        # verdict = fw_rules.check_rules(packet_test3, direction)
        # print "packet3", verdict




        




    # @pkt_dir: either PKT_DIR_INCOMING or PKT_DIR_OUTGOING
    # @pkt: the actual data of the IPv4 packet (including IP header)
    def handle_packet(self, pkt_dir, pkt):
        # TODO: Your main firewall code will be here.
        packet = Packet()
        #print("handling")
        header_len = self.ip_header_length(pkt)
        if header_len < 5:
            return
        proto_dec = self.get_protocol(pkt)
        packet.set_protocol(proto_dec)
        src = dst = None
        try:
            src = ip2int(self.get_src(pkt))
            dst = ip2int(self.get_dst(pkt))
        except:
            return
        if src == None or dst == None:
            return
        packet.src_ip = src
        packet.dest_ip = dst

        start_trans_header = header_len * 4

        if packet.protocol == "TCP":
            try:
                packet.src_port = int(self.get_src_port_std(pkt, start_trans_header))
                packet.dst_port = int(self.get_dst_port_std(pkt, start_trans_header))
            except:
                print "fail tcp port access"
                return

        elif packet.protocol == "UDP":
            try:
                packet.src_port = int(self.get_src_port_std(pkt, start_trans_header))
                packet.dst_port = int(self.get_dst_port_std(pkt, start_trans_header))
            ## UDP and the destination port is going to be 53
            except:
                print "fail UDP port access"
                return
            if pkt_dir == PKT_DIR_OUTGOING and packet.dst_port == 53:
                try:
                    result = self.parse_dns(pkt, start_trans_header + 8)
                    if result != None:
                        packet.dns_query = result
                        packet.is_DNS = True
                except Exception, e:
                    print "failed DNS Parse"
                    print e
        elif packet.protocol == "ICMP":
            try:
                packet.icmp_type = self.get_icmp_type(pkt, start_trans_header)
            except:
                print "failed icmp parse"
                return
        else:
            self.send_pkt(pkt_dir, pkt)
            return
        verdict = self.fw_rules.check_rules(packet, pkt_dir)
        if verdict == "pass":
            self.send_pkt(pkt_dir, pkt)

        # print "Source IP: " , packet.src_ip , ", ",
        # print "Source port: " , packet.src_port , ", ", 
        # print "Destination IP: " , packet.dest_ip , ", ",
        # print "Destination Port: " , packet.dst_port , ", ",
        # print "Length: " ,"not yet", ", ",
        # print "Protocol: " , packet.protocol , ", "
        # print "DNS" , packet.dns_query, ","
        # if packet.is_DNS:
        #     print "DNS Address: " , packet.dns_query , ", "
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

        q_type_byte = question[qname_end : qname_end + 2]
        q_class_byte = question[qname_end + 2: qname_end + 4]

        q_type = struct.unpack("!H", q_type_byte)[0]
        q_class = struct.unpack("!H", q_class_byte)[0]

        if q_type != 28 or q_type != 1:
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
                if rule.protocol == "dns":
                    print rule.verdict, rule.protocol, rule.dns_query
                else:
                    print rule.verdict, rule.protocol, rule.ip_rule, rule.port_rule 
        self.geo_array = []

        for line in geoipdb_str.split("\n"):
            elements = line.split(" ")
            if (len(elements) == 3):
                g_node = self.GeoIPNode(elements[2], ip2int(elements[0]), ip2int(elements[1]))
                self.geo_array.append(g_node)

    def test(self, ip, country):
        if self.get_country(ip2int("jkhgdfjksghd")) == country:
            print "yee"
        else:
            print "nay"
    #@pkt Packet class object
    #@dir either PKT_DIR_INCOMING, PKT_DIR_OUTGOING
    #@return True or False
    def check_rules(self, pkt, dir):
        #depending on packet type
        #
        ext_port = None
        ext_ip = None
        verdict = "drop"
        if pkt == PKT_DIR_OUTGOING:
            ext_port = pkt.dest_ip
            ext_ip = pkt.dst_port
        else: 
            ext_port = pkt.src_port
            ext_ip = pkt.src_ip

        if pkt.protocol == "icmp":
            ext_port = pkt.type
        if pkt.protocol not in self.rule_dictionary:
            return verdict
        rule_list = self.rule_dictionary[pkt.protocol]

        for rule in rule_list:
            condition1 = False
            condition2 = False
            if rule.protocol != "dns":
                if rule.check_port(ext_port):
                    condition1 = True
                if rule.check_ip(ext_ip):
                    condition2 = True
                if condition1 and condition2:
                    verdict = rule.verdict
            else: #rule is a DNS_rule
                if rule.check_dns_query(pkt.dns_query):
                    verdict = rule.verdict

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
            #could be any
           # print self.ip_rule, self.protocol , self.port_rule, self.ext_ip_case,
            if self.ext_ip_case == 0:
                return True
            elif self.ext_ip_case == 1:
                return self.ip_rule.lower() == res
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






firewall = Firewall()

firewall.fw_rules.test("203.208.24.255","PH")
firewall.fw_rules.test("203.170.28.23","HK")
firewall.fw_rules.test("203.160.48.123","MN")
firewall.fw_rules.test("194.1.215.0","SK")
firewall.fw_rules.test("1.0.0.255","AU")
firewall.fw_rules.test("223.255.255.255", "AU")
firewall.fw_rules.test("223.255.254.0","SG")
firewall.fw_rules.test("1.1.2.0", "CN")




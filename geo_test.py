#!/usr/bin/env python
        
import socket, struct
# from main import PKT_DIR_INCOMING, PKT_DIR_OUTGOING

# TODO: Feel free to import any Python standard moduless as necessary.
# (http://docs.python.org/2/library/)
# You must NOT use any 3rd-party libraries, though.

class Firewall:
    def __init__(self, config = None, iface_int = None, iface_ext = None):
        self.iface_int = iface_int
        self.iface_ext = iface_ext
        self.geo_array = []
        # TODO: Load the firewall rules (from rule_filename) here.
        # print 'I am supposed to load rules from %s, but I am feeling lazy.' % \
        #         config['rule']


        # TODO: Load the GeoIP DB ('geoipdb.txt') as well.





        with open("geoipdb.txt") as file:
            content = file.read()
            for line in content.split("\n"):
                elements = line.split(" ")
                if (len(elements) == 3):
                    g_node = GeoIPNode(elements[2], self.ip2int(elements[0]), self.ip2int(elements[1]))
                    self.geo_array.append(g_node)


        with open("rules.conf") as file:
            content = file.read()
            self.rule_dict = self.ingest_rules(content)

        print(self.rule_dict)
        # TODO: Also do some initialization if needed.

    def ingest_rules(self,rules_str):
        ret_dict = dict()

        for line in rules_str.split("\n"):
            if line == '':
                continue

            contents = []
            elements = line.split(" ")
            verdict = elements[0]
            protocol = elements[1]

            if protocol == "dns":
                #do dns things
                contents =[verdict, elements[2]]
            else:
                external_ip = elements[2]
                external_port = elements[3]
                contents =[verdict,external_ip,external_port]

            if protocol not in ret_dict:
                ret_dict[protocol] = []

            ret_dict[protocol].append(contents)

        return ret_dict

    #@protocol should be either udp,tcp,icmp,dns
    #@port should be "any", a single port(int), or a range tuple([2000-3000])
    #@ip should be "any", a single IP(1.1.1.1), a 2 string country("AU"), an IP prefix tuple(["1.1.1.0",18])
    def rule_check(self, protocol, port = None, ip = None, dns = None):
        verdict = None

        if dns != None:
            #do dns things
            pass
        else:
            country = self.get_country(ip)
            condition1 = False
            condition2 = False
            #need to go through the dictionary and check to see what the most recent match is
            for rule in self.rule_dict[protocol]:
                rule_ip = rule[1]
                if rule_ip == 'any':
                    condition1 = True
                elif type(rule_ip) is str:
                    if rule_ip == ip:
                        condition1 = True
                else:
                    condition1 = False
                rule_port = rule[2]
                if rule_port == 'any':
                    condition2 = True
                # elif :
                else:
                    condition2 = False

        return verdict



    # @pkt_dir: either PKT_DIR_INCOMING or PKT_DIR_OUTGOING
    # @pkt: the actual data of the IPv4 packet (including IP header)
    def handle_packet(self, pkt_dir, pkt):
        # TODO: Your main firewall code will be here.
        pass

    #return int
    def ip2int(self, ip):
        packedIP = socket.inet_aton(ip)
        return struct.unpack("!I", packedIP)[0]

    def get_country(self, ip):
        return self.bst_geo_array(self.ip2int(ip),0,len(self.geo_array)).country

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

    def test(self,ip,country):
        if self.bst_geo_array(self.ip2int(ip),0,len(self.geo_array)).country == country:
            print "wee!"
        else:
            print "fuuuuuu"

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



firewall = Firewall()
firewall.test("203.208.24.255","PH")
firewall.test("203.170.28.23","HK")
firewall.test("203.160.48.123","MN")
firewall.test("194.1.215.0","SK")
firewall.test("1.0.0.255","AU")
firewall.test("223.255.255.255", "AU")
firewall.test("223.255.254.0","SG")


# firewall.test("1.1.2.0", "CN")




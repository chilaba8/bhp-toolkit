import socket
import struct

PROTOCOL_MAP = {1: "ICMP", 6: "TCP", 17: "UDP"}


class IPHeader:
    def __init__(self, buff):
        header = struct.unpack("<BBHHHBBH4s4s", buff)
        self.ver = header[0] >> 4
        self.ihl = header[0] & 0xF
        self.tos = header[1]
        self.len = header[2]
        self.id = header[3]
        self.offset = header[4]
        self.ttl = header[5]
        self.protocol_num = header[6]
        self.sum = header[7]
        self.src = header[8]
        self.dst = header[9]

        self.src_address = socket.inet_ntoa(self.src)
        self.dst_address = socket.inet_ntoa(self.dst)
        self.protocol = PROTOCOL_MAP.get(self.protocol_num, str(self.protocol_num))


class ICMPHeader:
    def __init__(self, buff):
        header = struct.unpack("<BBHHH", buff)
        self.type = header[0]
        self.code = header[1]
        self.sum = header[2]
        self.id = header[3]
        self.seq = header[4]

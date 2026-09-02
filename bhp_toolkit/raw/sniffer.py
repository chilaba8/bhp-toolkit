import argparse
import os
import socket
import sys

from bhp_toolkit.raw.headers import ICMPHeader, IPHeader


def create_socket(host):
    socket_protocol = socket.IPPROTO_IP if os.name == "nt" else socket.IPPROTO_ICMP
    sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
    sniffer.bind((host, 0))
    sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    if os.name == "nt":
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
    return sniffer


def sniff(host):
    sniffer = create_socket(host)
    print(f"[*] Escuchando en {host} (Ctrl-C para salir)")
    try:
        while True:
            raw_buffer = sniffer.recvfrom(65535)[0]
            ip_header = IPHeader(raw_buffer[0:20])
            line = f"Protocolo: {ip_header.protocol} {ip_header.src_address} -> {ip_header.dst_address}"

            if ip_header.protocol == "ICMP":
                offset = ip_header.ihl * 4
                buf = raw_buffer[offset:offset + 8]
                icmp_header = ICMPHeader(buf)
                line += f"  ICMP Type: {icmp_header.type} Code: {icmp_header.code}"

            print(line)
    except KeyboardInterrupt:
        if os.name == "nt":
            sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        print("\n[!] Sniffer detenido.")
        sys.exit(0)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sniffer con socket sin procesar: decodifica cabeceras IP e ICMP de todo el trafico visible."
    )
    parser.add_argument(
        "-H", "--host", default="0.0.0.0", help="IP local en la que escuchar (por defecto todas las interfaces)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if os.name != "nt" and os.geteuid() != 0:
        print("[!] Este script necesita privilegios de root para crear sockets sin procesar.", file=sys.stderr)
        sys.exit(1)
    sniff(args.host)


if __name__ == "__main__":
    main()

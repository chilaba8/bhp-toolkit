import argparse
import ipaddress
import os
import socket
import sys
import threading
import time

from bhp_toolkit.raw.headers import ICMPHeader, IPHeader

MAGIC_MESSAGE = b"BHPTOOLKIT!"


def udp_sender(subnet, magic_message, port, delay):
    time.sleep(delay)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        for ip in ipaddress.ip_network(subnet).hosts():
            sender.sendto(magic_message, (str(ip), port))


class HostDiscoveryScanner:
    def __init__(self, host, subnet, magic_message):
        self.host = host
        self.subnet = ipaddress.ip_network(subnet)
        self.magic_message = magic_message

        socket_protocol = socket.IPPROTO_IP if os.name == "nt" else socket.IPPROTO_ICMP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
        self.socket.bind((host, 0))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        if os.name == "nt":
            self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

    def sniff(self, duration=None):
        hosts_up = set()
        deadline = time.monotonic() + duration if duration else None
        try:
            while True:
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    self.socket.settimeout(remaining)
                try:
                    raw_buffer = self.socket.recvfrom(65535)[0]
                except socket.timeout:
                    continue

                ip_header = IPHeader(raw_buffer[0:20])

                if ip_header.protocol != "ICMP":
                    continue

                offset = ip_header.ihl * 4
                buf = raw_buffer[offset:offset + 8]
                icmp_header = ICMPHeader(buf)

                # type 3 / code 3 = Destination Unreachable / Port Unreachable
                if icmp_header.type != 3 or icmp_header.code != 3:
                    continue
                if ipaddress.ip_address(ip_header.src_address) not in self.subnet:
                    continue
                if raw_buffer[len(raw_buffer) - len(self.magic_message):] != self.magic_message:
                    continue

                if ip_header.src_address not in hosts_up:
                    hosts_up.add(ip_header.src_address)
                    print(f"[+] Host activo: {ip_header.src_address}")
        except KeyboardInterrupt:
            pass
        finally:
            if os.name == "nt":
                self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        return hosts_up


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Escaner de descubrimiento de hosts por UDP: envia datagramas UDP a un puerto "
            "cerrado en toda la subred y escucha las respuestas ICMP 'puerto inalcanzable' "
            "para averiguar que hosts estan vivos."
        )
    )
    parser.add_argument("subnet", help="Subred a escanear en notacion CIDR (p. ej. 192.168.1.0/24)")
    parser.add_argument(
        "-H", "--host", default="0.0.0.0", help="IP local en la que escuchar las respuestas ICMP"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=54321, help="Puerto UDP (debe estar cerrado) a sondear en cada host"
    )
    parser.add_argument(
        "-d", "--delay", type=float, default=2.0,
        help="Segundos de espera antes de enviar los datagramas, para que el sniffer este listo",
    )
    parser.add_argument(
        "-T", "--duration", type=float, default=None,
        help="Detener el escaneo tras N segundos en vez de esperar a Ctrl-C",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if os.name != "nt" and os.geteuid() != 0:
        print("[!] Este script necesita privilegios de root para crear sockets sin procesar.", file=sys.stderr)
        sys.exit(1)

    scanner = HostDiscoveryScanner(args.host, args.subnet, MAGIC_MESSAGE)
    sender_thread = threading.Thread(
        target=udp_sender, args=(args.subnet, MAGIC_MESSAGE, args.port, args.delay), daemon=True
    )
    sender_thread.start()

    print(f"[*] Sondeando {args.subnet} por UDP en el puerto {args.port}...")
    hosts_up = scanner.sniff(args.duration)

    if hosts_up:
        print(f"\n[*] Resumen: hosts activos en {args.subnet}")
        for host in sorted(hosts_up, key=ipaddress.ip_address):
            print(f"    {host}")
    else:
        print("\n[!] No se detectaron hosts.")


if __name__ == "__main__":
    main()

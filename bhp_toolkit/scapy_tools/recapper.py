import argparse
import os
import re
import sys
import zlib
from collections import namedtuple

from scapy.all import TCP, rdpcap

Response = namedtuple("Response", ["header", "payload"])


class Recapper:
    def __init__(self, fname):
        pcap = rdpcap(fname)
        self.sessions = pcap.sessions()
        self.responses = list()

    def get_header(self, payload):
        try:
            header_raw = payload[: payload.index(b"\r\n\r\n") + 4]
        except ValueError:
            sys.stdout.write("-")
            sys.stdout.flush()
            return None

        header = dict(
            re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", header_raw.decode(errors="replace"))
        )
        if "Content-Type" not in header:
            return None
        return header

    def extract_content(self, response, content_name="image"):
        content, content_type = None, None

        if content_name in response.header.get("Content-Type", ""):
            content_type = response.header["Content-Type"].split("/")[1]
            content = response.payload[response.payload.index(b"\r\n\r\n") + 4 :]

            encoding = response.header.get("Content-Encoding")
            if encoding == "gzip":
                content = zlib.decompress(content, zlib.MAX_WBITS | 32)
            elif encoding == "deflate":
                content = zlib.decompress(content)

        return content, content_type

    def get_responses(self):
        for session in self.sessions:
            payload = b""
            for packet in self.sessions[session]:
                try:
                    if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                        payload += bytes(packet[TCP].payload)
                except (IndexError, AttributeError):
                    continue

            if not payload:
                continue

            header = self.get_header(payload)
            if header is None:
                continue
            self.responses.append(Response(header=header, payload=payload))


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Extrae contenido (por defecto imagenes) de las respuestas HTTP presentes en un "
            "archivo pcap, reconstruyendo las sesiones TCP capturadas."
        )
    )
    parser.add_argument("pcap", help="Archivo .pcap a analizar (p. ej. el arper.pcap de bhp-arper)")
    parser.add_argument("-o", "--outdir", default="pictures", help="Directorio de salida")
    parser.add_argument(
        "-t", "--type", default="image", help="Subcadena a buscar en el Content-Type (p. ej. image, text)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    recapper = Recapper(args.pcap)
    recapper.get_responses()

    extracted = 0
    for i, response in enumerate(recapper.responses):
        content, content_type = recapper.extract_content(response, args.type)
        if content is None:
            continue

        fname = os.path.join(args.outdir, f"ex_{i}.{content_type}")
        print(f"Writing {fname}")
        with open(fname, "wb") as f:
            f.write(content)
        extracted += 1

    print(f"\nExtracted {extracted} archivo(s)")


if __name__ == "__main__":
    main()

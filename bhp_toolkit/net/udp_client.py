import argparse
import socket
import sys


def send_and_receive(host, port, data, recv_size=4096, timeout=5.0, expect_response=True):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(timeout)
    try:
        if data:
            client.sendto(data, (host, port))
        if not expect_response:
            return b"", None
        try:
            data, addr = client.recvfrom(recv_size)
            return data, addr
        except socket.timeout:
            return b"", None
    finally:
        client.close()


def read_payload(args):
    if args.file:
        with open(args.file, "rb") as f:
            return f.read()
    if args.data is not None:
        return args.data.encode("utf-8").decode("unicode_escape").encode("latin1")
    if not sys.stdin.isatty():
        return sys.stdin.buffer.read()
    return b""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Cliente UDP generico para probar servicios o hacer fuzzing basico."
    )
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument(
        "-d", "--data", default=None, help="Datos a enviar, admite secuencias de escape (\\r\\n, \\x00, ...)"
    )
    parser.add_argument("-f", "--file", default=None, help="Ruta a un archivo con el payload en binario")
    parser.add_argument("--no-recv", action="store_true", help="No esperar respuesta del servidor")
    parser.add_argument("--no-send", action="store_true", help="No enviar datos, solo escuchar la respuesta")
    parser.add_argument("-t", "--timeout", type=float, default=5.0)
    parser.add_argument("-s", "--recv-size", type=int, default=4096)
    parser.add_argument(
        "--raw", action="store_true", help="Imprimir la respuesta con repr() en vez de decodificarla como texto"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    payload = b"" if args.no_send else read_payload(args)
    data, addr = send_and_receive(
        args.host,
        args.port,
        payload,
        recv_size=args.recv_size,
        timeout=args.timeout,
        expect_response=not args.no_recv,
    )

    if addr:
        print(f"[*] Respuesta de {addr[0]}:{addr[1]}", file=sys.stderr)
    if args.raw:
        print(repr(data))
    else:
        print(data.decode(errors="replace"))


if __name__ == "__main__":
    main()

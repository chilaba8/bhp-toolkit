import argparse
import socket
import sys


def send_and_receive(host, port, data, recv_size=4096, timeout=5.0, expect_response=True):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect((host, port))
        if data:
            client.send(data)
        if not expect_response:
            return b""

        chunks = []
        try:
            while True:
                chunk = client.recv(recv_size)
                if not chunk:
                    break
                chunks.append(chunk)
        except socket.timeout:
            pass
        return b"".join(chunks)


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
        description="Cliente TCP generico para probar servicios, enviar payloads o hacer fuzzing basico."
    )
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument(
        "-d", "--data", default=None, help="Datos a enviar, admite secuencias de escape (\\r\\n, \\x00, ...)"
    )
    parser.add_argument("-f", "--file", default=None, help="Ruta a un archivo con el payload en binario")
    parser.add_argument("--no-recv", action="store_true", help="No esperar respuesta del servidor")
    parser.add_argument(
        "--no-send", action="store_true", help="No enviar datos, solo recibir (servidores que hablan primero)"
    )
    parser.add_argument("-t", "--timeout", type=float, default=5.0)
    parser.add_argument("-s", "--recv-size", type=int, default=4096)
    parser.add_argument(
        "--raw", action="store_true", help="Imprimir la respuesta con repr() en vez de decodificarla como texto"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    payload = b"" if args.no_send else read_payload(args)
    try:
        response = send_and_receive(
            args.host,
            args.port,
            payload,
            recv_size=args.recv_size,
            timeout=args.timeout,
            expect_response=not args.no_recv,
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"[!] Error de conexion: {e}", file=sys.stderr)
        sys.exit(1)

    if args.raw:
        print(repr(response))
    else:
        print(response.decode(errors="replace"))


if __name__ == "__main__":
    main()

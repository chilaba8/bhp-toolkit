import argparse
import socket
import threading


def handle_client(client_socket, address, mode, banner, recv_size, verbose):
    with client_socket as sock:
        try:
            request = sock.recv(recv_size)
        except OSError:
            return
        if verbose:
            print(f"[*] {address[0]}:{address[1]} -> {request!r}")

        if mode == "ack":
            sock.send(b"ACK")
        elif mode == "echo":
            sock.send(request)
        elif mode == "banner":
            sock.send(banner.encode())


def serve(host, port, backlog, mode, banner, recv_size, once, verbose):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(backlog)
    print(f"[*] Escuchando en {host}:{port}")
    try:
        while True:
            client, address = server.accept()
            print(f"[*] Conexion aceptada desde {address[0]}:{address[1]}")
            if once:
                handle_client(client, address, mode, banner, recv_size, verbose)
                break
            handler = threading.Thread(
                target=handle_client,
                args=(client, address, mode, banner, recv_size, verbose),
                daemon=True,
            )
            handler.start()
    except KeyboardInterrupt:
        print("\n[!] Servidor detenido.")
    finally:
        server.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Servidor TCP multihilo generico, para probar clientes o payloads propios."
    )
    parser.add_argument("-H", "--host", default="0.0.0.0")
    parser.add_argument("-p", "--port", type=int, default=9998)
    parser.add_argument("-b", "--backlog", type=int, default=5)
    parser.add_argument(
        "-m",
        "--mode",
        choices=["ack", "echo", "banner", "none"],
        default="ack",
        help="Respuesta al recibir datos: ack (b'ACK'), echo (reenvia lo recibido), banner (texto fijo), none",
    )
    parser.add_argument("--banner", default="bhp-toolkit tcp server\n", help="Texto a enviar en modo banner")
    parser.add_argument("-s", "--recv-size", type=int, default=1024)
    parser.add_argument("--once", action="store_true", help="Atender una sola conexion y salir")
    parser.add_argument("-q", "--quiet", action="store_true", help="No imprimir los datos recibidos")
    return parser.parse_args()


def main():
    args = parse_args()
    serve(
        args.host,
        args.port,
        args.backlog,
        args.mode,
        args.banner,
        args.recv_size,
        args.once,
        not args.quiet,
    )


if __name__ == "__main__":
    main()

import argparse
import socket
import sys
import threading

HEX_FILTER = "".join(
    [(len(repr(chr(i))) == 3) and chr(i) or "." for i in range(256)]
)


def hexdump(src, length=16, show=True):
    if isinstance(src, bytes):
        src = src.decode(errors="replace")
    results = []
    for i in range(0, len(src), length):
        word = str(src[i:i + length])
        printable = word.translate(HEX_FILTER)
        hexa = " ".join([f"{ord(c):02X}" for c in word])
        hexwidth = length * 3
        results.append(f"{i:04x}   {hexa:<{hexwidth}}   {printable}")
    if show:
        for line in results:
            print(line)
    else:
        return results


def receive_from(connection, timeout=5.0):
    buffer = b""
    connection.settimeout(timeout)
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except OSError:
        pass
    return buffer


def request_handler(buffer):
    return buffer


def response_handler(buffer):
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first, timeout, verbose):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    if receive_first:
        remote_buffer = receive_from(remote_socket, timeout)
        if verbose:
            hexdump(remote_buffer)
        remote_buffer = response_handler(remote_buffer)
        if len(remote_buffer):
            print(f"[<==] Sending {len(remote_buffer)} bytes to localhost.")
            client_socket.send(remote_buffer)

    while True:
        local_buffer = receive_from(client_socket, timeout)
        if len(local_buffer):
            print(f"[==>] Received {len(local_buffer)} bytes from localhost.")
            if verbose:
                hexdump(local_buffer)
            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        remote_buffer = receive_from(remote_socket, timeout)
        if len(remote_buffer):
            print(f"[<==] Received {len(remote_buffer)} bytes from remote.")
            if verbose:
                hexdump(remote_buffer)
            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")

        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")
            break


def server_loop(local_host, local_port, remote_host, remote_port, receive_first, timeout, verbose):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((local_host, local_port))
    except OSError as e:
        print(f"[!!] No se pudo hacer bind en {local_host}:{local_port}: {e}")
        sys.exit(1)

    print(f"[*] Escuchando en {local_host}:{local_port}")
    server.listen(5)

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"[*] Conexion entrante de {addr[0]}:{addr[1]}")
            proxy_thread = threading.Thread(
                target=proxy_handler,
                args=(client_socket, remote_host, remote_port, receive_first, timeout, verbose),
                daemon=True,
            )
            proxy_thread.start()
    except KeyboardInterrupt:
        print("\n[!] Proxy detenido.")
    finally:
        server.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Proxy TCP para inspeccionar y modificar trafico entre un cliente local y un host remoto."
    )
    parser.add_argument("local_host", help="IP local en la que escuchar")
    parser.add_argument("local_port", type=int, help="Puerto local en el que escuchar")
    parser.add_argument("remote_host", help="Host remoto al que reenviar el trafico")
    parser.add_argument("remote_port", type=int, help="Puerto remoto al que reenviar el trafico")
    parser.add_argument(
        "-r",
        "--receive-first",
        action="store_true",
        help="Esperar datos del host remoto antes que del cliente local (p. ej. banners FTP/SMTP)",
    )
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Timeout de recepcion en segundos")
    parser.add_argument("-q", "--quiet", action="store_true", help="No imprimir el hexdump del trafico")
    return parser.parse_args()


def main():
    args = parse_args()
    server_loop(
        args.local_host,
        args.local_port,
        args.remote_host,
        args.remote_port,
        args.receive_first,
        args.timeout,
        not args.quiet,
    )


if __name__ == "__main__":
    main()

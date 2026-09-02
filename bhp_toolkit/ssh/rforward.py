import argparse
import getpass
import select
import socket
import threading

import paramiko


def handler(channel, remote_host, remote_port):
    sock = socket.socket()
    try:
        sock.connect((remote_host, remote_port))
    except Exception as e:
        print(f"[!] No se pudo conectar a {remote_host}:{remote_port}: {e}")
        return

    print(
        f"[*] Tunel abierto {channel.origin_addr} -> {channel.getpeername()} -> ({remote_host}, {remote_port})"
    )
    while True:
        r, _, _ = select.select([sock, channel], [], [])
        if sock in r:
            data = sock.recv(1024)
            if not data:
                break
            channel.send(data)
        if channel in r:
            data = channel.recv(1024)
            if not data:
                break
            sock.send(data)
    channel.close()
    sock.close()
    print(f"[*] Tunel cerrado desde {channel.origin_addr}")


def reverse_forward_tunnel(server_port, remote_host, remote_port, transport):
    transport.request_port_forward("", server_port)
    while True:
        channel = transport.accept(1000)
        if channel is None:
            continue
        thread = threading.Thread(
            target=handler, args=(channel, remote_host, remote_port), daemon=True
        )
        thread.start()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tunel SSH inverso: expone un servicio local a traves de un servidor SSH remoto."
    )
    parser.add_argument("host", help="Servidor SSH al que conectarse")
    parser.add_argument("-p", "--port", type=int, default=22)
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-k", "--keyfile", default=None)
    parser.add_argument("--ask-pass", action="store_true")
    parser.add_argument(
        "-r", "--remote-port", type=int, required=True, help="Puerto a abrir en el servidor SSH"
    )
    parser.add_argument("-d", "--dest", required=True, help="host:puerto local/accesible a exponer")
    parser.add_argument("--strict-host-check", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    dest_host, dest_port = args.dest.split(":")
    dest_port = int(dest_port)

    password = getpass.getpass("Contrasena SSH: ") if args.ask_pass else None
    policy = paramiko.RejectPolicy() if args.strict_host_check else paramiko.WarningPolicy()

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(policy)
    client.connect(
        args.host, port=args.port, username=args.user, password=password, key_filename=args.keyfile
    )

    print(f"[*] Reenviando puerto remoto {args.host}:{args.remote_port} -> {dest_host}:{dest_port}")
    try:
        reverse_forward_tunnel(args.remote_port, dest_host, dest_port, client.get_transport())
    except KeyboardInterrupt:
        print("\n[!] Tunel detenido.")
    finally:
        client.close()


if __name__ == "__main__":
    main()

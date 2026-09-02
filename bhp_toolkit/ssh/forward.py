import argparse
import getpass
import select
import socketserver

import paramiko


class ForwardServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(socketserver.BaseRequestHandler):
    chain_host = None
    chain_port = None
    ssh_transport = None

    def handle(self):
        try:
            channel = self.ssh_transport.open_channel(
                "direct-tcpip",
                (self.chain_host, self.chain_port),
                self.request.getpeername(),
            )
        except Exception as e:
            print(f"[!] No se pudo abrir el canal hacia {self.chain_host}:{self.chain_port}: {e}")
            return
        if channel is None:
            print(f"[!] El servidor SSH rechazo el reenvio hacia {self.chain_host}:{self.chain_port}")
            return

        print(f"[*] Tunel abierto: {self.request.getpeername()} -> {self.chain_host}:{self.chain_port}")
        while True:
            r, _, _ = select.select([self.request, channel], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if not data:
                    break
                channel.send(data)
            if channel in r:
                data = channel.recv(1024)
                if not data:
                    break
                self.request.send(data)
        channel.close()
        self.request.close()
        print("[*] Tunel cerrado.")


def forward_tunnel(local_port, remote_host, remote_port, transport):
    class SubHandler(Handler):
        pass

    SubHandler.chain_host = remote_host
    SubHandler.chain_port = remote_port
    SubHandler.ssh_transport = transport

    server = ForwardServer(("127.0.0.1", local_port), SubHandler)
    server.serve_forever()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tunel SSH de reenvio local (equivalente a ssh -L)."
    )
    parser.add_argument("host", help="Servidor SSH al que conectarse")
    parser.add_argument("-p", "--port", type=int, default=22)
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-k", "--keyfile", default=None)
    parser.add_argument("--ask-pass", action="store_true")
    parser.add_argument("-L", "--local-port", type=int, required=True, help="Puerto local a abrir")
    parser.add_argument(
        "-r", "--remote", required=True, help="host:puerto remoto accesible desde el servidor SSH"
    )
    parser.add_argument("--strict-host-check", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    remote_host, remote_port = args.remote.split(":")
    remote_port = int(remote_port)

    password = getpass.getpass("Contrasena SSH: ") if args.ask_pass else None
    policy = paramiko.RejectPolicy() if args.strict_host_check else paramiko.WarningPolicy()

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(policy)
    client.connect(
        args.host, port=args.port, username=args.user, password=password, key_filename=args.keyfile
    )

    print(f"[*] Reenviando 127.0.0.1:{args.local_port} -> {remote_host}:{remote_port} a traves de {args.host}")
    try:
        forward_tunnel(args.local_port, remote_host, remote_port, client.get_transport())
    except KeyboardInterrupt:
        print("\n[!] Tunel detenido.")
    finally:
        client.close()


if __name__ == "__main__":
    main()

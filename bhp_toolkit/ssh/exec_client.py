import argparse
import getpass
import sys

import paramiko


def build_client(hostname, port, username, password, key_filename, host_key_policy):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(host_key_policy)
    client.connect(
        hostname,
        port=port,
        username=username,
        password=password,
        key_filename=key_filename,
    )
    return client


def run_once(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    if out:
        print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
    return stdout.channel.recv_exit_status()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ejecuta comandos en un servidor remoto via SSH (Paramiko)."
    )
    parser.add_argument("host")
    parser.add_argument("-p", "--port", type=int, default=22)
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-k", "--keyfile", default=None, help="Ruta a clave privada")
    parser.add_argument("--ask-pass", action="store_true", help="Solicitar contrasena")
    parser.add_argument(
        "-c",
        "--command",
        default=None,
        help="Comando unico a ejecutar; si se omite, abre un bucle interactivo",
    )
    parser.add_argument(
        "--strict-host-check",
        action="store_true",
        help="Rechaza host keys desconocidas en vez de solo avisar",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    password = getpass.getpass("Contrasena SSH: ") if args.ask_pass else None
    policy = paramiko.RejectPolicy() if args.strict_host_check else paramiko.WarningPolicy()
    client = build_client(args.host, args.port, args.user, password, args.keyfile, policy)
    try:
        if args.command:
            sys.exit(run_once(client, args.command))
        print("[*] Sesion SSH interactiva. Escribe 'exit' para salir.")
        while True:
            command = input(f"{args.user}@{args.host}$ ").strip()
            if command.lower() in ("exit", "quit"):
                break
            if not command:
                continue
            run_once(client, command)
    except (KeyboardInterrupt, EOFError):
        print("\n[!] Interrumpido por el usuario.")
    finally:
        client.close()


if __name__ == "__main__":
    main()

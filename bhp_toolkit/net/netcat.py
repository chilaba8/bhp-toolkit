import argparse
import shlex
import socket
import subprocess
import sys
import textwrap
import threading


def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return ""
    try:
        output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output
    except (FileNotFoundError, OSError) as e:
        return f"{e}\n"
    return output.decode(errors="replace")


class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)
        try:
            while True:
                response = ""
                while True:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    response += data.decode(errors="replace")
                    if len(data) < 4096:
                        break
                if response:
                    print(response)
                buffer = input("> ")
                buffer += "\n"
                self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print("User terminated.")
        finally:
            self.socket.close()

    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        print(f"[*] Listening on {self.args.target}:{self.args.port}")
        while True:
            client_socket, address = self.socket.accept()
            print(f"[*] Accepted connection from {address[0]}:{address[1]}")
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,), daemon=True
            )
            client_thread.start()

    def handle(self, client_socket):
        with client_socket:
            try:
                if self.args.execute:
                    output = execute(self.args.execute)
                    client_socket.send(output.encode())

                elif self.args.upload:
                    file_buffer = b""
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                        file_buffer += data
                    with open(self.args.upload, "wb") as f:
                        f.write(file_buffer)
                    message = f"Saved file {self.args.upload} ({len(file_buffer)} bytes)\n"
                    client_socket.send(message.encode())

                elif self.args.command:
                    cmd_buffer = b""
                    while True:
                        client_socket.send(b"BHP: #> ")
                        while b"\n" not in cmd_buffer:
                            data = client_socket.recv(64)
                            if not data:
                                return
                            cmd_buffer += data
                        line, _, cmd_buffer = cmd_buffer.partition(b"\n")
                        response = execute(line.decode(errors="replace"))
                        if response:
                            client_socket.send(response.encode())
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"[!] Conexion terminada: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="BHP Net Tool - sustituto minimalista de Netcat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Ejemplos:
              bhp-netcat -t 192.168.1.203 -p 5555 -l -c              # shell de comandos
              bhp-netcat -t 192.168.1.203 -p 5555 -l -u mytest.txt   # subir archivo
              bhp-netcat -t 192.168.1.203 -p 5555 -l -e "cat /etc/passwd"  # ejecutar comando
              echo 'ABC' | bhp-netcat -t 192.168.1.203 -p 135        # enviar texto al puerto
              bhp-netcat -t 192.168.1.203 -p 5555                    # conectar como cliente
            """
        ),
    )
    parser.add_argument("-c", "--command", action="store_true", help="iniciar shell de comandos interactivo")
    parser.add_argument("-e", "--execute", help="ejecutar el comando especificado y devolver la salida")
    parser.add_argument("-l", "--listen", action="store_true", help="modo escucha (listener)")
    parser.add_argument("-p", "--port", type=int, default=5555, help="puerto")
    parser.add_argument(
        "-t", "--target", default="127.0.0.1", help="IP destino (cliente) o de escucha (listener)"
    )
    parser.add_argument("-u", "--upload", help="ruta donde guardar el archivo subido")
    return parser.parse_args()


def main():
    args = parse_args()
    buffer = "" if args.listen else sys.stdin.read()
    nc = NetCat(args, buffer.encode())
    nc.run()


if __name__ == "__main__":
    main()

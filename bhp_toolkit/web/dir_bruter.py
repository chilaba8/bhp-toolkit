import argparse
import queue
import sys
import threading

import requests

DEFAULT_EXTENSIONS = [".php", ".bak", ".orig", ".inc"]
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/119.0"


def extend_words(word, extensions, words):
    if "." in word:
        words.put(f"/{word}")
    else:
        words.put(f"/{word}/")
    for extension in extensions:
        words.put(f"/{word}{extension}")


def get_words(wordlist, extensions):
    words = queue.Queue()
    with open(wordlist, "r", encoding="utf-8", errors="ignore") as f:
        raw_words = f.read()

    for word in raw_words.split():
        extend_words(word, extensions, words)
    return words


def dir_bruter(target, words, headers, only_success):
    while not words.empty():
        path = words.get()
        url = f"{target}{path}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
        except requests.exceptions.RequestException:
            if not only_success:
                sys.stderr.write("x")
                sys.stderr.flush()
            continue

        if r.status_code == 200:
            print(f"\n[+] Success ({r.status_code}): {url}")
        elif r.status_code == 404:
            if not only_success:
                sys.stderr.write(".")
                sys.stderr.flush()
        else:
            print(f"[?] {r.status_code} => {url}")


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Forzador de directorios y archivos por fuerza bruta: prueba una lista de "
            "palabras (mas variantes de directorio/extension) contra un sitio web objetivo."
        )
    )
    parser.add_argument("target", help="URL base del objetivo (p. ej. http://objetivo.com)")
    parser.add_argument("wordlist", help="Archivo de lista de palabras")
    parser.add_argument(
        "-e", "--extensions", default=",".join(DEFAULT_EXTENSIONS),
        help=f"Extensiones a probar, separadas por coma (por defecto: {','.join(DEFAULT_EXTENSIONS)})",
    )
    parser.add_argument("-t", "--threads", type=int, default=10)
    parser.add_argument("-a", "--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument(
        "-q", "--only-success", action="store_true",
        help="No mostrar el progreso (x/.) en stderr, solo los resultados",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    extensions = [e if e.startswith(".") else f".{e}" for e in args.extensions.split(",") if e]
    headers = {"User-Agent": args.user_agent}

    words = get_words(args.wordlist, extensions)
    print(f"[*] {words.qsize()} rutas a probar contra {args.target}")

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=dir_bruter, args=(args.target, words, headers, args.only_success), daemon=True)
        threads.append(t)
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[!] Detenido por el usuario.")

    print("\n[*] Terminado.")


if __name__ == "__main__":
    main()

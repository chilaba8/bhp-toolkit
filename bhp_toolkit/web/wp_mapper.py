import argparse
import os
import queue
import sys
import threading
import time

import requests

DEFAULT_FILTERED = [".jpg", ".gif", ".png", ".css"]


def gather_paths(local_dir, filtered_exts):
    web_paths = queue.Queue()
    for root, _, files in os.walk(local_dir):
        for fname in files:
            if os.path.splitext(fname)[1].lower() in filtered_exts:
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, local_dir)
            web_paths.put("/" + rel_path.replace(os.sep, "/"))
    return web_paths


def test_remote(target, web_paths, answers, delay):
    while not web_paths.empty():
        path = web_paths.get()
        url = f"{target}{path}"
        time.sleep(delay)  # el objetivo puede tener throttling o bloqueo por peticion
        try:
            r = requests.get(url, timeout=10)
        except requests.exceptions.RequestException:
            sys.stdout.write("x")
            sys.stdout.flush()
            continue

        if r.status_code == 200:
            answers.put(url)
            sys.stdout.write("+")
        else:
            sys.stdout.write("x")
        sys.stdout.flush()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Mapeador de aplicaciones web de codigo abierto: recorre una copia local de la "
            "aplicacion (p. ej. una instalacion de WordPress descargada) para construir un "
            "mapa de rutas de archivo, y comprueba cuales de esas rutas existen en el "
            "objetivo remoto activo."
        )
    )
    parser.add_argument("local_dir", help="Directorio con la copia local de la aplicacion web")
    parser.add_argument("target", help="URL base del objetivo remoto (p. ej. http://objetivo.com/wordpress)")
    parser.add_argument(
        "-f", "--filtered", default=",".join(DEFAULT_FILTERED),
        help=f"Extensiones a ignorar, separadas por coma (por defecto: {','.join(DEFAULT_FILTERED)})",
    )
    parser.add_argument("-t", "--threads", type=int, default=10)
    parser.add_argument(
        "-d", "--delay", type=float, default=2.0, help="Segundos de espera entre peticiones por hilo"
    )
    parser.add_argument(
        "-o", "--outfile", default="myanswers.txt", help="Archivo donde guardar las rutas encontradas"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    filtered = [e if e.startswith(".") else f".{e}" for e in args.filtered.split(",") if e]

    web_paths = gather_paths(args.local_dir, filtered)
    print(f"[*] {web_paths.qsize()} rutas locales encontradas en {args.local_dir}")

    answers = queue.Queue()
    threads = []
    for _ in range(args.threads):
        t = threading.Thread(
            target=test_remote, args=(args.target, web_paths, answers, args.delay), daemon=True
        )
        threads.append(t)
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[!] Detenido por el usuario.")

    with open(args.outfile, "w") as f:
        while not answers.empty():
            f.write(answers.get() + "\n")

    print(f"\n[*] Terminado. Resultados en {args.outfile}")


if __name__ == "__main__":
    main()

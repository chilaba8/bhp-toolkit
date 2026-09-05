import argparse
import os
import sys

import cv2

SCALE_FACTOR = 1.3
MIN_NEIGHBORS = 5


def detect_faces(image_path, cascade, outdir):
    img = cv2.imread(image_path)
    if img is None:
        return 0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=SCALE_FACTOR, minNeighbors=MIN_NEIGHBORS)

    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    if len(faces):
        outname = os.path.join(outdir, os.path.basename(image_path))
        cv2.imwrite(outname, img)

    return len(faces)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Deteccion facial sobre un directorio de imagenes (p. ej. las extraidas con "
            "bhp-recapper), usando un clasificador Haar de OpenCV. Guarda una copia con "
            "cajas verdes alrededor de cada cara detectada."
        )
    )
    parser.add_argument("indir", help="Directorio con las imagenes a analizar")
    parser.add_argument("-o", "--outdir", default="faces", help="Directorio de salida para las imagenes con caras")
    parser.add_argument(
        "-c", "--cascade", default="haarcascade_frontalface_alt.xml",
        help="Ruta al archivo XML del clasificador Haar (descargalo de la pagina de OpenCV)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not os.path.isfile(args.cascade):
        print(f"[!] No se encuentra el clasificador: {args.cascade}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.outdir, exist_ok=True)
    cascade = cv2.CascadeClassifier(args.cascade)

    total_faces = 0
    for fname in sorted(os.listdir(args.indir)):
        fpath = os.path.join(args.indir, fname)
        if not os.path.isfile(fpath):
            continue

        faces = detect_faces(fpath, cascade, args.outdir)
        if faces:
            print(f"Got {faces} cara(s) en {fname}")
        total_faces += faces

    print(f"\n[*] Total de caras detectadas: {total_faces}")


if __name__ == "__main__":
    main()

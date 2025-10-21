#!/usr/env  python

from urllib.parse import urljoin
import sys
import os
import argparse
import unicodedata
import re
import requests
from bs4 import BeautifulSoup
import time

def tprint(string):
    """Takes a string and prints it with a timestamp prefixt."""
    print('[{}] {}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), string))

def send_message(mensaje):
    requests.post(
        "http://192.168.1.40:3003/api/sessions/default/start",
        headers={
            "accept": "application/json",
            "X-Api-Key": "***REMOVED***",
            "Content-Type": "application/json",
        },
        timeout=1000,
    )
    requests.post(
        "http://192.168.1.40:3003/api/sendText",
        headers={
            "accept": "application/json",
            "X-Api-Key": "***REMOVED***",
            "Content-Type": "application/json",
        },
        json={
            "chatId": "***REMOVED***",
            "reply_to": None,
            "text": mensaje,
            "linkPreview": True,
            "linkPreviewHighQuality": True,
            "session": "default",
        },
        timeout=1000,
    )
    requests.post(
        "http://192.168.1.40:3003/api/sessions/default/stop",
        headers={
            "accept": "application/json",
            "X-Api-Key": "***REMOVED***",
            "Content-Type": "application/json",
        },
        timeout=1000,
    )


URL = "https://www.cgeonline.com.ar/informacion/apertura-de-citas.html"


def sanitize_param(p: str) -> str:
    if not p:
        return ""
    # normalize and remove accents
    normalized = unicodedata.normalize("NFKD", p)
    without_accents = "".join(c for c in normalized if not unicodedata.combining(c))
    # lowercase
    lower = without_accents.lower()
    # keep only alphanumeric characters
    cleaned = re.sub(r"[^a-z0-9]", "", lower)
    return cleaned


def main(params: argparse.Namespace) -> None:
    search_text = params.text

    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = f"fecha_{sanitize_param(search_text)}.txt"
    path = os.path.join(script_dir, filename)

    response = requests.get(URL, timeout=1000)
    bs = BeautifulSoup(response.content, "html.parser")

    tabla = [
        [
            urljoin(URL, td.a["href"]) if td.a is not None else "".join(td.stripped_strings)
            for td in tr.children
            if td != "\n"
        ]
        for tr in bs.find_all("tr")
    ]

    try:
        row = [x for x in tabla if x[0] == search_text][0]
    except IndexError:
        tprint(f"No se encontró la fila con el texto: {search_text}")
        sys.exit(2)

    fecha = row[1]
    link = row[3]

    fecha_archivo = ""
    try:
        with open(path, "r+", encoding="utf-8") as archivo_fecha:
            fecha_archivo = archivo_fecha.read()
    except FileNotFoundError:
        tprint("Primera ejecución, se creará el archivo de fecha")

    if fecha == fecha_archivo:
        tprint("Ejecutado ok, sin cambios")
        return

    with open(path, "w+", encoding="utf-8") as archivo_fecha:
        archivo_fecha.write(fecha)
    tprint(f"Ejecutado ok, cambió la fecha ({fecha}), enviando mensaje")

    message = f"Hay una nueva fecha: {fecha}, entrá acá: {link}"
    send_message(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrapea la página de citas y notifica cuando cambia la fecha para una fila dada.")
    parser.add_argument(
        "--text",
        "-t",
        dest="text",
        help='Texto a buscar en la primera columna de la tabla (por ej: "Registro de Matrícula Consular-Altas").',
    )
    args = parser.parse_args()
    main(args)

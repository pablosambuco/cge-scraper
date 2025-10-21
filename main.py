#!/usr/bin/env python3

from urllib.parse import urljoin
import sys
import os
import argparse
import unicodedata
import re
import requests
from bs4 import BeautifulSoup
import time
import tomllib
import tomlkit

# config cache
_CONFIG = None

def read_config(path: str):
    """Read TOML config file. Use tomllib if available (Py3.11+), otherwise fall
    back to the third-party 'toml' package. Returns a dict.
    """
    with open(path, "rb") as f:
        return tomllib.load(f)

def get_config(path: str | None = None):

    global _CONFIG
    if _CONFIG is not None and path is None:
        return _CONFIG

    cfg_path = (
        path
        if path
        else os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
    )
    if not os.path.exists(cfg_path):
        template = {
            "api": {"key": "", "base_url": ""},
            "chat": {"chat_id": ""},
            "web": {"url": ""}
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(template))
        print(f"Se creó un archivo de configuración de ejemplo en: {cfg_path}")
        print("Por favor edítalo y añade tu API key y chat_id, luego vuelve a ejecutar el programa.")
        sys.exit(1)

    cfg = read_config(cfg_path)
    if path is None:
        _CONFIG = cfg
    return cfg

def tprint(string):
    """Takes a string and prints it with a timestamp prefix."""
    print("[{}] {}".format(time.strftime("%Y-%m-%d %H:%M:%S"), string))

def send_message(mensaje):
    cfg = get_config()
    base = cfg["api"]["base_url"].rstrip("/")
    key = cfg["api"]["key"]
    chat_id = cfg["chat"]["chat_id"]

    _requests = (
        requests
        if "requests" in globals() and requests is not None
        else __import__("requests")
    )

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    if key:
        headers["X-Api-Key"] = key

    _requests.post(f"{base}/sessions/default/start", headers=headers, timeout=1000)
    _requests.post(
        f"{base}/sendText",
        headers=headers,
        json={
            "chatId": chat_id,
            "reply_to": None,
            "text": mensaje,
            "linkPreview": True,
            "linkPreviewHighQuality": True,
            "session": "default",
        },
        timeout=1000,
    )
    _requests.post(f"{base}/sessions/default/stop", headers=headers, timeout=1000)

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
    cfg = get_config(getattr(params, "config", None))
    url = cfg["web"]["url"]
    search_text = params.text

    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = f"fecha_{sanitize_param(search_text)}.txt"
    path = os.path.join(script_dir, filename)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        tprint(f"Error al obtener la URL {url}: {exc}")
        sys.exit(3)

    bs = BeautifulSoup(response.content, "html.parser")

    # Build a table as list of rows, each row is list of cell texts/links.
    tabla = []
    for tr in bs.find_all("tr"):
        cells = []
        for td in tr.find_all(["td", "th"]):
            if td is None:
                continue
            if td.a and td.a.get("href"):
                cells.append(urljoin(url, td.a["href"]))
            else:
                cells.append("".join(td.stripped_strings))
        if cells:
            tabla.append(cells)

    try:
        row = [x for x in tabla if len(x) > 0 and x[0] == search_text][0]
    except IndexError:
        tprint(f"No se encontró la fila con el texto: {search_text}")
        sys.exit(2)

    # Validate expected columns exist
    if len(row) < 4:
        tprint(f"La fila encontrada no tiene las columnas esperadas: {row}")
        sys.exit(4)

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
    parser = argparse.ArgumentParser(
        description="Scrapea la página de citas y notifica cuando cambia la fecha para una fila dada."
    )
    parser.add_argument(
        "--text",
        "-t",
        dest="text",
        required=True,
        help='Texto a buscar en la primera columna de la tabla (por ej: "Registro de Matrícula Consular-Altas").',
    )
    parser.add_argument(
        "--config",
        "-c",
        dest="config",
        help="Ruta al archivo config.toml. Si no se especifica, se usa el del directorio del script.",
    )
    args = parser.parse_args()
    main(args)

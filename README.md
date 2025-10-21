cge-scraper
===========

Descripción
-----------

Pequeño script que scrapea una página web con una tabla de citas y notifica cuando cambia la fecha para una fila específica. Extrae la fila por el texto de la primera columna, guarda la última fecha en un archivo `fecha_<texto_sanitizado>.txt` y envía un mensaje usando una API configurada en `config.toml`.

Requisitos
----------

- Python 3.12+
- uv

Configuración
-------------

Al ejecutar el script por primera vez, si no existe `config.toml` en el mismo directorio que `main.py`, el programa creará un archivo de ejemplo con las claves necesarias. Debes añadir tu API key, base_url y chat_id.

Ejemplo mínimo de `config.toml`:

```toml
[api]
key = ""          # si aplica
base_url = "https://mi-api-ejemplo.local"

[chat]
chat_id = "123456789"

[web]
url = "https://ejemplo.com/tabla-de-citas"
```

Uso
---

Ejecuta el script indicando el texto a buscar (obligatorio):

```bash
uv run main.py --text "Registro de Matrícula Consular-Altas"
```

Opcionalmente puedes especificar un `config.toml` diferente:

```bash
uv run main.py --text "Registro de Matrícula Consular-Altas" --config /ruta/a/config.toml
```

Lo que hace el script:
- Busca en la página `web.url` la fila cuya primera celda coincide exactamente con `--text`.
- Extrae la segunda columna (fecha) y la cuarta (link).
- Si la fecha cambia respecto al archivo local `fecha_<texto_sanitizado>.txt`, sobrescribe el archivo y envía un mensaje a la API configurada en `config.toml`.

Pruebas
-------

La suite de tests usa `pytest`. Para ejecutar las pruebas:

```bash
uv run pytest -q
```

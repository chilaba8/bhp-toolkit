# Mando y control con GitHub (C2)

Plataforma de troyano que usa un repositorio **privado** de GitHub como canal
de mando y control, construida siguiendo el capitulo 7 de *Black Hat Python*.
El troyano lee su configuracion y sus modulos desde GitHub, los ejecuta y
devuelve los resultados exfiltrados al mismo repositorio. El trafico viaja
cifrado sobre HTTPS/SSL.

## Aviso legal

Uso exclusivo en pruebas de penetracion autorizadas, auditorias con permiso
explicito por escrito o laboratorios propios. Desplegar esto contra sistemas
de terceros sin autorizacion es ilegal.

## Estructura

```
github_c2/
├── git_trojan.py        # troyano principal (importador remoto + runner)
├── config/
│   └── abc.json         # tareas del troyano con ID "abc" (lista de modulos)
├── modules/
│   ├── dirlister.py     # modulo de ejemplo: lista el directorio actual
│   └── environment.py   # modulo de ejemplo: devuelve las variables de entorno
└── data/                # datos exfiltrados (se rellena en ejecucion)
```

## Puesta en marcha

1. Crea un repositorio **privado** llamado `bhptrojan` en GitHub con la misma
   estructura (`config/`, `modules/`, `data/`).
2. Instala la libreria de la API de GitHub:
   ```
   pip install github3.py
   ```
3. Crea un **token de acceso personal** (permisos de lectura y escritura sobre
   el repo) y guardalo en un archivo local `mytoken.txt` **fuera de control de
   versiones** (ya esta en `.gitignore`).
4. Ajusta `github_connect()` en `git_trojan.py`: cambia `user` y el nombre del
   repositorio (`bhptrojan`) por los tuyos.
5. Sube `config/` y `modules/` a GitHub (codificados por la API en base64).
6. Ejecuta el troyano:
   ```
   python git_trojan.py
   ```

## Como funciona

- `github_connect()` / `get_file_contents()` — autenticacion con el token y
  lectura del contenido de archivos del repo.
- `Trojan` — cada troyano tiene un **ID** unico; lee `config/<id>.json`, importa
  los modulos listados, lanza cada uno en su propio hilo y guarda la salida en
  `data/<id>/<timestamp>.data` (base64) de vuelta en GitHub. Entre ciclos duerme
  un intervalo aleatorio para dificultar el analisis de patrones de red.
- `GitImporter` — se engancha en `sys.meta_path` para **importar modulos
  remotamente**: si un modulo no existe en local, lo descarga de `modules/` del
  repo, lo decodifica de base64 y lo carga en memoria.

## Aviso de seguridad

Con un repositorio **publico**, cualquier informacion sensible (tokens,
variables de entorno exfiltradas, configuracion) quedaria expuesta a todo el
mundo. Usa siempre un repositorio **privado**. El cifrado de modulos, config y
datos exfiltrados se trata en el capitulo 9.

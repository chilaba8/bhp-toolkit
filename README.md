# bhp-toolkit

Conjunto de herramientas de red en Python para auditorias de seguridad y pentesting,
construidas mientras trabajo los ejercicios de *Black Hat Python* (2a edicion).
Cada modulo implementa un patron del libro con CLI propia, pensado para usarse
en entornos de laboratorio y engagements autorizados.

## Aviso legal

Estas herramientas estan pensadas exclusivamente para pruebas de penetracion
autorizadas, auditorias de seguridad con permiso explicito del propietario del
sistema, laboratorios propios (Dockerlabs, HTB, TryHackMe, etc.) o CTFs. Usarlas
contra sistemas sin autorizacion es ilegal. El autor no se hace responsable del
mal uso de este codigo.

## Instalacion

```bash
git clone <url-del-repo>
cd bhp-toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Herramientas

### `bhp-ssh-exec` — Cliente de ejecucion remota de comandos

Se conecta a un servidor SSH y ejecuta comandos (uno suelto o en bucle
interactivo), usando `paramiko.SSHClient.exec_command`.

```bash
bhp-ssh-exec 192.168.1.203 -u justin --ask-pass
bhp-ssh-exec 192.168.1.203 -u justin -k ~/.ssh/id_rsa -c "whoami"
```

### `bhp-ssh-forward` — Tunel SSH de reenvio local (equivalente a `ssh -L`)

Abre un puerto local que reenvia el trafico, a traves del servidor SSH, hacia
un host y puerto solo accesibles desde la red del servidor SSH.

```bash
# Expone web:80 (visible solo desde sshserver) en tu localhost:8008
bhp-ssh-forward sshserver -u justin --ask-pass -L 8008 -r web:80
```

### `bhp-ssh-rforward` — Tunel SSH inverso

Utilidad para cuando el sistema objetivo (p. ej. Windows) no tiene servidor
SSH pero si tiene un cliente. Te conectas desde el objetivo hacia tu propio
servidor SSH y expones alli un puerto que reenvia el trafico de vuelta a un
host/puerto accesible desde el objetivo.

```bash
# Desde el sistema objetivo: abre el puerto 8081 en tu servidor SSH (192.168.1.203)
# y lo reenvia hacia 192.168.1.207:3000, accesible desde el objetivo
bhp-ssh-rforward 192.168.1.203 -u tim --ask-pass -r 8081 -d 192.168.1.207:3000
```

### `bhp-tcp-client` — Cliente TCP generico

Para probar servicios, hacer banner grabbing, enviar payloads de fuzzing o
hablar con protocolos a mano cuando no hay herramientas de red disponibles en
el entorno.

```bash
# Peticion HTTP simple
bhp-tcp-client www.example.com 80 -d "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"

# Enviar un payload binario desde un archivo (fuzzing) y ver la respuesta en crudo
bhp-tcp-client 10.0.0.5 9000 -f payload.bin --raw

# Solo escuchar lo que el servicio envia al conectar (banner grabbing)
bhp-tcp-client 10.0.0.5 21 --no-send
```

### `bhp-udp-client` — Cliente UDP generico

Igual que `bhp-tcp-client` pero sin conexion previa (`sendto`/`recvfrom`),
para probar servicios UDP (DNS, SNMP, servicios propietarios, etc.).

```bash
bhp-udp-client 127.0.0.1 9997 -d "AAABBBCCC"
bhp-udp-client 10.0.0.5 161 -f payload.bin --raw
```

### `bhp-tcp-server` — Servidor TCP multihilo generico

Para probar los clientes de arriba, montar un listener rapido en un
laboratorio o servir de base a herramientas mas complejas (proxy, shell).

```bash
# Servidor de eco en el puerto 9998
bhp-tcp-server -p 9998 -m echo

# Servidor que solo confirma recepcion con ACK, una sola conexion
bhp-tcp-server -p 9998 -m ack --once
```

### `bhp-netcat` — Sustituto minimalista de Netcat

Listener/cliente TCP para sistemas donde no hay `nc` pero si Python: subir
archivos, ejecutar un comando puntual o dejar un shell de comandos
interactivo compatible con el propio Netcat (usa `\n` como separador, asi
que puedes hablarle con `nc` normal desde el otro lado).

**Aviso:** el modo `-c` deja un shell de comandos remoto sin autenticacion.
Usalo solo en laboratorios propios o en el post-explotacion de un engagement
autorizado, nunca expuesto a redes que no controlas.

```bash
# Shell de comandos remoto
bhp-netcat -t 192.168.1.203 -p 5555 -l -c
bhp-netcat -t 192.168.1.203 -p 5555          # cliente, Ctrl-D para enviar stdin

# Ejecutar un unico comando y devolver la salida
bhp-netcat -t 192.168.1.203 -p 5555 -l -e "cat /etc/passwd"

# Subir un archivo al listener
bhp-netcat -t 192.168.1.203 -p 5555 -l -u recibido.txt

# Hablar con cualquier servicio TCP, a la antigua usanza
echo -ne "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n" | bhp-netcat -t example.com -p 80
```

### `bhp-tcp-proxy` — Proxy TCP con hexdump

Se interpone entre un cliente y un servicio remoto, mostrando en hexdump
todo el trafico en ambas direcciones. Util para entender protocolos
desconocidos, capturar credenciales en texto plano o preparar un fuzzer,
en entornos donde no puedes usar Wireshark. `request_handler` y
`response_handler` son los puntos donde modificar el trafico al vuelo.

```bash
# Todo lo que llegue a 127.0.0.1:9000 se reenvia a 10.0.0.5:21, mostrando hexdump
bhp-tcp-proxy 127.0.0.1 9000 10.0.0.5 21

# Servicios que hablan primero (banners FTP/SMTP)
bhp-tcp-proxy 127.0.0.1 9000 10.0.0.5 21 --receive-first
```

### `bhp-sniffer` — Sniffer con sockets sin procesar

Decodifica en vivo las cabeceras IP (y, si aplica, ICMP) de todo el trafico
visible en una interfaz. Requiere privilegios de root (crea un `SOCK_RAW`).

```bash
sudo bhp-sniffer -H 0.0.0.0
```

### `bhp-host-discovery` — Escaner de descubrimiento de hosts por UDP

Envia datagramas UDP con una firma propia a un puerto cerrado en toda una
subred y escucha las respuestas ICMP "puerto inalcanzable" para deducir que
hosts estan vivos, sin necesidad de un escaneo de puertos completo. Tambien
requiere privilegios de root.

```bash
sudo bhp-host-discovery 192.168.1.0/24
```

### `bhp-mail-sniffer` — Sniffer de credenciales de correo electronico

Sniffer basado en Scapy que intercepta trafico SMTP/POP3/IMAP en texto plano y
muestra los paquetes cuyo contenido incluye palabras clave de login (`user`,
`pass`, `login`, `pwd`). Combinalo con `bhp-arper` para interceptar el
trafico de otra maquina de la LAN.

```bash
sudo bhp-mail-sniffer -i eth0
```

### `bhp-arper` — Envenenador ARP para ataques MITM

Envenena la cache ARP de una victima y de la puerta de enlace para
interponerse en su trafico (Man-In-The-Middle), lo captura en un archivo
pcap y restaura las tablas ARP originales al terminar (por `Ctrl-C` o al
alcanzar el numero de paquetes indicado).

```bash
sudo bhp-arper 192.168.1.193 192.168.1.254 eth0 -c 200 -o arper.pcap
```

### `bhp-recapper` — Extractor de contenido HTTP desde un pcap

Reconstruye las sesiones TCP de un archivo pcap (por ejemplo, el generado
por `bhp-arper`) y extrae el contenido de las respuestas HTTP cuyo
`Content-Type` coincida con el tipo indicado (por defecto, imagenes),
descomprimiendo `gzip`/`deflate` si hace falta.

```bash
bhp-recapper arper.pcap -o pictures -t image
```

### `bhp-face-detector` — Deteccion facial en imagenes extraidas

Ejecuta un clasificador Haar de OpenCV sobre un directorio de imagenes (por
ejemplo, las extraidas con `bhp-recapper`) para determinar que imagenes
contienen caras, dibujando un recuadro verde sobre cada una. Requiere las
dependencias opcionales de `faces` (`pip install -e ".[faces]"`) y el
archivo del clasificador:

```bash
wget http://eclecti.cc/files/2008/03/haarcascade_frontalface_alt.xml
bhp-face-detector pictures -o faces -c haarcascade_frontalface_alt.xml
```

### `bhp-wp-mapper` — Mapeador de aplicaciones web de codigo abierto

Recorre una copia local de una aplicacion web de codigo abierto (p. ej. una
instalacion de WordPress descargada) para construir un mapa de rutas de
archivo, y comprueba con hilos cuales de esas rutas existen tambien en el
objetivo remoto activo. Guarda las coincidencias en un archivo de texto.

```bash
bhp-wp-mapper ~/Descargas/wordpress http://objetivo.com/wordpress -o myanswers.txt
```

### `bhp-dir-bruter` — Forzador de directorios y archivos

Cuando no conoces la estructura interna del objetivo (aplicacion
personalizada, sin codigo fuente disponible), prueba por fuerza bruta una
lista de palabras -junto con variantes de directorio y extension de
archivo comunes (`.php`, `.bak`, `.orig`, `.inc`)- contra el sitio web
objetivo.

```bash
bhp-dir-bruter http://objetivo.com /usr/share/wordlists/dirb/common.txt -t 20
```

### `bhp-form-bruter` — Forzador de autenticacion por formulario HTML

Extrae automaticamente los campos de un formulario de login (incluidos
tokens ocultos y cookies anti-CSRF, gestionadas via `requests.Session`) y
prueba contrasenas de una lista contra el. Los nombres de campo por
defecto (`log`/`pwd`) corresponden al formulario de WordPress; ajustalos
con `-U`/`-P` para otros CMS o formularios personalizados.

```bash
bhp-form-bruter http://objetivo.com/wp-login.php admin /usr/share/seclists/Passwords/Software/cain-and-abel.txt \
    -s "Welcome to WordPress!" -t 5 -d 2
```

## Extensiones de Burp Suite

A partir de aqui, las herramientas no son scripts CLI instalables con pip,
sino extensiones Jython que se cargan dentro de Burp Suite. Detalles de
instalacion y uso en [`burp_extensions/README.md`](burp_extensions/README.md).

### `bhp_fuzzer.py` — Fuzzer de mutacion para Intruder

Generador de cargas utiles personalizado para Burp Intruder: muta la
carga util original insertando al azar un intento de inyeccion SQL, un
intento de XSS o repitiendo un fragmento aleatorio de la propia carga
util.

### `bhp_bing.py` — Descubrimiento de hosts via API de Bing

Menu contextual **Send to Bing** sobre cualquier peticion HTTP: consulta
la API de Bing Web Search por IP (otros virtual hosts en el mismo
servidor) y por dominio (subdominios indexados), y anade automaticamente
al ambito objetivo de Burp cualquier sitio nuevo que encuentre. Requiere
una clave gratuita de la API de Bing Web Search.

## Roadmap

- [x] Ejecucion de comandos remotos via SSH
- [x] Tunel SSH de reenvio local
- [x] Tunel SSH inverso
- [x] Cliente TCP generico
- [x] Cliente UDP generico
- [x] Servidor TCP multihilo generico
- [x] Sustituto de Netcat (shell, upload, execute)
- [x] Proxy TCP con hexdump
- [x] Sockets sin procesar / sniffer de red
- [x] Escaner de descubrimiento de hosts
- [x] Sniffer de credenciales de correo con Scapy
- [x] Envenenador ARP (MITM) con Scapy
- [x] Extractor de contenido HTTP desde pcap
- [x] Deteccion facial en imagenes extraidas
- [x] Mapeador de aplicaciones web de codigo abierto
- [x] Forzador de directorios y archivos
- [x] Forzador de autenticacion por formulario HTML
- [x] Extension Burp: fuzzer de mutacion para Intruder
- [x] Extension Burp: descubrimiento de subdominios/hosts via API de Bing
- [ ] Extension Burp: generador de listas de contrasenas desde contenido rastreado

Las extensiones de Burp del capitulo 6 son *plugins* Jython que se cargan
dentro de Burp Suite (API `burp.IBurpExtender` / `IIntruderPayloadGenerator`,
sintaxis Python 2), no scripts CLI independientes. Vivirian en un directorio
aparte (p. ej. `burp_extensions/`), fuera del empaquetado `pip install -e .`
del resto del toolkit.

## Referencia

Basado en *Black Hat Python, 2nd Edition* (Justin Seitz, Tim Arnold), No Starch
Press — implementaciones propias inspiradas en los patrones del libro, no
copias literales del codigo fuente.

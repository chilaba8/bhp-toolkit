# Extensiones de Burp Suite

Extensiones Jython (Python 2) para Burp Suite, construidas siguiendo el
capitulo 6 de *Black Hat Python*. A diferencia del resto del toolkit, estas
no son scripts CLI: se cargan directamente dentro de Burp y usan su API
(`burp.IBurpExtender` y compania), asi que no forman parte del paquete
`bhp-toolkit` instalable con pip.

## Aviso legal

Igual que el resto del proyecto, uso exclusivo en pruebas de penetracion
autorizadas, auditorias con permiso explicito o laboratorios propios.

## Instalacion

1. Descarga el JAR standalone de Jython (2.7.x) desde
   <https://www.jython.org/download.html>.
2. En Burp, ve a **Extender > Options > Python Environment** y selecciona
   la ubicacion de ese JAR.
3. Ve a **Extender > Extensions > Add**, elige tipo **Python** y selecciona
   el archivo `.py` de la extension que quieras cargar.
4. Revisa la pestana **Errors** de la extension si algo no carga bien.

## Extensiones

### `bhp_fuzzer.py` — Fuzzer de mutacion para Intruder

Registra un generador de cargas utiles personalizado para Burp Intruder.
Por cada iteracion, muta la carga util original insertando al azar un
intento de inyeccion SQL, un intento de XSS o repitiendo un fragmento
aleatorio de la propia carga util. Util para descubrir errores o
comportamientos inesperados que un escaner generico podria pasar por alto.

Uso: intercepta una peticion con Proxy, envíala a Intruder
(`Send to Intruder`), marca las posiciones a mutar, y en la pestana
**Payloads** selecciona el tipo **Extension-generated** con el generador
**BHP Payload Generator**.

### `bhp_bing.py` — Descubrimiento de hosts via API de Bing

Anade un menu contextual **Send to Bing** sobre cualquier peticion HTTP.
Consulta la API de Bing Web Search por IP (otros virtual hosts en el mismo
servidor) y por dominio (subdominios indexados), y anade automaticamente
al ambito objetivo de Burp cualquier sitio nuevo que encuentre.

Necesitas una clave de la API de Bing Web Search (nivel gratuito, hasta
1000 consultas/mes:
<https://www.microsoft.com/en-us/bing/apis/bing-web-search-api>).
Sustituye `API_KEY = "TU_CLAVE_AQUI"` en el archivo antes de cargarlo.

### `bhp_wordlist.py` — Generador de listas de contrasenas desde el sitio

Anade un menu contextual **Create Wordlist** sobre el trafico HTTP
capturado. Extrae las palabras del texto visible de las respuestas
(incluidos los comentarios HTML), descarta las que no sean de tipo texto,
y genera con ellas una lista de contrasenas especifica del sitio, con
variantes al estilo John the Ripper (capitalizada, con sufijos comunes y
el ano actual).

Para cubrir todo el sitio antes de generar la lista, combina con un
analisis pasivo en vivo de Burp: **Dashboard > New live task > Live
passive crawl**, apuntando a todo el trafico de Proxy.

## Referencia

Basado en *Black Hat Python, 2nd Edition* (Justin Seitz, Tim Arnold), No
Starch Press — implementaciones propias inspiradas en los patrones del
libro, no copias literales del codigo fuente.

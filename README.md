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

## Roadmap

- [x] Ejecucion de comandos remotos via SSH
- [x] Tunel SSH de reenvio local
- [x] Tunel SSH inverso
- [ ] Sockets sin procesar / sniffer de red
- [ ] Escaner de descubrimiento de hosts

## Referencia

Basado en *Black Hat Python, 2nd Edition* (Justin Seitz, Tim Arnold), No Starch
Press — implementaciones propias inspiradas en los patrones del libro, no
copias literales del codigo fuente.

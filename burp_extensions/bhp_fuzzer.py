# Extension de Burp Suite (Jython) que anade un generador de cargas utiles
# personalizado a Intruder. Muta la carga util original insertando de forma
# aleatoria un intento de inyeccion SQL, un intento de XSS o repitiendo un
# fragmento aleatorio de la propia carga util, para provocar errores o
# comportamientos que un escaner generico podria pasar por alto.
#
# Instalacion: Burp > Extender > Options > Python Environment, apunta al JAR
# de Jython standalone. Despues, Extender > Extensions > Add > Python y
# selecciona este archivo.

from burp import IBurpExtender
from burp import IIntruderPayloadGeneratorFactory
from burp import IIntruderPayloadGenerator

import random

MAX_PAYLOADS = 10


class BurpExtender(IBurpExtender, IIntruderPayloadGeneratorFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()

        callbacks.setExtensionName("BHP Fuzzer")
        callbacks.registerIntruderPayloadGeneratorFactory(self)
        return

    def getGeneratorName(self):
        return "BHP Payload Generator"

    def createNewInstance(self, attack):
        return BHPFuzzer(attack)


class BHPFuzzer(IIntruderPayloadGenerator):
    def __init__(self, attack):
        self._attack = attack
        self.max_payloads = MAX_PAYLOADS
        self.num_iterations = 0

    def hasMorePayloads(self):
        return self.num_iterations < self.max_payloads

    def getNextPayload(self, current_payload):
        # convertimos la matriz de bytes original en una cadena de texto
        payload = "".join(chr(b) for b in current_payload)
        payload = self.mutate_payload(payload)
        self.num_iterations += 1
        return payload

    def reset(self):
        self.num_iterations = 0
        return

    def mutate_payload(self, original_payload):
        picker = random.randint(1, 3)
        offset = random.randint(0, len(original_payload) - 1)
        front, back = original_payload[:offset], original_payload[offset:]

        if picker == 1:
            # intento sencillo de inyeccion SQL
            front += "'"
        elif picker == 2:
            # intento sencillo de XSS
            front += "<script>alert('BHP!');</script>"
        elif picker == 3:
            # repite un fragmento aleatorio de la carga util original
            chunk_length = random.randint(0, len(back) - 1)
            repeater = random.randint(1, 10)
            for _ in range(repeater):
                front += original_payload[offset:offset + chunk_length]

        return front + back

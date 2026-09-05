# Extension de Burp Suite (Jython) que anade un menu contextual "Send to
# Bing" sobre cualquier peticion HTTP. Consulta la API de Bing Web Search
# por IP (otros virtual hosts en el mismo servidor) y por dominio (otros
# subdominios indexados), e incorpora automaticamente al ambito objetivo
# de Burp cualquier sitio nuevo que encuentre.
#
# Necesitas una clave de la API de Bing Web Search (nivel gratuito, hasta
# 1000 consultas/mes): https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
#
# Instalacion: igual que bhp_fuzzer.py (Extender > Options > Python
# Environment, luego Extender > Extensions > Add > Python).

from burp import IBurpExtender
from burp import IContextMenuFactory

from java.net import URL
from java.util import ArrayList
from javax.swing import JMenuItem
from thread import start_new_thread

import json
import socket
import urllib

API_KEY = "TU_CLAVE_AQUI"
API_HOST = "api.cognitive.microsoft.com"


class BurpExtender(IBurpExtender, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self.context = None

        callbacks.setExtensionName("BHP Bing")
        callbacks.registerContextMenuFactory(self)
        return

    def createMenuItems(self, context_menu):
        self.context = context_menu
        menu_list = ArrayList()
        menu_list.add(JMenuItem("Send to Bing", actionPerformed=self.bing_menu))
        return menu_list

    def bing_menu(self, event):
        http_traffic = self.context.getSelectedMessages()
        print("%d peticion(es) seleccionada(s)" % len(http_traffic))

        for traffic in http_traffic:
            host = traffic.getHttpService().getHost()
            self.bing_search(host)
        return

    def bing_search(self, host):
        try:
            is_ip = bool(socket.inet_aton(host))
        except socket.error:
            is_ip = False

        if is_ip:
            start_new_thread(self.bing_query, ("ip:%s" % host,))
            return

        start_new_thread(self.bing_query, ("domain:%s" % host,))
        try:
            ip_address = socket.gethostbyname(host)
            start_new_thread(self.bing_query, ("ip:%s" % ip_address,))
        except socket.error:
            pass
        return

    def bing_query(self, bing_query_string):
        print("Buscando en Bing: %s" % bing_query_string)

        http_request = "GET https://%s/bing/v7.0/search?" % API_HOST
        http_request += "q=%s HTTP/1.1\r\n" % urllib.quote(bing_query_string)
        http_request += "Host: %s\r\n" % API_HOST
        http_request += "Connection: close\r\n"
        http_request += "Ocp-Apim-Subscription-Key: %s\r\n" % API_KEY
        http_request += "User-Agent: Black Hat Python\r\n\r\n"

        request_bytes = self._helpers.stringToBytes(http_request)
        response_bytes = self._callbacks.makeHttpRequest(API_HOST, 443, True, request_bytes)
        raw_response = self._helpers.bytesToString(response_bytes)

        try:
            json_body = raw_response.split("\r\n\r\n", 1)[1]
            response = json.loads(json_body)
        except (IndexError, TypeError, ValueError) as err:
            print("Sin resultados de Bing: %s" % err)
            return

        sites = list()
        if response.get("webPages"):
            sites = response["webPages"]["value"]

        for site in sites:
            print("*" * 100)
            print("Nombre: %s" % site["name"])
            print("URL: %s" % site["url"])
            print("Descripcion: %r" % site["snippet"])

            java_url = URL(site["url"])
            if not self._callbacks.isInScope(java_url):
                print("Anadiendo %s al ambito de Burp" % site["url"])
                self._callbacks.includeInScope(java_url)

        print("*" * 100)
        return

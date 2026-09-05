# Extension de Burp Suite (Jython) que anade un menu contextual "Create
# Wordlist" sobre el trafico HTTP capturado. Extrae las palabras del texto
# visible de las respuestas (incluidos los comentarios HTML), y genera con
# ellas una lista de contrasenas especifica del sitio, con variantes al
# estilo John the Ripper (capitalizada, con sufijos comunes y el ano
# actual). Combinala con un analisis pasivo en vivo de Burp (Dashboard >
# New live task > Live passive crawl) para cubrir todo el sitio antes de
# generar la lista.
#
# Instalacion: igual que bhp_fuzzer.py (Extender > Options > Python
# Environment, luego Extender > Extensions > Add > Python).

from burp import IBurpExtender
from burp import IContextMenuFactory

from java.util import ArrayList
from javax.swing import JMenuItem

from datetime import datetime
from HTMLParser import HTMLParser

import re

WORD_PATTERN = re.compile(r"[a-zA-Z]\w{2,}")
MAX_WORD_LENGTH = 12


class TagStripper(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.page_text = []

    def handle_data(self, data):
        self.page_text.append(data)

    def handle_comment(self, data):
        # los comentarios de desarrolladores tambien pueden dar pistas
        self.handle_data(data)

    def strip(self, html):
        self.feed(html)
        return " ".join(self.page_text)


class BurpExtender(IBurpExtender, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        self.context = None
        self.hosts = set()

        # empezamos con algo que sabemos que es habitual
        self.wordlist = set(["password"])

        callbacks.setExtensionName("BHP Wordlist")
        callbacks.registerContextMenuFactory(self)
        return

    def createMenuItems(self, context_menu):
        self.context = context_menu
        menu_list = ArrayList()
        menu_list.add(JMenuItem("Create Wordlist", actionPerformed=self.wordlist_menu))
        return menu_list

    def wordlist_menu(self, event):
        http_traffic = self.context.getSelectedMessages()

        for traffic in http_traffic:
            host = traffic.getHttpService().getHost()
            self.hosts.add(host)

            http_response = traffic.getResponse()
            if http_response:
                self.get_words(http_response)

        self.display_wordlist()
        return

    def get_words(self, http_response):
        headers, body = http_response.tostring().split("\r\n\r\n", 1)

        # descartamos respuestas que no sean de tipo texto
        if headers.lower().find("content-type: text") == -1:
            return

        tag_stripper = TagStripper()
        page_text = tag_stripper.strip(body)

        for word in WORD_PATTERN.findall(page_text):
            if len(word) <= MAX_WORD_LENGTH:
                self.wordlist.add(word.lower())
        return

    def mangle(self, word):
        year = datetime.now().year
        suffixes = ["", "1", "!", str(year)]
        mangled = []

        for candidate in (word, word.capitalize()):
            for suffix in suffixes:
                mangled.append("%s%s" % (candidate, suffix))

        return mangled

    def display_wordlist(self):
        print("#!comment: BHP Wordlist for site(s) %s" % ", ".join(self.hosts))
        for word in sorted(self.wordlist):
            for password in self.mangle(word):
                print(password)
        return

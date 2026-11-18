"""Bounded loopback listeners for the synthetic Discord pilot."""
from __future__ import annotations

import socket
from socketserver import ThreadingMixIn
from threading import BoundedSemaphore, Timer
from time import monotonic
from wsgiref.simple_server import WSGIServer, make_server

from .server import InteractionApp, QuietRequestHandler


class _Errors:
    def write(self, text):
        pass

    def flush(self):
        pass


class PilotHandler(QuietRequestHandler):
    def get_stderr(self):
        return _Errors()

    def _deadline(self):
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def handle(self):
        timer = Timer(self.server.deadline, self._deadline)
        timer.daemon = True
        timer.start()
        try:
            super().handle()
        finally:
            timer.cancel()

    def parse_request(self):
        if not super().parse_request():
            return False
        lengths = self.headers.get_all("Content-Length", [])
        if (self.headers.get_all("Transfer-Encoding") or len(lengths) > 1
                or (lengths and not lengths[0].isascii())
                or (lengths and not lengths[0].isdecimal())):
            self.send_error(400)
            return False
        return True


class PilotServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    deadline = 2.0

    def __init__(self, *args, **kwargs):
        self.capacity = BoundedSemaphore(8)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.capacity.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.capacity.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.capacity.release()

    def handle_error(self, request, client_address):
        pass


def listener(app: InteractionApp, port: int, *, downloads: bool, report):
    """Expose a single route class on each listener and log only receipt metrics."""
    def route(environ, start_response):
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD")
        started = monotonic()

        def measured(status, headers, exc_info=None):
            report("http", surface="download" if downloads else "discord",
                   status=int(status.split()[0]), ms=round(1000 * (monotonic() - started), 1))
            return start_response(status, headers, exc_info)

        permitted = (path.startswith("/private/resumes/") and method == "GET" if downloads
                     else path == "/interactions" and method == "POST" and not environ.get("QUERY_STRING"))
        if permitted:
            return app(environ, measured)
        measured("404 Not Found", [("Cache-Control", "no-store"), ("Content-Length", "0")])
        return [b""]

    instance = make_server("127.0.0.1", port, route, server_class=PilotServer, handler_class=PilotHandler)
    instance.deadline = 5.0 if downloads else 2.0
    return instance

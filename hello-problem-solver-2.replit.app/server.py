from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from pathlib import Path

ROOT = Path(__file__).parent


class SpaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.proxy_request()
        requested = ROOT / self.path.lstrip("/").split("?", 1)[0]
        if not requested.exists() and "." not in requested.name:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self.proxy_request()
        return super().do_POST()

    def proxy_request(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        target = "https://hello-problem-solver-2.replit.app" + self.path
        headers = {key: value for key, value in self.headers.items() if key.lower() != "host"}
        try:
            with urlopen(Request(target, data=body, headers=headers, method=self.command)) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in {"transfer-encoding", "connection", "content-encoding"}:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
        except Exception as error:
            self.send_error(502, str(error))


ThreadingHTTPServer(("", 8000), SpaHandler).serve_forever()

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json

ROOT = Path(__file__).parent


class RocketHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.handle_api_get()
        # توجيه الملفات المفقودة إلى index.html لتشتغل مسارات اللعبة بسلاسة
        requested = ROOT / self.path.lstrip("/").split("?", 1)[0]
        if not requested.exists() and not self.path.startswith("/assets/"):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self.handle_api_post()
        return super().do_POST()

    def handle_api_get(self):
        request_path = self.path.split("?", 1)[0].rstrip("/")
        
        if "gifts" in request_path:
            payload = json.dumps([{
                "id": "vice-cream-demo",
                "name": "Vice Cream",
                "model_name": "Vice Cream",
                "price": 4.08,
                "price_ton": "4.08",
                "priceTon": 4.08,
                "status": "available",
                "imageUrl": "https://cdn.changes.tg/gifts/models/vice-cream.webp",
                "backdropName": None
            }]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if "wallet/balance" in request_path:
            payload = b'{"availableTON":"1000","balanceTON":"1000","starsBalance":"0"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        # الرد الافتراضي لأي طلب API آخر لتجنب حصول خطأ 502
        payload = b'{"status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def handle_api_post(self):
        # استقبال طلبات الـ POST محلياً والرد بنجاح لتجنب أي توقف في اللعبة
        payload = b'{"success": true, "status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    port = 8001
    print(f"🚀 Local Rocket Server running on port {port}...")
    ThreadingHTTPServer(("0.0.0.0", port), RocketHandler).serve_forever()
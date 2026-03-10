# mock_backend_simple.py
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "backend_simple.log")

def log(msg):
    line = f"{datetime.utcnow().isoformat()} {msg}\n"
    print(line, end="")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

class SimpleHandler(BaseHTTPRequestHandler):
    def _send_ok(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(body.decode('utf-8')) if body else None
        except Exception as e:
            payload = None
        if parsed.path == "/api/v1/metrics":
            log(f"[METRICS] From {self.client_address[0]} path={parsed.path} payload={payload}")
            self._send_ok()
        elif parsed.path == "/api/v1/heartbeat":
            log(f"[HEARTBEAT] From {self.client_address[0]} payload={payload}")
            self._send_ok()
        else:
            # unknown path
            log(f"[UNKNOWN POST] path={parsed.path} payload={payload}")
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # override to avoid printing default messages
        return

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    server = HTTPServer((host, port), SimpleHandler)
    print(f"Mock backend running at http://{host}:{port}/ (log: {LOG_FILE})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
        server.server_close()
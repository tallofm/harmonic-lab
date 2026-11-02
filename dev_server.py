"""
Local development server for HarmonicLab.
Serves static UI assets from public/ and dispatches /api requests to api/index.py.
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from api.index import handler as ApiHandler


class DevServerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(BASE_DIR, "public"), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api"):
            return ApiHandler.do_GET(self)
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api"):
            return ApiHandler.do_POST(self)
        return super().do_POST()

    def do_OPTIONS(self):
        if self.path.startswith("/api"):
            return ApiHandler.do_OPTIONS(self)
        return super().do_OPTIONS()

    def _send_json(self, data, status=200):
        return ApiHandler._send_json(self, data, status)

    def _send_problem(self, status, title, detail, error_type="bad-request"):
        return ApiHandler._send_problem(self, status, title, detail, error_type)


def run(port: int = 3000):
    server = HTTPServer(("0.0.0.0", port), DevServerHandler)
    print(f"HarmonicLab dev server running at http://localhost:{port}")
    print("Serving public/ static UI and routing /api to serverless handler.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run(port)

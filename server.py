#!/usr/bin/env python3
"""
Local proxy server for Local LLM Chat with AI Guard.
Serves chat.html and proxies requests to Trend Micro AI Guard API (bypassing browser CORS).

Usage: python3 server.py
Then open: http://localhost:3000
"""

import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"  {self.address_string()} {format % args}")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/chat.html"):
            try:
                with open("chat.html", "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "chat.html not found")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/proxy/guard":
            self._proxy_guard()
        else:
            self.send_error(404)

    def _proxy_guard(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        api_key  = self.headers.get("X-Guard-Key", "")
        region   = self.headers.get("X-Guard-Region", "sg")
        app_name = self.headers.get("X-Guard-AppName", "AI Guard")

        base = (
            "https://api.xdr.trendmicro.com"
            if region == "us"
            else f"https://api.{region}.xdr.trendmicro.com"
        )
        url = f"{base}/v3.0/aiSecurity/applyGuardrails"

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("TMV1-Application-Name", app_name)
        req.add_header("Content-Type", "application/json")
        req.add_header("Prefer", "return=representation")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = resp.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(result)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(502)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


if __name__ == "__main__":
    port = 3000
    server = HTTPServer(("localhost", port), Handler)
    print(f"\n  Local LLM Chat proxy running")
    print(f"  Open: http://localhost:{port}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")

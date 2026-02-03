"""Manual smoke script for verifying the HttpServerProcess lifecycle.

Run this script with `python3 tests/smoke_http_server.py` to exercise the start/stop
path that App uses for its subprocess management."""

import os
import socket
import sys
import tempfile
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server_process import HttpServerProcess


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


def main():
    port = find_free_port()
    cmd = [sys.executable, "-m", "http.server", str(port)]
    server = HttpServerProcess()
    print(f"Starting python http.server on port {port}")
    proc = server.start(cmd, cwd=tempfile.gettempdir())
    try:
        time.sleep(1)
        if not server.is_running():
            raise RuntimeError("server did not start")
        print("Server started; stopping now")
    finally:
        if server.is_running():
            server.stop()
        else:
            server.release(proc)
        print("Server stopped")


if __name__ == "__main__":
    main()

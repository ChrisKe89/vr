"""Shared helpers for running the http-server subprocess."""

import os
import subprocess


def build_http_server_command(port, cert_path, key_path, npx_cmd="npx"):
    return [
        npx_cmd,
        "-y",
        "http-server",
        "-c1",
        "--gzip",
        "-p",
        port,
        "--cors",
        "--ssl",
        "--cert",
        cert_path,
        "--key",
        key_path,
        "-a",
        "0.0.0.0",
    ]


class HttpServerProcess:
    def __init__(self):
        self.proc = None

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, cmd, cwd, creationflags=0, startupinfo=None, capture_output=True):
        if self.is_running():
            raise RuntimeError("http server already running")
        stdout = subprocess.PIPE if capture_output else None
        stderr = subprocess.STDOUT if capture_output else None
        self.proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=stdout,
            stderr=stderr,
            text=True,
            shell=False,
            creationflags=creationflags,
            startupinfo=startupinfo,
        )
        return self.proc

    def stop(self, timeout=4):
        proc = self.proc
        if not proc or proc.poll() is not None:
            return False
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                proc.wait(timeout=timeout)
            else:
                proc.terminate()
                proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        finally:
            self.proc = None
        return True

    def release(self, proc):
        if self.proc is proc:
            self.proc = None

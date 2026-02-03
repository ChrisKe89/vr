import os
import socket
import subprocess
import threading
import queue
import time
import ipaddress
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = r"C:\C_DRIVE_PROJECT_WIP"

class App:
    def __init__(self, root):
        self.root = root
        self.proc = None
        self.reader_thread = None
        self.output_queue = queue.Queue()
        self.current_ip = ""
        self.selected_name = ""
        self.port_var = tk.StringVar(value="8443")
        self.status_var = tk.StringVar(value="")
        self.build_ui()
        self.apply_style()
        self.refresh_ip()
        self.load_versions()

    def build_ui(self):
        self.root.title("VR Training Server Helper")
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Select Version").pack(side="left")
        ttk.Label(top, text=f"(base: {BASE_DIR})").pack(side="left", padx=8)

        list_frame = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        list_frame.pack(fill="both", expand=True)
        self.lb = tk.Listbox(list_frame, height=10, activestyle="dotbox", font=("Segoe UI", 11))
        ysb = ttk.Scrollbar(list_frame, orient="vertical", command=self.lb.yview)
        self.lb.configure(yscrollcommand=ysb.set)
        self.lb.bind("<Double-Button-1>", self.on_double)
        self.lb.bind("<<ListboxSelect>>", self.on_select)
        self.lb.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        ribbon = ttk.Frame(self.root, padding=8)
        ribbon.pack(fill="x")
        self.btn_install = ttk.Button(ribbon, text="Install http‑server", command=self.install_http_server_cmd)
        self.btn_install.grid(row=0, column=0, padx=(0, 6))
        ttk.Label(ribbon, text="Port").grid(row=0, column=1, padx=(6, 2))
        self.port_entry = ttk.Entry(ribbon, textvariable=self.port_var, width=8, justify="center")
        self.port_entry.grid(row=0, column=2, padx=(0, 10))
        self.btn_start = tk.Button(ribbon, text="Start Server", command=self.start_server, bg="#2E7D32", fg="white", activebackground="#1B5E20", activeforeground="white", bd=0, padx=18, pady=6, font=("Segoe UI Semibold", 10))
        self.btn_start.grid(row=0, column=3, padx=(0, 6))
        self.btn_stop = ttk.Button(ribbon, text="Stop Server", command=self.stop_server)
        self.btn_stop.grid(row=0, column=4, padx=6)
        self.btn_refresh_ip = ttk.Button(ribbon, text="Refresh IP", command=self.refresh_ip)
        self.btn_refresh_ip.grid(row=0, column=5, padx=6)
        self.btn_launch = ttk.Button(ribbon, text="Launch Browser", command=self.launch_browser)
        self.btn_launch.grid(row=0, column=6, padx=6)
        ribbon.columnconfigure(7, weight=1)

        status = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        status.pack(fill="x")
        ttk.Label(status, text="IPv4:").pack(side="left")
        self.ip_label = ttk.Label(status, text="detecting…")
        self.ip_label.pack(side="left", padx=(4, 12))
        ttk.Label(status, textvariable=self.status_var, foreground="#006400").pack(side="left")

        log = ttk.LabelFrame(self.root, text="Log", padding=8)
        log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log_text = tk.Text(log, height=10, wrap="word", font=("Consolas", 10))
        y = ttk.Scrollbar(log, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscroll=y.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        y.pack(side="right", fill="y")
        self.root.after(120, self.drain_output)

    def apply_style(self):
        style = ttk.Style()
        names = style.theme_names()
        if "vista" in names:
            style.theme_use("vista")
        elif "xpnative" in names:
            style.theme_use("xpnative")
        style.configure("TButton", padding=(12, 8), font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TLabelframe.Label", font=("Segoe UI Semibold", 10))

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")

    def load_versions(self):
        self.lb.delete(0, "end")
        if not os.path.isdir(BASE_DIR):
            self.log(f"Base not found: {BASE_DIR}")
            return
        try:
            entries = sorted([e for e in os.listdir(BASE_DIR)], key=lambda x: x.lower())
        except Exception as e:
            self.log(str(e))
            return
        for name in entries:
            full = os.path.join(BASE_DIR, name)
            if os.path.isdir(full):
                self.lb.insert("end", name)

    def on_double(self, event):
        self.on_select(event)
        self.start_server()

    def on_select(self, event):
        sel = self.lb.curselection()
        if not sel:
            return
        self.selected_name = self.lb.get(sel[0])
        self.log(f"Selected: {self.selected_name}")

    def install_http_server_cmd(self):
        cmd = (
            'start "" cmd /c '
            '"title Installing http-server && '
            'echo Installing http-server globally... && echo. && '
            'npm install -g http-server && echo. && '
            'echo Completed. Press any key to close. && '
            'pause > nul"'
        )
        try:
            subprocess.Popen(cmd, shell=True)
            self.log("Opened a Command Prompt to install http-server.")
        except Exception as e:
            self.log(str(e))


    def get_private_ipv4(self):
        try:
            out = subprocess.check_output(["ipconfig"], text=True, encoding="utf-8", errors="ignore")
            candidates = []
            for raw in out.splitlines():
                line = raw.strip()
                if "IPv4" in line and ":" in line:
                    ip = line.split(":")[-1].strip()
                    try:
                        ip_obj = ipaddress.ip_address(ip)
                        if ip_obj.version == 4 and ip_obj.is_private and not ip_obj.is_loopback:
                            candidates.append(ip)
                    except Exception:
                        pass
            if candidates:
                return candidates[0]
        except Exception:
            pass
        try:
            host = socket.gethostname()
            ips = socket.getaddrinfo(host, None, socket.AF_INET)
            for info in ips:
                ip = info[4][0]
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private and not ip_obj.is_loopback:
                    return ip
        except Exception:
            pass
        return "127.0.0.1"

    def refresh_ip(self):
        self.current_ip = self.get_private_ipv4()
        self.ip_label.config(text=self.current_ip)
        self.log(f"IP detected: {self.current_ip}")

    def start_server(self):
        if not self.selected_name:
            messagebox.showerror("Error", "Select a version folder.")
            return
        serve_dir = os.path.join(BASE_DIR, self.selected_name, "WebVRTrainingApp")
        if not os.path.isdir(serve_dir):
            self.log(f"WebVRTrainingApp not found under: {self.selected_name}")
            return
        if self.proc and self.proc.poll() is None:
            self.log("Server already running.")
            return
        port = self.port_var.get().strip() or "8443"
        if not port.isdigit():
            messagebox.showerror("Error", "Port must be numeric.")
            return
        cert_path = os.path.join(serve_dir, "server.cert")
        key_path = os.path.join(serve_dir, "server.key")
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            self.log("server.cert or server.key not found in WebVRTrainingApp.")
            return
        cmd = ["npx", "-y", "http-server", "-c1", "--gzip", "-p", port, "--cors", "--ssl", "--cert", cert_path, "--key", key_path, "-a", "0.0.0.0"]
        self.log("Starting: " + " ".join(['"{}"'.format(c) if " " in str(c) else str(c) for c in cmd]))
        creationflags = 0x08000000 if os.name == "nt" else 0
        try:
            self.proc = subprocess.Popen(cmd, cwd=serve_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False, creationflags=creationflags)
        except FileNotFoundError:
            self.log("http-server not found. Use Install http-server first.")
            return
        self.reader_thread = threading.Thread(target=self.read_output, daemon=True)
        self.reader_thread.start()
        self.status_var.set("Server running")

    def read_output(self):
        if not self.proc or not self.proc.stdout:
            return
        for line in self.proc.stdout:
            self.output_queue.put(line.rstrip())
        code = self.proc.wait()
        self.output_queue.put(f"http-server exited with code {code}")
        self.status_var.set("")

    def stop_server(self):
        if self.proc and self.proc.poll() is None:
            self.log("Stopping server...")
            try:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
            except Exception:
                pass
            self.status_var.set("")
        else:
            self.log("Server is not running.")

    def launch_browser(self):
        ip = self.current_ip or "127.0.0.1"
        port = self.port_var.get().strip() or "8443"
        url = f"https://{ip}:{port}"
        self.log(f"Launching: {url}")
        webbrowser.open_new_tab(url)

    def drain_output(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.log(line)
        except queue.Empty:
            pass
        self.root.after(120, self.drain_output)

def main():
    root = tk.Tk()
    app = App(root)
    root.geometry("920x600")
    root.mainloop()

if __name__ == "__main__":
    main()
import os
import socket
import subprocess
import threading
import queue
import time
import ipaddress
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import shutil

from server_process import HttpServerProcess, build_http_server_command

BASE_DIR = r"C:\C_DRIVE_PROJECT_WIP"
ACTION_BUTTON_WIDTH = 12


class App:
    def __init__(self, root):
        self.root = root
        self.server_process = HttpServerProcess()
        self.reader_thread = None
        self.output_queue = queue.Queue()
        self.current_ip = ""
        self.selected_name = ""
        self.version_map = {}
        self.base_dir_var = tk.StringVar(value=BASE_DIR)
        self.port_var = tk.StringVar(value="8443")
        self.status_var = tk.StringVar(value="")
        self.stopping = False
        self.build_ui()
        self.apply_style()
        self.refresh_ip()
        self.load_versions()

    def build_ui(self):
        self.root.title("VR Training Server Helper")
        self.root.minsize(1020, 720)
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(
            header,
            text="VR Training Server Helper",
            font=("Segoe UI Semibold", 18),
        ).pack(side="left")
        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=3)
        body.grid_rowconfigure(1, weight=1)

        version_frame = ttk.LabelFrame(body, text="Available Versions", padding=8)
        version_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        version_frame.grid_rowconfigure(0, weight=1)
        version_frame.grid_columnconfigure(0, weight=1)

        self.lb = tk.Listbox(
            version_frame,
            activestyle="dotbox",
            font=("Segoe UI", 9),
            selectbackground="#006db6",
            selectforeground="white",
        )
        ysb = ttk.Scrollbar(version_frame, orient="vertical", command=self.lb.yview)
        self.lb.configure(yscrollcommand=ysb.set)
        self.lb.bind("<Double-Button-1>", self.on_double)
        self.lb.bind("<<ListboxSelect>>", self.on_select)
        self.lb.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        ysb.grid(row=0, column=1, sticky="ns")

        control_frame = ttk.LabelFrame(body, text="Server Control", padding=12)
        control_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        control_frame.grid_columnconfigure(0, weight=1)

        action_row = ttk.Frame(control_frame)
        action_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)

        self.btn_start = ttk.Button(
            action_row,
            text="Start Server",
            command=self.start_server,
            width=ACTION_BUTTON_WIDTH,
        )
        self.btn_start.grid(row=0, column=0, padx=4, pady=(0, 6), sticky="ew")
        self.btn_stop = ttk.Button(
            action_row,
            text="Stop Server",
            command=self.stop_server,
            width=ACTION_BUTTON_WIDTH,
        )
        self.btn_stop.grid(row=0, column=1, padx=4, pady=(0, 6), sticky="ew")
        self.btn_refresh_ip = ttk.Button(
            action_row,
            text="Refresh IP",
            command=self.refresh_ip,
            width=ACTION_BUTTON_WIDTH,
        )
        self.btn_refresh_ip.grid(row=1, column=0, padx=4, sticky="ew")
        self.btn_launch = ttk.Button(
            action_row,
            text="Launch Browser",
            command=self.launch_browser,
            width=ACTION_BUTTON_WIDTH,
        )
        self.btn_launch.grid(row=1, column=1, padx=4, sticky="ew")
        status_holder = ttk.Frame(control_frame)
        status_holder.grid(row=1, column=0, sticky="ew", pady=(0, 8), padx=4)
        status_holder.grid_columnconfigure(0, weight=1)
        status_holder.grid_columnconfigure(1, weight=1)

        ipv4_frame = ttk.LabelFrame(status_holder, text="IPv4", padding=(8, 4))
        ipv4_frame.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.ip_label = ttk.Label(ipv4_frame, text="detecting…", font=("Segoe UI", 10))
        self.ip_label.pack(side="left")

        port_frame = ttk.LabelFrame(status_holder, text="Port", padding=(8, 4))
        port_frame.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.port_entry = ttk.Entry(
            port_frame, textvariable=self.port_var, width=10, justify="center"
        )
        self.port_entry.pack(side="left")

        location_frame = ttk.LabelFrame(
            control_frame, text="Current Location", padding=8
        )
        location_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        location_frame.grid_columnconfigure(0, weight=1)
        self.base_dir_entry = ttk.Entry(
            location_frame, textvariable=self.base_dir_var, state="readonly"
        )
        self.base_dir_entry.grid(row=0, column=0, sticky="ew")

        install_row = ttk.Frame(control_frame)
        install_row.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        install_row.grid_columnconfigure(0, weight=1)
        self.btn_browse = ttk.Button(
            install_row,
            text="Browse other locations",
            command=self.browse_base_dir,
            width=ACTION_BUTTON_WIDTH,
        )
        self.btn_browse.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.btn_install = ttk.Button(
            install_row,
            text="Install Env Variables",
            command=self.install_http_server_cmd,
            width=ACTION_BUTTON_WIDTH,
        )
        self.btn_install.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.btn_refresh_versions = ttk.Button(
            install_row,
            text="Refresh Available Versions",
            command=self.refresh_versions,
            width=ACTION_BUTTON_WIDTH,
        )
        self.btn_refresh_versions.grid(row=2, column=0, sticky="ew")

        status_row = ttk.Frame(control_frame)
        status_row.grid(row=4, column=0, sticky="ew", pady=(4, 0))
        status_row.grid_columnconfigure(0, weight=1)
        ttk.Label(
            status_row,
            textvariable=self.status_var,
            foreground="#006400",
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, sticky="w")

        log_frame = ttk.LabelFrame(body, text="Log", padding=10)
        log_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
        )
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame,
            height=12,
            wrap="word",
            font=("Consolas", 10),
            bd=0,
            relief="flat",
            background="#111",
            foreground="#f1f1f1",
            insertbackground="#f1f1f1",
        )
        y = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=y.set)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        y.grid(row=0, column=1, sticky="ns")

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
        self.version_map = {}
        base_dir = self.base_dir_var.get().strip() or BASE_DIR
        if not os.path.isdir(base_dir):
            self.log(f"Base not found: {base_dir}")
            return
        self.log("Scanning for WebVRTrainingApp folders...")
        try:
            parents = set()
            for root, dirnames, _ in os.walk(base_dir):
                if "WebVRTrainingApp" in dirnames:
                    parents.add(root)
                    # Skip walking deeper inside the app folder.
                    dirnames.remove("WebVRTrainingApp")
        except Exception as e:
            self.log(str(e))
            return

        if not parents:
            self.log("No WebVRTrainingApp folders found under base.")
            return

        rel_paths = []
        for parent in parents:
            rel = os.path.relpath(parent, base_dir)
            if rel == ".":
                display = "<root>"
            else:
                display = rel
            self.version_map[display] = rel
            rel_paths.append(display)

        for display in sorted(rel_paths, key=lambda x: x.lower()):
            self.lb.insert("end", display)
        self.log(f"Found {len(rel_paths)} WebVRTrainingApp location(s).")

    def on_double(self, event):
        self.on_select(event)
        self.start_server()

    def on_select(self, event):
        sel = self.lb.curselection()
        if not sel:
            return
        display = self.lb.get(sel[0])
        self.selected_name = self.version_map.get(display, display)
        self.log(f"Selected: {self.selected_name}")

    def refresh_versions(self):
        self.load_versions()
        self.log("Available versions refreshed.")

    def browse_base_dir(self):
        start_dir = self.base_dir_var.get().strip() or BASE_DIR
        selected = filedialog.askdirectory(initialdir=start_dir)
        if selected:
            self.base_dir_var.set(selected)
            self.log(f"Base folder set to: {selected}")
            self.load_versions()

    def install_http_server_cmd(self):
        cmd = (
            'start "" cmd /c '
            '"title Installing http-server && '
            "echo Installing http-server globally... && echo. && "
            "npm install -g http-server && echo. && "
            "echo Completed. Press any key to close. && "
            'pause > nul"'
        )
        try:
            subprocess.Popen(cmd, shell=True)
            self.log("Opened a Command Prompt to install http-server.")
        except Exception as e:
            self.log(str(e))

    def get_private_ipv4(self):
        try:
            out = subprocess.check_output(
                ["ipconfig"], text=True, encoding="utf-8", errors="ignore"
            )
            candidates = []
            for raw in out.splitlines():
                line = raw.strip()
                if "IPv4" in line and ":" in line:
                    ip = line.split(":")[-1].strip()
                    try:
                        ip_obj = ipaddress.ip_address(ip)
                        if (
                            ip_obj.version == 4
                            and ip_obj.is_private
                            and not ip_obj.is_loopback
                        ):
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
        base_dir = self.base_dir_var.get().strip() or BASE_DIR
        serve_dir = os.path.join(base_dir, self.selected_name, "WebVRTrainingApp")
        if not os.path.isdir(serve_dir):
            self.log(f"WebVRTrainingApp not found under: {self.selected_name}")
            return
        if self.server_process.is_running():
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
        npx_cmd = "npx"
        if os.name == "nt":
            npx_cmd = shutil.which("npx.cmd") or shutil.which("npx")
            if not npx_cmd:
                messagebox.showerror(
                    "Error",
                    "npx not found. Install Node.js or add it to PATH, then try again.",
                )
                return
        cmd = build_http_server_command(port, cert_path, key_path, npx_cmd=npx_cmd)
        display_cmd = build_http_server_command(
            port, "server.cert", "server.key", npx_cmd="npx"
        )
        log_cmd = " ".join(
            ['"{}"'.format(c) if " " in str(c) else str(c) for c in display_cmd]
        )
        creationflags = 0x08000000 if os.name == "nt" else 0
        capture_output = True
        if os.name == "nt":
            # Use cmd.exe to run the .cmd shim directly without list2cmdline
            # to avoid quoting edge cases that can surface as "unknown command".
            cmd = ["cmd.exe", "/c", *cmd]
            log_cmd = f'(cwd "{serve_dir}") {log_cmd}'
            creationflags = subprocess.CREATE_NO_WINDOW
        self.log(f"Starting: {log_cmd}")
        try:
            proc = self.server_process.start(
                cmd,
                cwd=serve_dir,
                creationflags=creationflags,
                capture_output=capture_output,
            )
        except FileNotFoundError:
            self.log("http-server not found. Use Install http-server first.")
            return
        except RuntimeError as exc:
            self.log(str(exc))
            return
        if capture_output:
            self.reader_thread = threading.Thread(
                target=self.read_output, args=(proc,), daemon=True
            )
            self.reader_thread.start()
        else:
            self.reader_thread = threading.Thread(
                target=self.wait_for_exit, args=(proc,), daemon=True
            )
            self.reader_thread.start()
        self.status_var.set("Server running")

    def read_output(self, proc):
        if not proc or not proc.stdout:
            return
        for line in proc.stdout:
            self.output_queue.put(line.rstrip())
        code = proc.wait()
        was_stopping = self.stopping
        self.stopping = False
        if not was_stopping:
            self.output_queue.put(f"http-server exited with code {code}")
        self.server_process.release(proc)
        try:
            self.root.after(0, lambda: self.status_var.set(""))
        except tk.TclError:
            pass

    def wait_for_exit(self, proc):
        if not proc:
            return
        code = proc.wait()
        was_stopping = self.stopping
        self.stopping = False
        self.server_process.release(proc)
        try:
            self.root.after(0, lambda: self.status_var.set(""))
        except tk.TclError:
            pass
        if not was_stopping:
            if code == 0:
                self.output_queue.put("http-server exited.")
            else:
                self.output_queue.put(f"http-server exited with code {code}.")

    def stop_server(self):
        if self.server_process.is_running():
            self.log("Stopping server...")
            self.stopping = True
            stopped = self.server_process.stop()
            if stopped:
                self.status_var.set("")
                self.log("Server Stopped.")
            else:
                self.stopping = False
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

    def handle_close():
        app.stop_server()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", handle_close)
    root.geometry("1020x720")
    root.mainloop()


if __name__ == "__main__":
    main()

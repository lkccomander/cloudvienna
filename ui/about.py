import json
import os
import platform
import re
import socket
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from version import __version__
from i18n import t


def build(tab_about):
   # ttk.Label(tab_about, text="STUDENTS TAB OK", foreground="green").grid(
    #    row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    tab_about.grid_rowconfigure(2, weight=1)
    tab_about.grid_columnconfigure(0, weight=1)

    logo_frame = ttk.LabelFrame(tab_about, text=t("label.logo"), padding=10)
    logo_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))

    logo_label = ttk.Label(logo_frame)
    logo_label.grid(row=0, column=0, sticky="w")

    def _settings_path():
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "app_settings.json")

    def _load_settings():
        try:
            with open(_settings_path(), "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_settings(data):
        with open(_settings_path(), "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)

    def _load_logo(path):
        try:
            from PIL import Image, ImageTk
        except Exception:
            messagebox.showerror(t("label.logo"), t("label.logo_pillow_missing"))
            return

        if not path or not os.path.exists(path):
            return

        img = Image.open(path)
        img.thumbnail((320, 140))
        photo = ImageTk.PhotoImage(img)
        logo_label.configure(image=photo)
        logo_label.image = photo

    def choose_logo():
        path = filedialog.askopenfilename(
            title=t("label.choose_logo"),
            filetypes=[(t("label.jpg_files"), "*.jpg;*.jpeg")],
        )
        if not path:
            return
        settings = _load_settings()
        settings["logo_path"] = path
        _save_settings(settings)
        _load_logo(path)

    ttk.Button(logo_frame, text=t("button.choose_logo"), command=choose_logo).grid(
        row=0, column=1, sticky="e", padx=(12, 0)
    )
    logo_frame.columnconfigure(0, weight=1)

    settings = _load_settings()
    _load_logo(settings.get("logo_path"))

    about_frame = ttk.LabelFrame(tab_about, text=t("label.system_config"), padding=10)
    about_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(10, 6))

    unknown_text = t("label.unknown")

    about_values = {
        "version": tk.StringVar(),
        "hostname": tk.StringVar(),
        "ip": tk.StringVar(),
        "dns": tk.StringVar(),
        "gateway": tk.StringVar(),
        "os": tk.StringVar(),
    }

    ttk.Label(about_frame, text=t("label.software_version")).grid(row=0, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["version"]).grid(row=0, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text=t("label.hostname")).grid(row=1, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["hostname"]).grid(row=1, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text=t("label.ip_address")).grid(row=2, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["ip"]).grid(row=2, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text=t("label.dns_servers")).grid(row=3, column=0, sticky="nw", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["dns"], justify="left").grid(row=3, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text=t("label.default_gateway")).grid(row=4, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["gateway"]).grid(row=4, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text=t("label.operating_system")).grid(row=5, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["os"]).grid(row=5, column=1, sticky="w", padx=5, pady=4)

    about_frame.columnconfigure(1, weight=1)

    def _parse_windows_network_config(output):
        ips = []
        gateways = []
        dns_servers = []

        for line in output.splitlines():
            ip_match = re.search(r"IPv4 Address[^:]*:\s*([0-9.]+)", line)
            if ip_match:
                ips.append(ip_match.group(1))
            gw_match = re.search(r"Default Gateway[^:]*:\s*([0-9.]+)", line)
            if gw_match:
                gateways.append(gw_match.group(1))

        lines = output.splitlines()
        for idx, line in enumerate(lines):
            if "DNS Servers" in line:
                dns_servers.extend(re.findall(r"([0-9.]+)", line))
                j = idx + 1
                while j < len(lines) and (lines[j].startswith(" ") or lines[j].startswith("\t")):
                    dns_servers.extend(re.findall(r"([0-9.]+)", lines[j]))
                    j += 1

        def _filter_ips(values):
            return [v for v in values if v and not v.startswith("169.254") and v != "0.0.0.0"]

        ips = _filter_ips(ips)
        gateways = _filter_ips(gateways)
        dns_servers = _filter_ips(dns_servers)

        return {
            "ip": ips[0] if ips else unknown_text,
            "gateway": gateways[0] if gateways else unknown_text,
            "dns": ", ".join(dns_servers) if dns_servers else unknown_text,
        }

    def _collect_network_info():
        info = {
            "ip": unknown_text,
            "dns": unknown_text,
            "gateway": unknown_text,
        }

        if os.name == "nt":
            try:
                output = subprocess.check_output(["ipconfig", "/all"], text=True, errors="ignore")
                info.update(_parse_windows_network_config(output))
            except Exception:
                pass
            return info

        try:
            addr_info = socket.getaddrinfo(socket.gethostname(), None)
            ipv4s = {item[4][0] for item in addr_info if item[0] == socket.AF_INET}
            ipv4s = {ip for ip in ipv4s if not ip.startswith("127.")}
            if ipv4s:
                info["ip"] = sorted(ipv4s)[0]
        except Exception:
            pass

        try:
            with open("/etc/resolv.conf", "r", encoding="utf-8") as handle:
                servers = []
                for line in handle:
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) > 1:
                            servers.append(parts[1])
                if servers:
                    info["dns"] = ", ".join(servers)
        except Exception:
            pass

        try:
            route_output = subprocess.check_output(["ip", "route"], text=True, errors="ignore")
            for line in route_output.splitlines():
                if line.startswith("default "):
                    parts = line.split()
                    if "via" in parts:
                        info["gateway"] = parts[parts.index("via") + 1]
                    break
        except Exception:
            pass

        return info

    def refresh_about_panel():
        net = _collect_network_info()
        about_values["version"].set(__version__)
        about_values["hostname"].set(socket.gethostname())
        about_values["ip"].set(net.get("ip", "Unknown"))
        about_values["dns"].set(net.get("dns", "Unknown"))
        about_values["gateway"].set(net.get("gateway", "Unknown"))
        about_values["os"].set(f"{platform.system()} {platform.release()}")

    ttk.Button(about_frame, text=t("button.refresh"), command=refresh_about_panel) \
        .grid(row=6, column=0, columnspan=2, pady=8, sticky="w")

    logs_frame = ttk.LabelFrame(tab_about, text=t("label.app_log"), padding=10)
    logs_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))

    log_text = tk.Text(logs_frame, height=10, wrap="none", font=("Consolas", 9))
    log_text.grid(row=0, column=0, columnspan=2, sticky="nsew")

    log_scroll_y = ttk.Scrollbar(logs_frame, orient="vertical", command=log_text.yview)
    log_text.configure(yscrollcommand=log_scroll_y.set)
    log_scroll_y.grid(row=0, column=2, sticky="ns")

    log_scroll_x = ttk.Scrollbar(logs_frame, orient="horizontal", command=log_text.xview)
    log_text.configure(xscrollcommand=log_scroll_x.set)
    log_scroll_x.grid(row=1, column=0, columnspan=2, sticky="ew")

    logs_frame.columnconfigure(0, weight=1)
    logs_frame.rowconfigure(0, weight=1)

    def _log_path():
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "app.log")

    def refresh_logs():
        path = _log_path()
        if not os.path.exists(path):
            content = t("label.no_log")
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                lines = handle.readlines()
                content = "".join(reversed(lines))
        log_text.config(state="normal")
        log_text.delete("1.0", tk.END)
        log_text.insert(tk.END, content)
        log_text.config(state="disabled")

    ttk.Button(logs_frame, text=t("button.refresh_logs"), command=refresh_logs).grid(
        row=2, column=0, sticky="w", pady=(6, 0)
    )

    return {"refresh_about_panel": refresh_about_panel}

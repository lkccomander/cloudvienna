import os
import platform
import re
import socket
import subprocess
import tkinter as tk
from tkinter import ttk

from version import __version__


def build(tab_about):
   # ttk.Label(tab_about, text="STUDENTS TAB OK", foreground="green").grid(
    #    row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    about_frame = ttk.LabelFrame(tab_about, text="System Configuration", padding=10)
    about_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    tab_about.grid_rowconfigure(1, weight=1)
    tab_about.grid_columnconfigure(0, weight=1)

    about_values = {
        "version": tk.StringVar(),
        "hostname": tk.StringVar(),
        "ip": tk.StringVar(),
        "dns": tk.StringVar(),
        "gateway": tk.StringVar(),
        "os": tk.StringVar(),
    }

    ttk.Label(about_frame, text="Software Version").grid(row=0, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["version"]).grid(row=0, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text="Hostname").grid(row=1, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["hostname"]).grid(row=1, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text="IP Address").grid(row=2, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["ip"]).grid(row=2, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text="DNS Servers").grid(row=3, column=0, sticky="nw", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["dns"], justify="left").grid(row=3, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text="Default Gateway").grid(row=4, column=0, sticky="w", padx=5, pady=4)
    ttk.Label(about_frame, textvariable=about_values["gateway"]).grid(row=4, column=1, sticky="w", padx=5, pady=4)

    ttk.Label(about_frame, text="Operating System").grid(row=5, column=0, sticky="w", padx=5, pady=4)
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
            "ip": ips[0] if ips else "Unknown",
            "gateway": gateways[0] if gateways else "Unknown",
            "dns": ", ".join(dns_servers) if dns_servers else "Unknown",
        }

    def _collect_network_info():
        info = {
            "ip": "Unknown",
            "dns": "Unknown",
            "gateway": "Unknown",
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

    ttk.Button(about_frame, text="Refresh", command=refresh_about_panel) \
        .grid(row=6, column=0, columnspan=2, pady=8, sticky="w")

    return {"refresh_about_panel": refresh_about_panel}

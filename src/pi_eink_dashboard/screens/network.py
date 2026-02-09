"""Screen 3: WiFi details with clean key-value layout."""

import socket
import subprocess

import psutil

from ..composer import Composer
from .base import (
    BaseScreen,
    FONT_LABEL,
    FONT_BODY,
    CONTENT_TOP,
    MARGIN,
)

LINE_SPACING = 18


class NetworkScreen(BaseScreen):
    title = "NETWORK"

    def _get_ip(self) -> str:
        addrs = psutil.net_if_addrs()
        for iface in ("wlan0", "eth0"):
            if iface in addrs:
                for addr in addrs[iface]:
                    if addr.family == socket.AF_INET:
                        return addr.address
        return "No IP"

    def _get_ssid(self) -> str:
        try:
            return (
                subprocess.check_output(
                    ["/usr/sbin/iwgetid", "-r"], text=True, timeout=2
                ).strip()
                or "N/A"
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return "N/A"

    def _get_signal(self) -> str:
        try:
            out = subprocess.check_output(
                ["/usr/sbin/iwconfig", "wlan0"],
                text=True,
                timeout=2,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines():
                if "Signal level" in line:
                    part = line.split("Signal level=")[1].split()[0]
                    return f"{part} dBm"
        except (subprocess.SubprocessError, FileNotFoundError, IndexError):
            pass
        return "N/A"

    def _get_frequency(self) -> str:
        try:
            out = subprocess.check_output(
                ["iw", "dev", "wlan0", "link"],
                text=True,
                timeout=2,
                stderr=subprocess.DEVNULL,
            )
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("freq:"):
                    return line.split("freq:")[1].strip() + " MHz"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "N/A"

    def _get_gateway(self) -> str:
        try:
            out = subprocess.check_output(
                ["ip", "route", "show", "default"],
                text=True,
                timeout=2,
            )
            parts = out.strip().split()
            if len(parts) >= 3 and parts[0] == "default":
                return parts[2]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "N/A"

    def _get_dns(self) -> str:
        try:
            with open("/etc/resolv.conf") as f:
                for line in f:
                    if line.startswith("nameserver"):
                        return line.split()[1]
        except (OSError, IndexError):
            pass
        return "N/A"

    def _get_connections(self) -> int:
        try:
            return len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, OSError):
            return 0

    def draw(self, composer: Composer) -> None:
        y = CONTENT_TOP + 4

        ssid = self._get_ssid()
        composer.label_value(
            MARGIN, y, "SSID:", ssid,
            FONT_LABEL, FONT_BODY,
        )
        y += LINE_SPACING

        signal = self._get_signal()
        composer.label_value(
            MARGIN, y, "SIGNAL:", signal,
            FONT_LABEL, FONT_BODY,
        )
        y += LINE_SPACING

        freq = self._get_frequency()
        composer.label_value(
            MARGIN, y, "FREQ:", freq,
            FONT_LABEL, FONT_BODY,
        )
        y += LINE_SPACING

        ip = self._get_ip()
        composer.label_value(
            MARGIN, y, "IP:", ip,
            FONT_LABEL, FONT_BODY,
        )
        y += LINE_SPACING

        gateway = self._get_gateway()
        composer.label_value(
            MARGIN, y, "GW:", gateway,
            FONT_LABEL, FONT_BODY,
        )
        y += LINE_SPACING

        dns = self._get_dns()
        composer.label_value(
            MARGIN, y, "DNS:", dns,
            FONT_LABEL, FONT_BODY,
        )
        y += LINE_SPACING

        conns = self._get_connections()
        composer.label_value(
            MARGIN, y, "CONNS:", str(conns),
            FONT_LABEL, FONT_BODY,
        )

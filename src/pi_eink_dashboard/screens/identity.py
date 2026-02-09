"""Screen 2: Identity — large hostname + IP for headless Pi access."""

import socket
import subprocess

import psutil

from ..composer import Composer
from .base import (
    BaseScreen,
    FONT_LARGE,
    FONT_LABEL,
    FONT_BODY,
    CONTENT_TOP,
    MARGIN,
)


class IdentityScreen(BaseScreen):
    title = "IDENTITY"

    def _get_ip(self) -> str:
        addrs = psutil.net_if_addrs()
        for iface in ("wlan0", "eth0"):
            if iface in addrs:
                for addr in addrs[iface]:
                    if addr.family == socket.AF_INET:
                        return addr.address
        return "No IP"

    def _get_mac(self) -> str:
        addrs = psutil.net_if_addrs()
        if "wlan0" in addrs:
            for addr in addrs["wlan0"]:
                if addr.family == psutil.AF_LINK:
                    return addr.address
        return "N/A"

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

    def draw(self, composer: Composer) -> None:
        y = CONTENT_TOP + 4

        # Large hostname
        hostname = socket.gethostname()
        composer.text_centered(y, hostname, FONT_LARGE, color="black")
        y += 32

        # Red accent line
        composer.hline(y, color="red")
        y += 8

        # Hero IP address — the #1 thing you need from a headless Pi
        ip = self._get_ip()
        composer.text_centered(y, ip, FONT_LARGE, color="black")
        y += 32

        # Red accent line
        composer.hline(y, color="red")
        y += 8

        # Secondary info: MAC and SSID
        ssid = self._get_ssid()
        composer.label_value(
            MARGIN, y, "SSID:", ssid,
            FONT_LABEL, FONT_BODY,
        )
        y += 18

        mac = self._get_mac()
        composer.label_value(
            MARGIN, y, "MAC:", mac,
            FONT_LABEL, FONT_BODY,
        )

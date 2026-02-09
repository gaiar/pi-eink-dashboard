"""Screen 1: System overview dashboard with hero temperature and progress bars."""

import os
import socket
import subprocess

import psutil

from ..composer import Composer, WIDTH
from .base import (
    BaseScreen,
    FONT_HERO,
    FONT_BODY,
    FONT_LABEL,
    FONT_SMALL,
    CONTENT_TOP,
    MARGIN,
)


class DashboardScreen(BaseScreen):
    title = "DASHBOARD"

    def _get_temp(self) -> float:
        try:
            raw = subprocess.check_output(
                ["vcgencmd", "measure_temp"], text=True, timeout=2
            ).strip()
            return float(raw.split("=")[1].replace("'C", ""))
        except (subprocess.SubprocessError, FileNotFoundError, IndexError, ValueError):
            return 0.0

    def _get_uptime(self) -> str:
        try:
            with open("/proc/uptime") as f:
                seconds = float(f.read().split()[0])
        except (OSError, ValueError):
            return "N/A"
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        if days > 0:
            return f"Up: {days}d {hours}h {mins}m"
        return f"Up: {hours}h {mins}m"

    def draw(self, composer: Composer) -> None:
        y = CONTENT_TOP + 2

        # Hostname and uptime on the same line
        hostname = socket.gethostname()
        uptime = self._get_uptime()
        composer.text((MARGIN, y), hostname, FONT_BODY, color="black")
        composer.text_right(y, uptime, FONT_SMALL, color="black")
        y += 18

        # Hero temperature with decorative frame
        temp = self._get_temp()
        temp_str = f"{temp:.1f}\u00b0C"
        color = "red" if temp >= 70 else "black"

        frame_x = 40
        frame_w = WIDTH - 80
        frame_h = 50
        composer.rect(
            (frame_x, y, frame_x + frame_w, y + frame_h),
            color=color, fill=False,
        )
        composer.rect(
            (frame_x + 2, y + 2, frame_x + frame_w - 2, y + frame_h - 2),
            color=color, fill=False,
        )
        composer.text_centered(y + 5, temp_str, FONT_HERO, color=color)
        y += frame_h + 8

        # CPU / RAM / DISK progress bars with red labels
        cpu_pct = psutil.cpu_percent(interval=0)
        self._draw_labeled_bar(composer, y, "CPU", cpu_pct)
        y += 18

        mem = psutil.virtual_memory()
        self._draw_labeled_bar(composer, y, "RAM", mem.percent)
        y += 18

        disk = psutil.disk_usage("/")
        self._draw_labeled_bar(composer, y, "DISK", disk.percent)
        y += 20

        # Load average and process count in footer area
        load1, load5, load15 = os.getloadavg()
        composer.text(
            (MARGIN, y),
            f"Load: {load1:.2f} {load5:.2f} {load15:.2f}",
            FONT_SMALL,
            color="black",
        )
        procs = len(psutil.pids())
        composer.text_right(y, f"Procs: {procs}", FONT_SMALL, color="black")

    def _draw_labeled_bar(
        self,
        composer: Composer,
        y: int,
        label: str,
        percent: float,
    ) -> None:
        """Draw a labeled progress bar: LABEL [========] XX%"""
        label_w = 40
        pct_w = 35
        bar_x = MARGIN + label_w
        bar_w = WIDTH - MARGIN * 2 - label_w - pct_w - 4
        bar_h = 10

        composer.text((MARGIN, y), label, FONT_LABEL, color="red")
        composer.progress_bar(bar_x, y + 2, bar_w, bar_h, percent)
        pct_str = f"{percent:.0f}%"
        composer.text_right(y, pct_str, FONT_LABEL, color="black", margin=MARGIN)

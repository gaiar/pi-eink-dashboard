"""Screen 4: CPU health — temperature, frequency, voltage, throttle flags."""

import subprocess

from ..composer import Composer, WIDTH
from .base import (
    BaseScreen,
    FONT_HERO,
    FONT_LABEL,
    FONT_BODY,
    FONT_SMALL,
    CONTENT_TOP,
    MARGIN,
)

# Throttle flag bitmask (vcgencmd get_throttled)
_THROTTLE_FLAGS = {
    0: "Under-voltage",
    1: "Freq capped",
    2: "Throttled",
    3: "Soft temp limit",
}

_BOOT_FLAGS = {
    16: "Under-volt (boot)",
    17: "Freq cap (boot)",
    18: "Throttled (boot)",
    19: "Soft limit (boot)",
}


class HealthScreen(BaseScreen):
    title = "HEALTH"

    def _read_vcgencmd(self, arg: str) -> str:
        try:
            return subprocess.check_output(
                ["vcgencmd", arg], text=True, timeout=2
            ).strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            return ""

    def _get_temp(self) -> float:
        raw = self._read_vcgencmd("measure_temp")
        try:
            return float(raw.split("=")[1].replace("'C", ""))
        except (IndexError, ValueError):
            return 0.0

    def _get_voltage(self) -> str:
        raw = self._read_vcgencmd("measure_volts")
        try:
            return raw.split("=")[1]
        except IndexError:
            return "N/A"

    def _get_freq(self) -> int:
        """Return CPU frequency in MHz."""
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
                return int(f.read().strip()) // 1000
        except (OSError, ValueError):
            return 0

    def _get_governor(self) -> str:
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") as f:
                return f.read().strip()
        except OSError:
            return "N/A"

    def _get_throttled(self) -> int:
        raw = self._read_vcgencmd("get_throttled")
        try:
            return int(raw.split("=")[1], 16)
        except (IndexError, ValueError):
            return -1

    def draw(self, composer: Composer) -> None:
        y = CONTENT_TOP + 2

        # Hero temperature with decorative frame
        temp = self._get_temp()
        temp_str = f"{temp:.1f}\u00b0C"
        is_hot = temp >= 70
        color = "red" if is_hot else "black"

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

        # Frequency and voltage
        freq = self._get_freq()
        composer.label_value(
            MARGIN, y, "FREQ:", f"{freq} MHz",
            FONT_LABEL, FONT_BODY,
        )

        voltage = self._get_voltage()
        composer.label_value(
            WIDTH // 2, y, "VOLT:", voltage,
            FONT_LABEL, FONT_BODY,
        )
        y += 18

        # Governor
        governor = self._get_governor()
        composer.label_value(
            MARGIN, y, "GOV:", governor,
            FONT_LABEL, FONT_BODY,
        )
        y += 18

        # Throttle status
        throttled = self._get_throttled()
        if throttled < 0:
            composer.label_value(
                MARGIN, y, "THROTTLE:", "unknown",
                FONT_LABEL, FONT_BODY,
            )
        elif throttled == 0:
            composer.label_value(
                MARGIN, y, "THROTTLE:", "none",
                FONT_LABEL, FONT_BODY, label_color="black",
            )
        else:
            # Current active flags (bits 0-3)
            current_flags = []
            for bit, name in _THROTTLE_FLAGS.items():
                if throttled & (1 << bit):
                    current_flags.append(name)

            # Boot flags (bits 16-19)
            boot_flags = []
            for bit, name in _BOOT_FLAGS.items():
                if throttled & (1 << bit):
                    boot_flags.append(name)

            if current_flags:
                composer.text(
                    (MARGIN, y), "ACTIVE:", FONT_LABEL, color="red",
                )
                lw = composer.textlength("ACTIVE:", FONT_LABEL)
                composer.text(
                    (MARGIN + lw + 3, y),
                    ", ".join(current_flags),
                    FONT_SMALL, color="red",
                )
                y += 14

            if boot_flags:
                composer.text(
                    (MARGIN, y), "BOOT:", FONT_LABEL, color="black",
                )
                lw = composer.textlength("BOOT:", FONT_LABEL)
                composer.text(
                    (MARGIN + lw + 3, y),
                    ", ".join(boot_flags),
                    FONT_SMALL, color="black",
                )

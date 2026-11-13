"""High-performance screen color sampler for spatial and ambient keyboard illumination."""

from __future__ import annotations

import colorsys
import math
from typing import Any
from kreo_control.ambience.models import AmbienceConfig, AmbienceMode
from kreo_control.lighting.models import KeyLedInfo
from kreo_control.lighting.matrix import load_swarm75_led_map, rgb_to_hex

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def boost_saturation_and_brightness(r: int, g: int, b: int, sat_boost: float, bright_mult: float) -> tuple[int, int, int]:
    """Enhance color saturation and scale brightness for vibrant physical LED projection."""
    if r == 0 and g == 0 and b == 0:
        return 0, 0, 0

    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    h, s, v = colorsys.rgb_to_hsv(rf, gf, bf)

    # Boost saturation
    s = min(1.0, s * sat_boost)
    # Scale brightness
    v = min(1.0, v * bright_mult)

    ro, go, bo = colorsys.hsv_to_rgb(h, s, v)
    return int(ro * 255.0), int(go * 255.0), int(bo * 255.0)


class ScreenSampler:
    """Captures desktop screen frames and translates spatial zones into 82 ANSI key colors."""

    def __init__(self, led_map: list[KeyLedInfo] | None = None) -> None:
        self.led_map = led_map or load_swarm75_led_map()
        self._sct: Any | None = None
        self._max_row = max((k.row for k in self.led_map), default=5)
        self._max_col = max((k.col for k in self.led_map), default=15.5)

        # Smoothed color cache for EMA filtering
        self._current_colors: dict[str, tuple[float, float, float]] = {
            k.ui_key.lower(): (0.0, 0.0, 0.0) for k in self.led_map
        }
        self.dominant_color_hex: str = "#000000"

    def _get_sct(self) -> Any:
        if self._sct is None and HAS_MSS:
            self._sct = mss.mss()
        return self._sct

    def close(self) -> None:
        if self._sct is not None:
            try:
                self._sct.close()
            except Exception:
                pass
            self._sct = None

    def capture_frame_raw(self) -> tuple[int, int, bytes] | None:
        """Capture primary display frame returning (width, height, BGRA or RGB bytes)."""
        if HAS_MSS:
            try:
                sct = self._get_sct()
                # monitor 1 is primary display
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                img = sct.grab(monitor)
                return img.width, img.height, img.raw
            except Exception:
                pass

        if HAS_PIL:
            try:
                img = ImageGrab.grab()
                img = img.resize((160, 90), Image.Resampling.BILINEAR)
                return img.width, img.height, img.tobytes()
            except Exception:
                pass

        return None

    def sample_keys(self, config: AmbienceConfig) -> dict[str, str]:
        """Compute the next frame's 82 key RGB hex dictionary from screen colors."""
        if not HAS_MSS and not HAS_PIL:
            # Fallback mock for headless testing environments without display
            return {k.ui_key.lower(): "#00E5FF" for k in self.led_map}

        sct = self._get_sct()
        if sct is None and not HAS_PIL:
            return {k.ui_key.lower(): "#000000" for k in self.led_map}

        try:
            if HAS_MSS and sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                shot = sct.grab(monitor)
                w, h = shot.width, shot.height
                raw = shot.raw  # BGRA 32-bit format
                stride = w * 4

                def get_pixel_rgb(x: int, y: int) -> tuple[int, int, int]:
                    cx = max(0, min(w - 1, x))
                    cy = max(0, min(h - 1, y))
                    idx = cy * stride + cx * 4
                    # mss returns BGRA
                    b, g, r = raw[idx], raw[idx + 1], raw[idx + 2]
                    return r, g, b

            elif HAS_PIL:
                img = ImageGrab.grab()
                w, h = img.width, img.height
                pixels = img.load()

                def get_pixel_rgb(x: int, y: int) -> tuple[int, int, int]:
                    cx = max(0, min(w - 1, x))
                    cy = max(0, min(h - 1, y))
                    px = pixels[cx, cy]
                    return px[0], px[1], px[2]

            else:
                return {k.ui_key.lower(): "#000000" for k in self.led_map}

            # 1. Calculate target RGB for each key based on mode
            targets: dict[str, tuple[int, int, int]] = {}

            if config.mode == AmbienceMode.AVERAGE:
                # Sample 8x8 coarse grid across whole screen to compute average
                grid_samples: list[tuple[int, int, int]] = []
                for gy in range(8):
                    for gx in range(8):
                        px = int(w * (gx + 0.5) / 8)
                        py = int(h * (gy + 0.5) / 8)
                        grid_samples.append(get_pixel_rgb(px, py))

                avg_r = sum(c[0] for c in grid_samples) // len(grid_samples)
                avg_g = sum(c[1] for c in grid_samples) // len(grid_samples)
                avg_b = sum(c[2] for c in grid_samples) // len(grid_samples)
                br, bg, bb = boost_saturation_and_brightness(
                    avg_r, avg_g, avg_b, config.saturation_boost, config.brightness_multiplier
                )
                self.dominant_color_hex = rgb_to_hex(br, bg, bb)
                for k in self.led_map:
                    targets[k.ui_key.lower()] = (br, bg, bb)

            elif config.mode == AmbienceMode.CENTER:
                # Sample center 30% area of screen
                center_samples: list[tuple[int, int, int]] = []
                for gy in range(6):
                    for gx in range(6):
                        px = int(w * (0.35 + 0.3 * (gx / 5.0)))
                        py = int(h * (0.35 + 0.3 * (gy / 5.0)))
                        center_samples.append(get_pixel_rgb(px, py))

                avg_r = sum(c[0] for c in center_samples) // len(center_samples)
                avg_g = sum(c[1] for c in center_samples) // len(center_samples)
                avg_b = sum(c[2] for c in center_samples) // len(center_samples)
                br, bg, bb = boost_saturation_and_brightness(
                    avg_r, avg_g, avg_b, config.saturation_boost, config.brightness_multiplier
                )
                self.dominant_color_hex = rgb_to_hex(br, bg, bb)
                for k in self.led_map:
                    targets[k.ui_key.lower()] = (br, bg, bb)

            else:  # AmbienceMode.SPATIAL
                # Map each key's physical col/row coordinates to corresponding screen zone
                all_targets_r: list[int] = []
                all_targets_g: list[int] = []
                all_targets_b: list[int] = []

                for k in self.led_map:
                    norm_x = min(1.0, max(0.0, k.col / self._max_col))
                    norm_y = min(1.0, max(0.0, k.row / self._max_row))

                    # Sample 3x3 mini-neighborhood around this coordinate
                    screen_x = int(norm_x * (w - 1))
                    screen_y = int(norm_y * (h - 1))

                    sub_r, sub_g, sub_b = 0, 0, 0
                    dxs = [-15, 0, 15]
                    dys = [-15, 0, 15]
                    for dx in dxs:
                        for dy in dys:
                            pr, pg, pb = get_pixel_rgb(screen_x + dx, screen_y + dy)
                            sub_r += pr
                            sub_g += pg
                            sub_b += pb

                    sub_r //= 9
                    sub_g //= 9
                    sub_b //= 9

                    br, bg, bb = boost_saturation_and_brightness(
                        sub_r, sub_g, sub_b, config.saturation_boost, config.brightness_multiplier
                    )
                    targets[k.ui_key.lower()] = (br, bg, bb)
                    all_targets_r.append(br)
                    all_targets_g.append(bg)
                    all_targets_b.append(bb)

                if all_targets_r:
                    self.dominant_color_hex = rgb_to_hex(
                        sum(all_targets_r) // len(all_targets_r),
                        sum(all_targets_g) // len(all_targets_g),
                        sum(all_targets_b) // len(all_targets_b),
                    )

            # 2. Apply Exponential Moving Average (EMA) smoothing
            alpha = max(0.05, 1.0 - config.smoothness)
            result_hex: dict[str, str] = {}

            for k in self.led_map:
                u = k.ui_key.lower()
                tr, tg, tb = targets.get(u, (0, 0, 0))
                cur_r, cur_g, cur_b = self._current_colors.get(u, (0.0, 0.0, 0.0))

                new_r = cur_r * (1.0 - alpha) + tr * alpha
                new_g = cur_g * (1.0 - alpha) + tg * alpha
                new_b = cur_b * (1.0 - alpha) + tb * alpha

                self._current_colors[u] = (new_r, new_g, new_b)
                result_hex[u] = rgb_to_hex(int(round(new_r)), int(round(new_g)), int(round(new_b)))

            return result_hex

        except Exception as exc:
            return {k.ui_key.lower(): "#000000" for k in self.led_map}

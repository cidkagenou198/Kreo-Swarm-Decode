"""Background thread controller for real-time screen ambience streaming."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from kreo_control.ambience.models import AmbienceConfig, AmbienceStatusResponse
from kreo_control.ambience.sampler import ScreenSampler
from kreo_control.device.keyboard import KreoKeyboard

logger = logging.getLogger("kreo_control.ambience")


class AmbienceController:
    """Manages background screen capture and physical keyboard LED streaming."""

    _instance: AmbienceController | None = None
    _lock = threading.Lock()

    def __init__(self, keyboard: KreoKeyboard | None = None) -> None:
        self.keyboard = keyboard or KreoKeyboard.get_shared_instance()
        self.sampler = ScreenSampler()
        self.config = AmbienceConfig()

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._fps_tracker = 0.0
        self._last_error: str | None = None
        self._latest_colors: dict[str, str] = {}

    @classmethod
    def get_shared_instance(cls) -> AmbienceController:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def get_status(self) -> AmbienceStatusResponse:
        return AmbienceStatusResponse(
            running=self.is_running,
            config=self.config,
            current_fps=round(self._fps_tracker, 1),
            dominant_color=self.sampler.dominant_color_hex,
            last_error=self._last_error,
        )

    def get_latest_colors(self) -> dict[str, str]:
        return dict(self._latest_colors)

    def update_config(self, new_config: AmbienceConfig) -> AmbienceConfig:
        with self._lock:
            self.config = new_config
        return self.config

    def start(self, config: AmbienceConfig | None = None) -> bool:
        """Start the background streaming worker."""
        with self._lock:
            if self.is_running:
                if config:
                    self.config = config
                return True

            if config:
                self.config = config

            self._stop_event.clear()
            self._last_error = None
            self._running = True

            self._thread = threading.Thread(
                target=self._worker_loop,
                name="KreoAmbienceSyncThread",
                daemon=True,
            )
            self._thread.start()
            logger.info("Screen ambience streaming worker started.")
            return True

    def stop(self) -> bool:
        """Stop the background streaming worker."""
        with self._lock:
            if not self._running:
                return True

            self._running = False
            self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("Screen ambience streaming worker stopped.")
        return True

    def _worker_loop(self) -> None:
        """Worker loop running at the target FPS."""
        frame_count = 0
        fps_start = time.perf_counter()

        while not self._stop_event.is_set():
            loop_start = time.perf_counter()
            target_fps = max(5, min(30, self.config.fps))
            target_period = 1.0 / target_fps

            try:
                # 1. Sample screen colors
                key_colors = self.sampler.sample_keys(self.config)
                self._latest_colors = key_colors

                # 2. Push to physical keyboard
                self.keyboard.set_per_key_lighting(key_colors)

                # 3. Track FPS
                frame_count += 1
                now = time.perf_counter()
                if now - fps_start >= 1.0:
                    self._fps_tracker = frame_count / (now - fps_start)
                    frame_count = 0
                    fps_start = now

            except Exception as exc:
                self._last_error = str(exc)
                logger.error("Ambience loop error: %s", exc)
                time.sleep(0.1)

            # Sleep remainder of frame budget
            elapsed = time.perf_counter() - loop_start
            sleep_time = target_period - elapsed
            if sleep_time > 0.001:
                time.sleep(sleep_time)

        self._running = False


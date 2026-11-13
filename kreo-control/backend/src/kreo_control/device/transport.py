from __future__ import annotations

import time
import hid


class KreoTransportError(Exception):
    """Base transport error."""
    pass


class KreoDeviceNotFoundError(KreoTransportError):
    """Device not found."""
    pass


class KreoConnectionError(KreoTransportError):
    """Failed to open or communicate with device."""
    pass


class KreoTimeoutError(KreoTransportError):
    """Operation timed out waiting for device response."""
    pass


class KreoProtocolError(KreoTransportError):
    """Malformed or invalid protocol data."""
    pass



class HidTransport:
    """Manages raw HID communication with the keyboard."""

    def __init__(self, path: str) -> None:
        self.path: str = path
        self._device: hid.device | None = None

    def open(self) -> None:
        if self._device is not None:
            return
        dev = hid.device()
        try:
            dev.open_path(self.path.encode("utf-8") if isinstance(self.path, str) else self.path)
            self._device = dev
        except OSError as exc:
            raise KreoConnectionError(f"Failed to open device at path: {self.path}") from exc

    def close(self) -> None:
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass
            finally:
                self._device = None

    def __enter__(self) -> HidTransport:
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return self._device is not None

    def send_feature_report(self, data: bytes) -> int:
        """Send a feature report (Wired USB transport) with automatic retry and reconnection."""
        last_err = ""
        for attempt in range(3):
            if self._device is None:
                self.open()
            try:
                res = self._device.send_feature_report(data)
                if res >= 0:
                    return res
                last_err = self._device.error() or "unknown hid error"
            except Exception as exc:
                last_err = str(exc)

            # Re-open handle on failure before next attempt
            self.close()
            time.sleep(0.015)

        raise KreoConnectionError(f"Failed to send feature report: {last_err}")

    def get_feature_report(self, report_id: int, length: int) -> bytes:
        """Receive a feature report (Wired USB transport) with automatic retry and reconnection."""
        last_err = ""
        for attempt in range(3):
            if self._device is None:
                self.open()
            try:
                raw = self._device.get_feature_report(report_id, length)
                if raw and len(raw) > 0:
                    return bytes(raw)
                last_err = self._device.error() or "empty feature report"
            except Exception as exc:
                last_err = str(exc)

            self.close()
            time.sleep(0.015)

        raise KreoConnectionError(f"Failed to get feature report: {last_err}")

    def write(self, data: bytes) -> int:
        """Send an output report / packet (Wireless dongle transport)."""
        if self._device is None:
            raise KreoConnectionError("Device is not open")
        res = self._device.write(data)
        if res <= 0:
            raise KreoConnectionError("Failed to write to device")
        return res

    def read(self, length: int = 64, timeout_ms: int = 200) -> bytes:
        """Read an input report / packet (Wireless dongle transport)."""
        if self._device is None:
            raise KreoConnectionError("Device is not open")
        raw = self._device.read(length, timeout_ms)
        return bytes(raw)

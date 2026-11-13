from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class ConnectionType(str, Enum):
    WIRED = "wired"
    WIRELESS = "wireless"


class SupportedDevice(BaseModel):
    vendor_id: int
    product_id: int
    usage_page: int
    usage: int
    product_name: str
    connection_type: ConnectionType


class DeviceDescriptor(BaseModel):
    vendor_id: int
    product_id: int
    usage_page: int
    usage: int
    interface_number: int
    path: str
    product_name: str
    product_string: str | None = None
    serial_number: str | None = None
    connection_type: ConnectionType


"""Protocol abstraction for serialization."""

from abc import ABC, abstractmethod
from typing import Any
import json
import msgpack


class Protocol(ABC):
    """Base protocol for serialization."""

    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        """Serialize data to bytes."""
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to data."""
        pass

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Content-Type header value."""
        pass


class JSONProtocol(Protocol):
    """JSON protocol."""

    def serialize(self, data: Any) -> bytes:
        return json.dumps(data).encode("utf-8")

    def deserialize(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))

    @property
    def content_type(self) -> str:
        return "application/json"


class MessagePackProtocol(Protocol):
    """MessagePack protocol."""

    def serialize(self, data: Any) -> bytes:
        return msgpack.packb(data, use_bin_type=True)

    def deserialize(self, data: bytes) -> Any:
        return msgpack.unpackb(data, raw=False)

    @property
    def content_type(self) -> str:
        return "application/msgpack"


def get_protocol(content_type: str = "application/json") -> Protocol:
    """Get protocol by content type."""
    if "msgpack" in content_type.lower():
        return MessagePackProtocol()
    return JSONProtocol()

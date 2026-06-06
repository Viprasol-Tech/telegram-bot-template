"""Transport layer for sending messages back to Telegram.

The bot never talks to the network directly. Instead it depends on the
:class:`Transport` protocol, so the real Bot-API HTTP client is a pluggable
implementation and tests use :class:`InMemoryTransport`, which simply records
every message that would have been sent — no network, no API token.

Part of Telegram Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

__all__ = ["InMemoryTransport", "SentMessage", "Transport"]


@dataclass(frozen=True, slots=True)
class SentMessage:
    """A record of a single outbound message.

    Attributes:
        chat_id: The chat the message was addressed to.
        text: The message body.
    """

    chat_id: int
    text: str


@runtime_checkable
class Transport(Protocol):
    """Anything capable of delivering a message to a Telegram chat.

    Implement this protocol to wire the bot to a real HTTP client (e.g. a thin
    wrapper over the ``sendMessage`` Bot-API method). The framework only depends
    on this single method, keeping I/O at the edge.
    """

    def send_message(self, chat_id: int, text: str) -> None:
        """Deliver ``text`` to the chat identified by ``chat_id``."""
        ...


@dataclass(slots=True)
class InMemoryTransport:
    """A deterministic fake transport that records messages instead of sending.

    Ideal for tests and the offline demo: every :meth:`send_message` call appends
    a :class:`SentMessage` to :attr:`sent`, which can then be asserted against.

    Attributes:
        sent: All messages recorded so far, in send order.
    """

    sent: list[SentMessage] = field(default_factory=list)

    def send_message(self, chat_id: int, text: str) -> None:
        """Record an outbound message without performing any I/O."""
        self.sent.append(SentMessage(chat_id=chat_id, text=text))

    @property
    def last(self) -> SentMessage | None:
        """The most recently recorded message, or ``None`` if none were sent."""
        return self.sent[-1] if self.sent else None

    def texts(self) -> list[str]:
        """Return just the text bodies of every recorded message, in order."""
        return [m.text for m in self.sent]

    def clear(self) -> None:
        """Forget all recorded messages."""
        self.sent.clear()

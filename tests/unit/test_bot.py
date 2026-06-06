"""Tests for the Bot pipeline and the in-memory transport fake."""

from __future__ import annotations

from telegram_bot_template.bot import Bot, build_default_router
from telegram_bot_template.transport import InMemoryTransport, SentMessage, Transport


def _payload(text: str, *, chat_id: int = 500) -> dict[str, object]:
    return {
        "update_id": 1,
        "message": {"from": {"id": 1}, "chat": {"id": chat_id}, "text": text},
    }


def test_in_memory_transport_is_a_transport() -> None:
    assert isinstance(InMemoryTransport(), Transport)


def test_transport_records_sent_messages() -> None:
    transport = InMemoryTransport()
    transport.send_message(7, "hello")
    transport.send_message(8, "world")
    assert transport.sent == [SentMessage(7, "hello"), SentMessage(8, "world")]
    assert transport.texts() == ["hello", "world"]
    assert transport.last == SentMessage(8, "world")


def test_transport_clear() -> None:
    transport = InMemoryTransport()
    transport.send_message(1, "x")
    transport.clear()
    assert transport.sent == []
    assert transport.last is None


def test_bot_process_update_sends_reply() -> None:
    transport = InMemoryTransport()
    bot = Bot(build_default_router(), transport)
    reply = bot.process_update(_payload("/echo ping", chat_id=123))
    assert reply == "ping"
    assert transport.last == SentMessage(123, "ping")


def test_bot_default_commands() -> None:
    transport = InMemoryTransport()
    bot = Bot(build_default_router(), transport)
    assert bot.process_update(_payload("/start")).startswith("Welcome!")  # type: ignore[union-attr]
    assert "Commands:" in bot.process_update(_payload("/help"))  # type: ignore[operator]


def test_bot_unknown_command_default_reply() -> None:
    transport = InMemoryTransport()
    bot = Bot(build_default_router(), transport)
    reply = bot.process_update(_payload("/missing"))
    assert reply is not None
    assert "Unknown command" in reply


def test_bot_skips_unparseable_payload() -> None:
    transport = InMemoryTransport()
    bot = Bot(build_default_router(), transport)
    assert bot.process_update({"update_id": 1}) is None
    assert transport.sent == []


def test_bot_process_updates_batch() -> None:
    transport = InMemoryTransport()
    bot = Bot(build_default_router(), transport)
    replies = bot.process_updates([_payload("/start"), {"update_id": 2}, _payload("/echo hi")])
    assert len(replies) == 2
    assert replies[1] == "hi"
    assert len(transport.sent) == 2


def test_bot_respects_username_for_mentions() -> None:
    transport = InMemoryTransport()
    bot = Bot(build_default_router(), transport, bot_username="MyBot")
    # Command addressed to another bot -> treated as non-command -> default reply.
    reply = bot.process_update(_payload("/help@OtherBot"))
    assert reply is not None
    assert "only understand commands" in reply

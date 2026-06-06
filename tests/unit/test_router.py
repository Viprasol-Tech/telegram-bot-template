"""Tests for command routing and dispatch."""

from __future__ import annotations

import pytest

from telegram_bot_template.router import CommandRouter
from telegram_bot_template.update import Update


def _update(text: str) -> Update:
    return Update.from_dict(
        {
            "update_id": 1,
            "message": {"from": {"id": 1}, "chat": {"id": 1}, "text": text},
        }
    )


def test_dispatch_routes_to_registered_handler() -> None:
    router = CommandRouter()
    router.register("start", lambda u: "hi")
    assert router.dispatch(_update("/start")) == "hi"


def test_register_strips_leading_slash_and_lowercases() -> None:
    router = CommandRouter()
    router.register("/PING", lambda u: "pong")
    assert router.dispatch(_update("/ping")) == "pong"
    assert router.has("ping")


def test_handler_receives_args() -> None:
    router = CommandRouter()
    router.register("echo", lambda u: " ".join(u.args))
    assert router.dispatch(_update("/echo a b c")) == "a b c"


def test_unknown_command_uses_default() -> None:
    router = CommandRouter()
    reply = router.dispatch(_update("/nope"))
    assert "Unknown command" in reply
    assert "/nope" in reply


def test_plain_text_uses_default() -> None:
    router = CommandRouter()
    reply = router.dispatch(_update("hello"))
    assert "only understand commands" in reply


def test_custom_default_handler() -> None:
    router = CommandRouter(default=lambda u: "fallback")
    assert router.dispatch(_update("anything")) == "fallback"


def test_decorator_registration() -> None:
    router = CommandRouter()

    @router.command("time")
    def _time(update: Update) -> str:
        return "now"

    assert router.dispatch(_update("/time")) == "now"


def test_commands_listing_is_sorted() -> None:
    router = CommandRouter()
    router.register("zebra", lambda u: "")
    router.register("apple", lambda u: "")
    assert router.commands() == ["apple", "zebra"]


def test_empty_command_name_rejected() -> None:
    router = CommandRouter()
    with pytest.raises(ValueError, match="must not be empty"):
        router.register("/", lambda u: "")

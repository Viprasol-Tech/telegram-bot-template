"""Tests for update parsing and command extraction."""

from __future__ import annotations

import pytest

from telegram_bot_template.update import Update, parse_command


def _msg(text: str, *, update_id: int = 1, chat_id: int = 100) -> dict[str, object]:
    return {
        "update_id": update_id,
        "message": {
            "message_id": 1,
            "from": {"id": 7, "username": "alice"},
            "chat": {"id": chat_id, "type": "private"},
            "text": text,
        },
    }


def test_parse_command_simple() -> None:
    assert parse_command("/start") == ("start", [])


def test_parse_command_with_args() -> None:
    assert parse_command("/echo hello world") == ("echo", ["hello", "world"])


def test_parse_command_lowercases_name() -> None:
    assert parse_command("/Start") == ("start", [])


def test_plain_text_is_not_a_command() -> None:
    assert parse_command("just text") == (None, [])


def test_parse_command_strips_bot_mention() -> None:
    assert parse_command("/help@MyBot now") == ("help", ["now"])


def test_parse_command_mention_for_other_bot_ignored() -> None:
    assert parse_command("/help@OtherBot", bot_username="MyBot") == (None, [])


def test_parse_command_mention_for_us_matches() -> None:
    assert parse_command("/help@MyBot", bot_username="mybot") == ("help", [])


def test_update_from_dict_parses_command_and_chat() -> None:
    update = Update.from_dict(_msg("/echo a b", chat_id=555))
    assert update.chat_id == 555
    assert update.user_id == 7
    assert update.command == "echo"
    assert update.args == ["a", "b"]
    assert update.text == "/echo a b"


def test_update_from_dict_plain_text() -> None:
    update = Update.from_dict(_msg("hello there"))
    assert update.command is None
    assert update.args == []
    assert update.text == "hello there"


def test_update_supports_edited_message() -> None:
    payload: dict[str, object] = {
        "update_id": 5,
        "edited_message": {
            "from": {"id": 9},
            "chat": {"id": 12},
            "text": "/ping",
        },
    }
    update = Update.from_dict(payload)
    assert update.command == "ping"
    assert update.chat_id == 12


def test_update_without_message_raises() -> None:
    with pytest.raises(ValueError, match="no 'message'"):
        Update.from_dict({"update_id": 1})


def test_update_is_frozen() -> None:
    update = Update.from_dict(_msg("/start"))
    with pytest.raises(Exception):  # noqa: B017 - pydantic raises ValidationError
        update.chat_id = 999  # type: ignore[misc]

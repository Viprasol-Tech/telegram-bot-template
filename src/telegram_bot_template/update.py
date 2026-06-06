"""Parse raw Telegram update dicts into typed :class:`Update` objects.

A Telegram *update* is the JSON payload delivered by the Bot API (via webhook or
long polling). This module turns the relevant slice of that payload into a small,
typed value object and splits any leading ``/command`` out of the message text.

Part of Telegram Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ["Update", "parse_command"]


def parse_command(text: str, *, bot_username: str | None = None) -> tuple[str | None, list[str]]:
    """Split message text into a normalised command and its arguments.

    A command is the first whitespace-delimited token when it starts with ``/``.
    Telegram allows ``/cmd@BotName`` in group chats; the ``@BotName`` suffix is
    stripped and, when ``bot_username`` is given, a mismatching suffix means the
    command was aimed at a different bot and is ignored.

    Args:
        text: The raw message text.
        bot_username: This bot's username (without ``@``), used to honour the
            ``/cmd@BotName`` addressing convention. Case-insensitive.

    Returns:
        A ``(command, args)`` tuple. ``command`` is the lower-cased name without
        the leading ``/`` (e.g. ``"start"``), or ``None`` when the text is not a
        command or is addressed to another bot. ``args`` are the remaining
        whitespace-delimited tokens (empty when there is no command).

    Examples:
        >>> parse_command("/start")
        ('start', [])
        >>> parse_command("/echo hello world")
        ('echo', ['hello', 'world'])
        >>> parse_command("just text")
        (None, [])
    """
    stripped = text.strip()
    if not stripped.startswith("/"):
        return None, []

    parts = stripped.split()
    head = parts[0][1:]  # drop the leading slash
    args = parts[1:]

    if "@" in head:
        name, _, mention = head.partition("@")
        if bot_username is not None and mention.lower() != bot_username.lower():
            return None, []
        head = name

    if not head:
        return None, []
    return head.lower(), args


class Update(BaseModel):
    """A typed, transport-agnostic view of an inbound Telegram update.

    Only the fields needed for routing are modelled. Construct one from a raw
    update dict with :meth:`from_dict`.

    Attributes:
        update_id: Telegram's monotonically increasing update identifier.
        chat_id: The chat the message belongs to (used to address replies).
        user_id: The sender's user id, when present.
        text: The full message text (empty string for non-text messages).
        command: The parsed command name without ``/`` (``None`` if not a command).
        args: Whitespace-delimited arguments following the command.
    """

    model_config = ConfigDict(frozen=True)

    update_id: int
    chat_id: int
    user_id: int | None
    text: str
    command: str | None
    args: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, object], *, bot_username: str | None = None) -> Update:
        """Build an :class:`Update` from a raw Telegram update payload.

        Supports both ``message`` and ``edited_message`` updates. Missing or
        malformed sections degrade gracefully to sensible defaults rather than
        raising, so a bot can stay up in the face of unexpected payloads.

        Args:
            payload: The raw update dict as delivered by the Telegram Bot API.
            bot_username: This bot's username for ``/cmd@BotName`` handling.

        Returns:
            A populated, immutable :class:`Update`.

        Raises:
            ValueError: If neither ``message`` nor ``edited_message`` is present.
        """
        update_id = int(_as_int(payload.get("update_id"), default=0))

        message = payload.get("message") or payload.get("edited_message")
        if not isinstance(message, dict):
            raise ValueError("update has no 'message' or 'edited_message'")

        chat = message.get("chat")
        chat_id = int(_as_int(chat.get("id") if isinstance(chat, dict) else None, default=0))

        user = message.get("from")
        user_id_raw = user.get("id") if isinstance(user, dict) else None
        user_id = int(_as_int(user_id_raw, default=0)) if user_id_raw is not None else None

        raw_text = message.get("text")
        text = raw_text if isinstance(raw_text, str) else ""

        command, args = parse_command(text, bot_username=bot_username)
        return cls(
            update_id=update_id,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            command=command,
            args=args,
        )


def _as_int(value: object, *, default: int) -> int:
    """Coerce ``value`` to ``int``, falling back to ``default`` on failure."""
    if isinstance(value, bool):  # bool is an int subclass; treat as non-numeric here
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default

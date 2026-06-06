"""Command routing: map an :class:`Update` to the handler that should reply.

A :class:`CommandRouter` keeps a table of command name to handler callables,
plus a single default handler for unmatched input. :meth:`CommandRouter.dispatch`
selects the right handler and returns its reply text — pure logic with no I/O,
which makes routing trivial to unit-test.

Part of Telegram Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Callable

from telegram_bot_template.update import Update

__all__ = ["CommandRouter", "Handler"]

#: A handler takes the inbound update and returns the reply text to send.
Handler = Callable[[Update], str]


def _default_handler(update: Update) -> str:
    """Fallback reply used when no command matches."""
    if update.command is not None:
        return f"Unknown command: /{update.command}. Try /help."
    return "I only understand commands. Try /help."


class CommandRouter:
    """Register command handlers and dispatch updates to the right one.

    Routing rules, in order:

    1. If the update carries a known ``command``, its registered handler runs.
    2. Otherwise the default handler runs (an unknown ``/command`` and plain text
       both fall through here, letting the default distinguish the two).

    Command names are matched case-insensitively and without the leading ``/``.
    """

    def __init__(self, default: Handler | None = None) -> None:
        """Create an empty router.

        Args:
            default: Optional handler for unmatched input. When omitted, a
                built-in default explains that the command was not recognised.
        """
        self._handlers: dict[str, Handler] = {}
        self._default: Handler = default if default is not None else _default_handler

    def register(self, command: str, handler: Handler) -> None:
        """Register ``handler`` for ``command``.

        Args:
            command: The command name, with or without a leading ``/``
                (e.g. ``"start"`` or ``"/start"``). Matched case-insensitively.
            handler: Callable returning the reply text for a matching update.

        Raises:
            ValueError: If ``command`` is empty after normalisation.
        """
        name = self._normalise(command)
        if not name:
            raise ValueError("command name must not be empty")
        self._handlers[name] = handler

    def command(self, name: str) -> Callable[[Handler], Handler]:
        """Decorator form of :meth:`register`.

        Example:
            >>> router = CommandRouter()
            >>> @router.command("ping")
            ... def _ping(update: Update) -> str:
            ...     return "pong"
            >>> router.commands()
            ['ping']
        """

        def decorator(handler: Handler) -> Handler:
            self.register(name, handler)
            return handler

        return decorator

    def set_default(self, handler: Handler) -> None:
        """Replace the default (no-match) handler."""
        self._default = handler

    def dispatch(self, update: Update) -> str:
        """Route ``update`` to a handler and return its reply text.

        Args:
            update: The parsed inbound update.

        Returns:
            The reply text produced by the matching handler, or the default
            handler when no command matches.
        """
        if update.command is not None:
            handler = self._handlers.get(update.command)
            if handler is not None:
                return handler(update)
        return self._default(update)

    def has(self, command: str) -> bool:
        """Return whether a handler is registered for ``command``."""
        return self._normalise(command) in self._handlers

    def commands(self) -> list[str]:
        """Return all registered command names, sorted alphabetically."""
        return sorted(self._handlers)

    @staticmethod
    def _normalise(command: str) -> str:
        """Lower-case ``command`` and strip a single leading ``/``."""
        name = command.strip()
        if name.startswith("/"):
            name = name[1:]
        return name.lower()

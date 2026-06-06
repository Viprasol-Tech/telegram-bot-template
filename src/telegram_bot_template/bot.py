"""The :class:`Bot` that ties a router and a transport together.

A bot receives a raw Telegram update dict, parses it, dispatches it through the
:class:`CommandRouter` for a reply, and sends that reply via the configured
:class:`Transport`. Swap the transport for :class:`InMemoryTransport` to run the
whole pipeline offline.

Part of Telegram Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from telegram_bot_template.router import CommandRouter, Handler
from telegram_bot_template.transport import Transport
from telegram_bot_template.update import Update

__all__ = ["Bot", "build_default_router"]


def _start_handler(update: Update) -> str:
    """Reply to ``/start``."""
    return "Welcome! I'm a Telegram Bot Template by Viprasol Tech. Try /help."


def _help_handler(update: Update) -> str:
    """Reply to ``/help`` listing the built-in commands."""
    return "Commands:\n/start - greet\n/help - this message\n/echo <text> - echo back"


def _echo_handler(update: Update) -> str:
    """Reply to ``/echo`` by echoing back the arguments."""
    if not update.args:
        return "Usage: /echo <text>"
    return " ".join(update.args)


def build_default_router() -> CommandRouter:
    """Return a router pre-wired with ``/start``, ``/help`` and ``/echo``.

    A convenient starting point for new bots; register more commands on the
    returned router or build your own from scratch.
    """
    router = CommandRouter()
    router.register("start", _start_handler)
    router.register("help", _help_handler)
    router.register("echo", _echo_handler)
    return router


class Bot:
    """Glue between update parsing, command routing and message sending.

    Attributes:
        router: The command router used to compute replies.
        transport: The transport used to deliver replies.
        bot_username: Optional username for ``/cmd@BotName`` handling.
    """

    def __init__(
        self,
        router: CommandRouter,
        transport: Transport,
        *,
        bot_username: str | None = None,
    ) -> None:
        """Create a bot.

        Args:
            router: The configured :class:`CommandRouter`.
            transport: The :class:`Transport` used to send replies.
            bot_username: This bot's username (without ``@``), forwarded to the
                update parser so ``/cmd@BotName`` is addressed correctly.
        """
        self.router = router
        self.transport = transport
        self.bot_username = bot_username

    def register(self, command: str, handler: Handler) -> None:
        """Register a command handler on the underlying router."""
        self.router.register(command, handler)

    def process_update(self, payload: dict[str, object]) -> str | None:
        """Parse, route and send a reply for one raw update payload.

        Args:
            payload: The raw Telegram update dict.

        Returns:
            The reply text that was sent, or ``None`` if the payload could not
            be parsed into a message (in which case nothing is sent).
        """
        try:
            update = Update.from_dict(payload, bot_username=self.bot_username)
        except ValueError:
            return None
        reply = self.router.dispatch(update)
        self.transport.send_message(update.chat_id, reply)
        return reply

    def process_updates(self, payloads: list[dict[str, object]]) -> list[str]:
        """Process a batch of raw updates, returning the replies that were sent.

        Unparseable payloads are skipped (they produce no reply).
        """
        replies: list[str] = []
        for payload in payloads:
            reply = self.process_update(payload)
            if reply is not None:
                replies.append(reply)
        return replies

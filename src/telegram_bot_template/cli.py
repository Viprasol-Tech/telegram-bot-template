"""Command-line interface for Telegram Bot Template.

``telegram-bot-template demo`` feeds a few synthetic Telegram update dicts
through a :class:`Bot` wired to the :class:`InMemoryTransport` fake and prints
each reply — no bot token, no network.

Part of Telegram Bot Template by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console

from telegram_bot_template import __version__
from telegram_bot_template.bot import Bot, build_default_router
from telegram_bot_template.transport import InMemoryTransport

app = typer.Typer(add_completion=False, help="Telegram Bot Template — by Viprasol Tech.")
console = Console()


def _demo_updates() -> list[dict[str, object]]:
    """Build a deterministic batch of raw Telegram update dicts."""
    texts = ["/start", "/help", "/echo hello world", "/unknown", "just chatting"]
    updates: list[dict[str, object]] = []
    for i, text in enumerate(texts, start=1):
        updates.append(
            {
                "update_id": 1000 + i,
                "message": {
                    "message_id": i,
                    "from": {"id": 42, "username": "demo_user"},
                    "chat": {"id": 9001, "type": "private"},
                    "text": text,
                },
            }
        )
    return updates


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"telegram-bot-template [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def demo() -> None:
    """Run a batch of synthetic updates through the bot and print the replies."""
    transport = InMemoryTransport()
    bot = Bot(build_default_router(), transport, bot_username="ViprasolDemoBot")

    console.print("[bold]Telegram Bot Template[/] demo (offline, fake transport)\n")
    for payload in _demo_updates():
        message = payload["message"]
        text = message["text"] if isinstance(message, dict) else ""
        reply = bot.process_update(payload)
        console.print(f"[cyan]IN [/] {text!r}")
        console.print(f"[green]OUT[/] {reply!r}\n")

    console.print(f"Transport recorded [bold]{len(transport.sent)}[/] sent messages.")


if __name__ == "__main__":
    app()

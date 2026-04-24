#!/usr/bin/env python3
"""
Guitar Practice Tool
Runs with:  python main.py
Exits with: Ctrl+C
"""

import sys
import logging
import signal

import questionary
import pyfiglet
from colorama import init, Fore, Style

from tools.metronome.metronome import run as run_metronome
from tools.chord_trainer.trainer import run as run_chord_trainer

# ─── Init ─────────────────────────────────────────────────────────────────────

init(autoreset=True)

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)-8s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("script.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── Print Helpers ────────────────────────────────────────────────────────────

WIDTH = 60


def banner():
    art = pyfiglet.figlet_format("PENELOPE", font="big")
    print(Fore.CYAN + Style.BRIGHT + art, end="")
    print(Fore.WHITE + Style.BRIGHT + "  Guitar Practice Tool  " + Fore.CYAN + "│" + Fore.WHITE + "  Ctrl+C to quit")
    divider()


def divider():
    print(Fore.CYAN + Style.DIM + "─" * WIDTH)


def section(title: str):
    print()
    divider()
    print(Fore.CYAN + Style.BRIGHT + f"  {title}")
    divider()


def ok(msg: str):
    print(Fore.GREEN + Style.BRIGHT + f"  ✓  {msg}")
    logger.info("OK  — %s", msg)


def err(msg: str):
    print(Fore.RED + Style.BRIGHT + f"  ✗  {msg}")
    logger.error("ERR — %s", msg)


def info(msg: str):
    print(Fore.YELLOW + f"  →  {msg}")
    logger.info("INFO — %s", msg)


def blank():
    print()


# ─── Graceful Exit ────────────────────────────────────────────────────────────


def _exit(sig=None, frame=None):
    blank()
    print(Fore.YELLOW + Style.BRIGHT + "  Goodbye!\n")
    logger.info("Tool exited by user")
    sys.exit(0)


signal.signal(signal.SIGINT, _exit)


# ─── Main Menu ────────────────────────────────────────────────────────────────


def menu_metronome():
    run_metronome()


def menu_chord_trainer():
    run_chord_trainer()


def main_menu() -> str | None:
    blank()
    return questionary.select(
        "Select a tool:",
        choices=[
            questionary.Choice("Chord Trainer", value="chord_trainer"),
            questionary.Choice("Metronome",     value="metronome"),
            questionary.Choice("Exit",          value="exit"),
        ],
        style=questionary.Style([
            ("selected",    "fg:cyan bold"),
            ("pointer",     "fg:cyan bold"),
            ("highlighted", "fg:cyan"),
        ]),
    ).ask()


# ─── Entry Point ──────────────────────────────────────────────────────────────


def main():
    logger.info("Guitar Practice Tool started")
    banner()

    ROUTES = {
        "chord_trainer": menu_chord_trainer,
        "metronome":     menu_metronome,
        "exit":          _exit,
    }

    while True:
        choice = main_menu()

        if choice is None or choice == "exit":
            _exit()

        handler = ROUTES.get(choice)
        if handler:
            handler()


if __name__ == "__main__":
    main()

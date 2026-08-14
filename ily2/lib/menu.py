from __future__ import annotations

import sys

import questionary
from questionary import Style

ily2_style = Style(
    [
        ("qmark", "fg:#00d7af bold"),
        ("question", "bold"),
        ("answer", "fg:#00d7af bold"),
        ("pointer", "fg:#00d7af bold"),
        ("highlighted", "fg:#00d7af bold"),
        ("selected", "fg:#00af5f"),
    ]
)


def _abort_if_none(value):
    if value is None:
        print("\nİptal edildi.")
        sys.exit(1)
    return value


def select(question: str, choices: list, default=None):
    return _abort_if_none(
        questionary.select(question, choices=choices, default=default, style=ily2_style).ask()
    )


def checkbox(question: str, choices: list):
    return _abort_if_none(
        questionary.checkbox(question, choices=choices, style=ily2_style).ask()
    )


def text(question: str, default: str = "", validate=None):
    return _abort_if_none(
        questionary.text(question, default=default, validate=validate, style=ily2_style).ask()
    )


def password(question: str, validate=None):
    return _abort_if_none(
        questionary.password(question, validate=validate, style=ily2_style).ask()
    )


def confirm(question: str, default: bool = True) -> bool:
    return _abort_if_none(
        questionary.confirm(question, default=default, style=ily2_style).ask()
    )


def password_with_confirmation(prompt_label: str) -> str:
    """Ask for a password twice and make sure they match."""
    while True:
        pw1 = password(f"{prompt_label}:")
        pw2 = password(f"{prompt_label} (tekrar):")
        if pw1 == pw2 and pw1:
            return pw1
        print("Parolalar eşleşmedi ya da boş, tekrar deneyin.")

"""Small terminal prompt helpers (standard library only)."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")


class Cancelled(Exception):
    """Raised when the user aborts (Ctrl+C / Ctrl+D)."""


def _input(text: str) -> str:
    try:
        return input(text)
    except (KeyboardInterrupt, EOFError):
        print()
        raise Cancelled()


def ask(question: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    answer = _input(f"  {question}{suffix}: ").strip()
    return answer or (default or "")


def confirm(question: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    answer = _input(f"  {question} [{hint}]: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def menu(title: str, items: Sequence[Tuple[str, T]], default: int = 1) -> T:
    """Numbered menu. `items` is a list of (label, value). Returns the chosen value."""
    print(f"\n  {title}")
    for i, (label, _) in enumerate(items, 1):
        print(f"    {i}) {label}")
    while True:
        answer = _input(f"  Choose 1-{len(items)} [{default}]: ").strip()
        if not answer:
            return items[default - 1][1]
        if answer.isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1][1]
        print("  Invalid choice, try again.")


def ask_lines(question: str) -> list:
    """Read lines until an empty line. Returns the non-empty lines."""
    print(f"  {question} (empty line to finish)")
    lines = []
    while True:
        line = _input("  > ").strip()
        if not line:
            return lines
        lines.append(line)

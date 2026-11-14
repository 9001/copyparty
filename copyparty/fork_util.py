# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only helpers; see FORK.md

if True:  # pylint: disable=using-constant-test
    from typing import Any


def split_names(txt: str) -> list[str]:
    """comma-separated names (e.g. --shr-adm) -> list of exact names"""
    return [x.strip() for x in txt.split(",") if x.strip()]


def grants_top(args: Any) -> str:
    """the grants virtual folder (--grants), without slashes; "" = off"""
    return (getattr(args, "grants", "") or "").strip("/")


def grants_on(args: Any) -> bool:
    return bool(grants_top(args))

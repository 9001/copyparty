# coding: utf-8
from __future__ import division, print_function, unicode_literals

# fork-only helpers; see FORK.md


def split_names(txt: str) -> list[str]:
    """comma-separated names (e.g. --shr-adm) -> list of exact names"""
    return [x.strip() for x in txt.split(",") if x.strip()]

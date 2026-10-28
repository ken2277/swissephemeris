# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import swisseph as swe

_is_configured = False


def configure_ephemeris(ephemeris_path: str) -> None:
    global _is_configured

    swe.set_ephe_path(ephemeris_path)
    _is_configured = True


def is_configured() -> bool:
    return _is_configured

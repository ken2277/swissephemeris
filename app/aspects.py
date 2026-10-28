# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

ASPECT_DEFINITIONS = [
    {"key": "conjunction", "angle": 0,   "max_orb": 8, "name_en": "Conjunction", "symbol": "☌", "nature_en": "Neutral"},
    {"key": "opposition",  "angle": 180, "max_orb": 8, "name_en": "Opposition",  "symbol": "☍", "nature_en": "Tense"},
    {"key": "trine",       "angle": 120, "max_orb": 8, "name_en": "Trine",       "symbol": "△", "nature_en": "Harmonious"},
    {"key": "square",      "angle": 90,  "max_orb": 7, "name_en": "Square",      "symbol": "□", "nature_en": "Tense"},
    {"key": "sextile",     "angle": 60,  "max_orb": 6, "name_en": "Sextile",     "symbol": "⚹", "nature_en": "Harmonious"},
]


def angular_distance(longitude_a: float, longitude_b: float) -> float:
    diff = abs(longitude_a - longitude_b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def find_aspects(bodies: list[dict]) -> list[dict]:
    found = []

    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            body_a = bodies[i]
            body_b = bodies[j]

            distance = angular_distance(body_a["longitude"], body_b["longitude"])

            best_match = None
            smallest_orb = None
            for aspect_def in ASPECT_DEFINITIONS:
                orb = abs(distance - aspect_def["angle"])
                if orb <= aspect_def["max_orb"]:
                    if smallest_orb is None or orb < smallest_orb:
                        smallest_orb = orb
                        best_match = aspect_def

            if best_match is not None:
                found.append({
                    "body_a": body_a["key"],
                    "body_b": body_b["key"],
                    "aspect_key": best_match["key"],
                    "aspect_name_en": best_match["name_en"],
                    "symbol": best_match["symbol"],
                    "nature_en": best_match["nature_en"],
                    "exact_angle": best_match["angle"],
                    "actual_angle": round(distance, 2),
                    "orb": round(smallest_orb, 2),
                })

    return found

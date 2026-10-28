# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

ZODIAC_SIGNS = [
    {"key": "aries",       "name_en": "Aries",       "symbol": "♈", "element_en": "Fire"},
    {"key": "taurus",      "name_en": "Taurus",      "symbol": "♉", "element_en": "Earth"},
    {"key": "gemini",      "name_en": "Gemini",      "symbol": "♊", "element_en": "Air"},
    {"key": "cancer",      "name_en": "Cancer",      "symbol": "♋", "element_en": "Water"},
    {"key": "leo",         "name_en": "Leo",         "symbol": "♌", "element_en": "Fire"},
    {"key": "virgo",       "name_en": "Virgo",       "symbol": "♍", "element_en": "Earth"},
    {"key": "libra",       "name_en": "Libra",       "symbol": "♎", "element_en": "Air"},
    {"key": "scorpio",     "name_en": "Scorpio",     "symbol": "♏", "element_en": "Water"},
    {"key": "sagittarius", "name_en": "Sagittarius", "symbol": "♐", "element_en": "Fire"},
    {"key": "capricorn",   "name_en": "Capricorn",   "symbol": "♑", "element_en": "Earth"},
    {"key": "aquarius",    "name_en": "Aquarius",    "symbol": "♒", "element_en": "Air"},
    {"key": "pisces",      "name_en": "Pisces",      "symbol": "♓", "element_en": "Water"},
]

DEGREES_PER_SIGN = 30.0


def normalize_longitude(longitude: float) -> float:
    return longitude % 360.0


def sign_from_longitude(longitude: float) -> dict:
    longitude = normalize_longitude(longitude)

    sign_index = int(longitude // DEGREES_PER_SIGN)
    sign_index = min(sign_index, len(ZODIAC_SIGNS) - 1)

    degree_in_sign = longitude - (sign_index * DEGREES_PER_SIGN)
    degree_int = int(degree_in_sign)
    minute_float = (degree_in_sign - degree_int) * 60
    minute_int = int(round(minute_float))

    if minute_int == 60:
        minute_int = 0
        degree_int += 1

    sign = ZODIAC_SIGNS[sign_index]

    return {
        "sign_index": sign_index,
        "sign_key": sign["key"],
        "sign_name_en": sign["name_en"],
        "sign_symbol": sign["symbol"],
        "sign_element_en": sign["element_en"],
        "degree_in_sign": degree_int,
        "minute_in_sign": minute_int,
        "degree_display": f"{sign['name_en']} {degree_int}°{minute_int:02d}'",
    }

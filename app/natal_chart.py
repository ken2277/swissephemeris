# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import datetime

import swisseph as swe

from . import zodiac
from .aspects import find_aspects
from .timezone_utils import TimezoneLookupError, to_utc

BODY_DEFINITIONS = [
    {"key": "sun",         "name_en": "Sun",         "symbol": "☉", "swe_id": swe.SUN,       "required": True},
    {"key": "moon",        "name_en": "Moon",        "symbol": "☽", "swe_id": swe.MOON,      "required": True},
    {"key": "mercury",     "name_en": "Mercury",     "symbol": "☿", "swe_id": swe.MERCURY,   "required": True},
    {"key": "venus",       "name_en": "Venus",       "symbol": "♀", "swe_id": swe.VENUS,     "required": True},
    {"key": "mars",        "name_en": "Mars",        "symbol": "♂", "swe_id": swe.MARS,      "required": True},
    {"key": "jupiter",     "name_en": "Jupiter",     "symbol": "♃", "swe_id": swe.JUPITER,   "required": True},
    {"key": "saturn",      "name_en": "Saturn",      "symbol": "♄", "swe_id": swe.SATURN,    "required": True},
    {"key": "uranus",      "name_en": "Uranus",      "symbol": "♅", "swe_id": swe.URANUS,    "required": True},
    {"key": "neptune",     "name_en": "Neptune",     "symbol": "♆", "swe_id": swe.NEPTUNE,   "required": True},
    {"key": "pluto",       "name_en": "Pluto",       "symbol": "♇", "swe_id": swe.PLUTO,     "required": True},
    {"key": "north_node",  "name_en": "North Node",  "symbol": "☊", "swe_id": swe.MEAN_NODE, "required": True},
    {"key": "chiron",      "name_en": "Chiron",      "symbol": "⚷", "swe_id": swe.CHIRON,    "required": False},
]

HOUSE_SYSTEM_NAMES_EN = {
    "P": "Placidus",
    "K": "Koch",
    "E": "Equal House",
    "W": "Whole Sign",
    "R": "Regiomontanus",
    "C": "Campanus",
}
DEFAULT_HOUSE_SYSTEM = "P"

FALLBACK_HOUSE_SYSTEM = "W"


class NatalChartError(Exception):
    pass


def _to_julian_day_ut(utc_datetime: datetime.datetime) -> float:
    hour_as_decimal = (
        utc_datetime.hour
        + utc_datetime.minute / 60
        + utc_datetime.second / 3600
    )
    return swe.julday(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        hour_as_decimal,
    )


def _calc_body_longitude(julian_day_ut: float, swe_id: int) -> tuple[float, float]:
    calc_flags = swe.FLG_SWIEPH | swe.FLG_SPEED

    values, _return_flags = swe.calc_ut(julian_day_ut, swe_id, calc_flags)
    longitude, _latitude, _distance, longitude_speed, _lat_speed, _dist_speed = values

    return longitude, longitude_speed


def _calc_houses(julian_day_ut: float, latitude: float, longitude: float, house_system: str):
    hsys_bytes = house_system.encode("ascii")

    try:
        cusps, ascmc = swe.houses(julian_day_ut, latitude, longitude, hsys_bytes)
        return cusps, ascmc, house_system, False
    except swe.Error:
        fallback_bytes = FALLBACK_HOUSE_SYSTEM.encode("ascii")
        cusps, ascmc = swe.houses(julian_day_ut, latitude, longitude, fallback_bytes)
        return cusps, ascmc, FALLBACK_HOUSE_SYSTEM, True


def _house_number_for_longitude(longitude: float, cusps) -> int:
    longitude = zodiac.normalize_longitude(longitude)

    for house_index in range(12):
        start = cusps[house_index]
        end = cusps[(house_index + 1) % 12]

        if start <= end:
            if start <= longitude < end:
                return house_index + 1
        else:
            if longitude >= start or longitude < end:
                return house_index + 1

    return 12


def calculate_natal_chart(
    birth_date: datetime.date,
    birth_time: datetime.time,
    latitude: float,
    longitude: float,
    place_name: str | None = None,
    house_system: str = DEFAULT_HOUSE_SYSTEM,
) -> dict:
    if not (-90.0 <= latitude <= 90.0):
        raise NatalChartError("Latitude must be between -90 and 90.")
    if not (-180.0 <= longitude <= 180.0):
        raise NatalChartError("Longitude must be between -180 and 180.")
    if house_system not in HOUSE_SYSTEM_NAMES_EN:
        raise NatalChartError(f"House system '{house_system}' is not supported.")

    try:
        birth_moment = to_utc(birth_date, birth_time, latitude, longitude)
    except TimezoneLookupError as exc:
        raise NatalChartError(str(exc)) from exc

    julian_day_ut = _to_julian_day_ut(birth_moment.utc_datetime)

    bodies = []
    for body_def in BODY_DEFINITIONS:
        try:
            body_longitude, body_speed = _calc_body_longitude(julian_day_ut, body_def["swe_id"])
        except swe.Error as exc:
            if body_def["required"]:
                raise NatalChartError(
                    f"Could not calculate the position of {body_def['name_en']}. "
                    "Please check the server's ephemeris data file configuration. "
                    f"(Details: {exc})"
                ) from exc
            continue

        sign_info = zodiac.sign_from_longitude(body_longitude)
        bodies.append({
            "key": body_def["key"],
            "name_en": body_def["name_en"],
            "symbol": body_def["symbol"],
            "longitude": round(body_longitude, 4),
            "is_retrograde": body_speed < 0,
            **sign_info,
        })

    cusps, ascmc, used_house_system, house_fallback_applied = _calc_houses(
        julian_day_ut, latitude, longitude, house_system
    )

    for body in bodies:
        body["house"] = _house_number_for_longitude(body["longitude"], cusps)

    houses = []
    for house_index in range(12):
        cusp_longitude = cusps[house_index]
        sign_info = zodiac.sign_from_longitude(cusp_longitude)
        houses.append({
            "number": house_index + 1,
            "longitude": round(cusp_longitude, 4),
            **sign_info,
        })

    ascendant_longitude = ascmc[0]
    midheaven_longitude = ascmc[1]
    descendant_longitude = zodiac.normalize_longitude(ascendant_longitude + 180)
    imum_coeli_longitude = zodiac.normalize_longitude(midheaven_longitude + 180)

    angles = {
        "ascendant": {
            "longitude": round(ascendant_longitude, 4),
            **zodiac.sign_from_longitude(ascendant_longitude),
        },
        "midheaven": {
            "longitude": round(midheaven_longitude, 4),
            **zodiac.sign_from_longitude(midheaven_longitude),
        },
        "descendant": {
            "longitude": round(descendant_longitude, 4),
            **zodiac.sign_from_longitude(descendant_longitude),
        },
        "imum_coeli": {
            "longitude": round(imum_coeli_longitude, 4),
            **zodiac.sign_from_longitude(imum_coeli_longitude),
        },
    }

    aspects = find_aspects(bodies)

    return {
        "input": {
            "birth_date": birth_date.isoformat(),
            "birth_time": birth_time.strftime("%H:%M"),
            "latitude": latitude,
            "longitude": longitude,
            "place_name": place_name,
        },
        "timezone": {
            "name": birth_moment.timezone_name,
            "utc_offset_hours": birth_moment.utc_offset_hours,
            "utc_datetime": birth_moment.utc_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "julian_day_ut": round(julian_day_ut, 6),
        "house_system": {
            "requested": house_system,
            "used": used_house_system,
            "name_en": HOUSE_SYSTEM_NAMES_EN.get(used_house_system, used_house_system),
            "fallback_applied": house_fallback_applied,
        },
        "bodies": bodies,
        "houses": houses,
        "angles": angles,
        "aspects": aspects,
    }

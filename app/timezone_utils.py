# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import datetime
from dataclasses import dataclass

from timezonefinder import TimezoneFinder

_timezone_finder = TimezoneFinder()


class TimezoneLookupError(Exception):
    pass


@dataclass
class LocalBirthMoment:
    utc_datetime: datetime.datetime
    timezone_name: str
    utc_offset_hours: float


def find_timezone_name(latitude: float, longitude: float) -> str:
    timezone_name = _timezone_finder.timezone_at(lat=latitude, lng=longitude)

    if timezone_name is None:
        raise TimezoneLookupError(
            "Could not determine the time zone for the specified location "
            "(latitude/longitude). Please choose the location again on the map."
        )

    return timezone_name


def to_utc(
    birth_date: datetime.date,
    birth_time: datetime.time,
    latitude: float,
    longitude: float,
) -> LocalBirthMoment:
    from zoneinfo import ZoneInfo

    timezone_name = find_timezone_name(latitude, longitude)

    local_datetime = datetime.datetime.combine(
        birth_date, birth_time, tzinfo=ZoneInfo(timezone_name)
    )

    utc_datetime = local_datetime.astimezone(datetime.timezone.utc)

    utc_offset = local_datetime.utcoffset()
    utc_offset_hours = utc_offset.total_seconds() / 3600.0 if utc_offset else 0.0

    return LocalBirthMoment(
        utc_datetime=utc_datetime,
        timezone_name=timezone_name,
        utc_offset_hours=utc_offset_hours,
    )

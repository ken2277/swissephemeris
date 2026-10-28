# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only
# ============================================================================
# app/timezone_utils.py
#
# 【このファイルは何をしているの?】
# 「生まれた場所(緯度・経度)」と「生まれた日時(現地時間)」から、
# 天体計算に必要な「世界標準時(UTC)」を求めるためのファイルです。
#
# なぜこの変換が必要なの?という理由を、小学生にも分かるように説明します。
#
#   世界には「時差(じさ)」があります。
#   たとえば日本の「午後3時」は、イギリスのロンドンではまだ「午前6時」です。
#   同じ瞬間なのに、国によって時計の表示は違うのです。
#
#   星占いで大切なのは「その瞬間、実際に空のどこに太陽や月があったか」です。
#   これは世界中どこでも共通の「世界標準時(UTC)」という、
#   1つの基準の時間で計算する必要があります。
#
#   なので、お客さんが「日本時間の午後3時に生まれた」と入力しても、
#   コンピューターの内部ではまず「それは世界標準時で何時か」に
#   変換してから、天体の位置を計算しなければならないのです。
#
# この変換のためには、「生まれた場所が、世界のどのタイムゾーン
# (時差のグループ)に属するか」を知る必要があります。
# それを調べてくれるのが timezonefinder という道具です。
# ============================================================================

from __future__ import annotations

import datetime
from dataclasses import dataclass

from timezonefinder import TimezoneFinder

# ------------------------------------------------------------------------
# TimezoneFinder は、内部に「世界地図のタイムゾーン境界線データ」という
# それなりに大きなデータを読み込みます。
# リクエストが来るたびに毎回作り直すと時間がもったいないので、
# このファイルが読み込まれた瞬間(アプリ起動時)に1回だけ作って、
# 使い回すようにしています。
# ------------------------------------------------------------------------
_timezone_finder = TimezoneFinder()


class TimezoneLookupError(Exception):
    """緯度・経度からタイムゾーンを特定できなかったときに発生させるエラーです。"""


@dataclass
class LocalBirthMoment:
    """
    「現地時間 → 世界標準時への変換結果」をまとめて持ち運ぶための入れ物です。

    Pythonの @dataclass は、「いくつかの値をひとまとめにした荷物」を
    簡単に作るための、便利な仕組み(おまじない)です。
    """
    utc_datetime: datetime.datetime   # 世界標準時での日時
    timezone_name: str                # 見つかったタイムゾーンの名前 (例: "Asia/Tokyo")
    utc_offset_hours: float           # その瞬間の時差(時間単位。例: 日本なら 9.0)


def find_timezone_name(latitude: float, longitude: float) -> str:
    """
    緯度・経度を受け取り、そこが属するタイムゾーンの名前を返します。

    タイムゾーンの名前は "Asia/Tokyo" や "America/New_York" のような、
    「地域/代表都市」という形式で表されます。これは "IANA タイムゾーン名"
    と呼ばれる、世界共通のルールです。

    陸地だけでなく、海の上であっても(その経度に応じた)大まかな時間帯を
    返すように "timezone_at" という関数を使っています。
    """
    timezone_name = _timezone_finder.timezone_at(lat=latitude, lng=longitude)

    if timezone_name is None:
        # 経度・緯度の値自体はおかしくないのに、何らかの理由で
        # タイムゾーンを特定できなかった、非常に稀なケースです。
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
    """
    「生まれた日」「生まれた時刻(現地時間)」「生まれた場所の緯度・経度」
    の3つから、世界標準時(UTC)に変換した結果を返します。

    処理の流れ:
      1. 緯度・経度から、タイムゾーン名(例: "Asia/Tokyo")を調べる
      2. 「日付+時刻」と「タイムゾーン」を組み合わせて、
         「タイムゾーン情報つきの日時」を作る
      3. Pythonの標準機能で、それを世界標準時に変換する

    ポイント: 同じ "Asia/Tokyo" というタイムゾーンでも、国や地域によっては
    昔「サマータイム(夏時間)」を採用していた時期があったりして、
    年によって時差が変わることがあります。
    Python標準の "zoneinfo" という仕組みは、そうした歴史上のルールの
    変化もすべて内蔵データとして知っているので、
    何年に生まれた人であっても、自動的に正しい時差を計算してくれます。
    """
    # Python 3.9 以降で標準搭載されている、タイムゾーンを扱うための機能です。
    # ここで import しているのは、必要になった時にだけ読み込むためです。
    from zoneinfo import ZoneInfo

    timezone_name = find_timezone_name(latitude, longitude)

    # "tzinfo=" を指定して datetime を作ると、「この日時は、この
    # タイムゾーンでの時刻ですよ」という情報がくっついた特別な値になります。
    local_datetime = datetime.datetime.combine(
        birth_date, birth_time, tzinfo=ZoneInfo(timezone_name)
    )

    # ".astimezone(timezone.utc)" で、世界標準時での日時に変換します。
    # イメージとしては「日本時間の15:00」を「世界標準時の6:00」に
    # 変換するようなものです(日本とUTCには9時間の差があるため)。
    utc_datetime = local_datetime.astimezone(datetime.timezone.utc)

    # その瞬間の時差を、時間の単位(例: 9.0時間)で取り出します。
    utc_offset = local_datetime.utcoffset()
    utc_offset_hours = utc_offset.total_seconds() / 3600.0 if utc_offset else 0.0

    return LocalBirthMoment(
        utc_datetime=utc_datetime,
        timezone_name=timezone_name,
        utc_offset_hours=utc_offset_hours,
    )

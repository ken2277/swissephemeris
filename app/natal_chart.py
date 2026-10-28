# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only
# ============================================================================
# app/natal_chart.py
#
# 【このファイルは何をしているの?】
# このアプリの「一番の頭脳」にあたるファイルです。
# 「いつ・どこで生まれたか」という情報を受け取って、
#
#   1. 太陽・月・惑星たちが、それぞれ何座の何度にいたか
#   2. 12個の「ハウス(部屋)」の境界線がどこにあったか
#   3. アセンダント(生まれた瞬間に東の地平線から昇っていた星座)
#   4. 天体同士の「アスペクト(角度の関係)」
#
# …をすべて計算して、1つの大きな辞書(dict)にまとめて返す
# 関数 calculate_natal_chart() を用意しています。
#
# 難しい天文計算そのものは、Swiss Ephemeris(pyswisseph)という
# 専門のライブラリにおまかせします。このファイルの役目は、
# 「入力された値を、正しい順番でSwiss Ephemerisに渡し、
#   返ってきた結果を、見やすい形に整理する」という、
# いわば "通訳" や "整理係" です。
# ============================================================================

from __future__ import annotations

import datetime

import swisseph as swe

from . import zodiac
from .aspects import find_aspects
from .timezone_utils import TimezoneLookupError, to_utc

# ----------------------------------------------------------------------------
# 計算する天体(太陽・月・惑星など)の一覧です。
#
#   key       : プログラム内部で使う短い名前
#   name_en   : 画面に表示する英語名
#   symbol    : 天体記号
#   swe_id    : Swiss Ephemeris の中で、その天体を指し示す番号
#   required  : True の場合、この天体の計算に失敗したらエラーにする。
#               False の場合、データファイルが無いなどの理由で計算できなくても
#               (キロンのように)その天体だけ省略して、他の計算は続行する。
#
# 太陽~冥王星と「ドラゴンヘッド(北交点)」は、専用のデータファイルが
# 無くても Swiss Ephemeris 内蔵の簡易計算(Moshier)で計算できるため
# required = True にしていますが、
# キロンのような小惑星は専用データファイル(seas_18.se1)が
# 無いと一切計算できないため required = False にしています。
# ----------------------------------------------------------------------------
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

# ハウス(部屋)の区切り方には、実はいくつもの流派(計算方式)があります。
# ここでは代表的なものだけを用意しています。既定値は世界的に最もよく
# 使われている「プラシーダス方式」です。
HOUSE_SYSTEM_NAMES_EN = {
    "P": "Placidus",
    "K": "Koch",
    "E": "Equal House",
    "W": "Whole Sign",
    "R": "Regiomontanus",
    "C": "Campanus",
}
DEFAULT_HOUSE_SYSTEM = "P"

# 北極圏・南極圏に近い場所で生まれた場合など、プラシーダス方式では
# 数学的に計算できないケースがあります。その場合に自動的に
# 切り替える、"必ず計算できる" 方式です。
FALLBACK_HOUSE_SYSTEM = "W"


class NatalChartError(Exception):
    """
    入力値がおかしい場合や、天体暦の計算でどうしても解決できない
    エラーが起きた場合に発生させる、このアプリ独自のエラーです。

    Flask 側(routes.py)は、このエラーを捕まえて、お客さんに
    分かりやすい英語のエラーメッセージを表示します。
    """


def _to_julian_day_ut(utc_datetime: datetime.datetime) -> float:
    """
    「世界標準時(UTC)での日時」を、Swiss Ephemeris が計算のために
    使う "ユリウス日(にちすう)" という数値に変換します。

    ユリウス日というのは、天文学の世界で昔から使われている
    「紀元前4713年のある日を1日目として、そこから数えて
    何日目か」を表す通し番号です。年・月・日・時・分・秒が
    バラバラになっているより、1つの数字で表した方が、
    コンピューターにとって計算しやすいのです。

    swe.julday() は「時刻」を "小数の時間" で受け取ります。
    たとえば 6時30分は 6.5、12時15分は 12.25、という具合です。
    なので、まず「時・分・秒」を1つの小数に合体させてから渡します。
    """
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
    """
    指定した天体(太陽・月・惑星など)の、ある瞬間の位置を計算します。

    返ってくるのは (経度, 移動速度) の組です。
      経度(黄経) : 天体が、黄道上の0度~360度のどこにいるか
      移動速度   : 1日あたり何度動いているか(マイナスなら「逆行」中)

    「逆行(ぎゃっこう)」とは、地球から見たときに、その天体が
    一時的に "後ろ向き" に進んでいるように見える現象のことです。
    (実際に天体が逆走しているわけではなく、地球自身も動きながら
     観測しているために起こる「見かけ上」の動きです)
    """
    # SEFLG_SWIEPH: できるだけ精密な Swiss Ephemeris のデータを使ってください、
    #               という希望を伝えるフラグです。
    #               (もしデータファイルが見つからない場合は、
    #                自動的に簡易計算(Moshier)に切り替わります)
    # SEFLG_SPEED : 位置だけでなく、動く速さも一緒に計算してください、
    #               という追加の希望です(逆行の判定に使います)。
    calc_flags = swe.FLG_SWIEPH | swe.FLG_SPEED

    values, _return_flags = swe.calc_ut(julian_day_ut, swe_id, calc_flags)
    longitude, _latitude, _distance, longitude_speed, _lat_speed, _dist_speed = values

    return longitude, longitude_speed


def _calc_houses(julian_day_ut: float, latitude: float, longitude: float, house_system: str):
    """
    12個のハウス(部屋)の境界線の角度と、
    アセンダント・MC(南中点)などの重要な角度(アングル)を計算します。

    北極圏・南極圏の近くなど、太陽が沈まない・昇らない時期がある
    ような特殊な場所と時刻の組み合わせでは、プラシーダス方式のような
    「時間ベース」の計算方式では、数学的に答えを求められないことが
    あります。その場合はエラーになるので、必ず答えが出せる
    「ホールサイン方式」に自動的に切り替えます。
    """
    hsys_bytes = house_system.encode("ascii")

    try:
        cusps, ascmc = swe.houses(julian_day_ut, latitude, longitude, hsys_bytes)
        return cusps, ascmc, house_system, False
    except swe.Error:
        fallback_bytes = FALLBACK_HOUSE_SYSTEM.encode("ascii")
        cusps, ascmc = swe.houses(julian_day_ut, latitude, longitude, fallback_bytes)
        return cusps, ascmc, FALLBACK_HOUSE_SYSTEM, True


def _house_number_for_longitude(longitude: float, cusps) -> int:
    """
    ある天体の経度(0度~360度)が、12個のハウスのうち
    どのハウスに含まれるかを調べます。

    ハウスの境界線は必ずしも綺麗に30度ずつではないため
    (プラシーダス方式などでは、場所や時間によって幅が変わります)、
    「このハウスの開始位置から、次のハウスの開始位置の手前まで」
    という範囲に入っているかどうかを、1つずつ確かめていきます。

    ただし、角度は0度に戻って1周する性質があるため
    (359度の次は0度)、"開始位置 > 終了位置" になる場合は
    「0度をまたいでいる」とみなして特別に扱います。
    """
    longitude = zodiac.normalize_longitude(longitude)

    for house_index in range(12):
        start = cusps[house_index]
        end = cusps[(house_index + 1) % 12]

        if start <= end:
            if start <= longitude < end:
                return house_index + 1
        else:
            # 例: 350度 → 20度のように、0度(360度)をまたぐハウス
            if longitude >= start or longitude < end:
                return house_index + 1

    # 理論上ここには到達しませんが、万一のための保険として
    # 最後のハウス番号を返しておきます。
    return 12


def calculate_natal_chart(
    birth_date: datetime.date,
    birth_time: datetime.time,
    latitude: float,
    longitude: float,
    place_name: str | None = None,
    house_system: str = DEFAULT_HOUSE_SYSTEM,
) -> dict:
    """
    ネイタルチャート(出生図)の計算をすべて行い、
    結果をひとまとめの辞書(dict)にして返す、メインの関数です。

    引数(この関数に渡す値):
      birth_date    : 生まれた日 (datetime.date型)
      birth_time    : 生まれた時刻。現地時間。 (datetime.time型)
      latitude      : 生まれた場所の緯度 (北緯はプラス、南緯はマイナス)
      longitude     : 生まれた場所の経度 (東経はプラス、西経はマイナス)
      place_name    : 生まれた場所の名前(表示用。無くても計算はできます)
      house_system  : ハウスの計算方式。省略した場合はプラシーダス方式。

    戻り値:
      天体・ハウス・アングル・アスペクトの情報を含んだ辞書。
      そのまま JSON(JavaScript Object Notation。Webでよく使われる
      データのやり取り形式)としてブラウザに送り返せる形になっています。
    """
    # --- 入力値のチェック -----------------------------------------------
    # プログラムの世界では「お客さんが入力してくる値は、何が来るか
    # 分からない」と考えて、まず値がおかしくないかを確認するのが
    # とても大切な習慣です(これを「バリデーション」と呼びます)。
    if not (-90.0 <= latitude <= 90.0):
        raise NatalChartError("Latitude must be between -90 and 90.")
    if not (-180.0 <= longitude <= 180.0):
        raise NatalChartError("Longitude must be between -180 and 180.")
    if house_system not in HOUSE_SYSTEM_NAMES_EN:
        raise NatalChartError(f"House system '{house_system}' is not supported.")

    # --- 現地時間 → 世界標準時(UTC)への変換 -----------------------------
    try:
        birth_moment = to_utc(birth_date, birth_time, latitude, longitude)
    except TimezoneLookupError as exc:
        raise NatalChartError(str(exc)) from exc

    julian_day_ut = _to_julian_day_ut(birth_moment.utc_datetime)

    # --- 各天体(太陽・月・惑星など)の位置を計算 --------------------------
    bodies = []
    for body_def in BODY_DEFINITIONS:
        try:
            body_longitude, body_speed = _calc_body_longitude(julian_day_ut, body_def["swe_id"])
        except swe.Error as exc:
            if body_def["required"]:
                # 太陽や月など、絶対に必要な天体の計算に失敗した場合は、
                # チャート全体を「計算できません」というエラーにします。
                raise NatalChartError(
                    f"Could not calculate the position of {body_def['name_en']}. "
                    "Please check the server's ephemeris data file configuration. "
                    f"(Details: {exc})"
                ) from exc
            # キロンのように、無くても致命的ではない天体は、
            # このデータだけ省略して、残りの計算を続けます。
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

    # --- ハウス(部屋)の境界線と、アセンダント/MCの計算 --------------------
    cusps, ascmc, used_house_system, house_fallback_applied = _calc_houses(
        julian_day_ut, latitude, longitude, house_system
    )

    # 天体それぞれについて「何ハウスに入っているか」を追加で計算します。
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

    ascendant_longitude = ascmc[0]  # アセンダント(生まれた瞬間、東の地平線に昇っていた度数)
    midheaven_longitude = ascmc[1]  # MC/南中点(生まれた瞬間、天の一番高いところにあった度数)
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

    # --- 天体同士のアスペクト(角度の関係)を計算 ---------------------------
    aspects = find_aspects(bodies)

    # --- 最終的な結果をひとまとめにする -----------------------------------
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

# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only
# ============================================================================
# app/zodiac.py
#
# 【このファイルは何をしているの?】
# 「黄道十二星座(おうどうじゅうにせいざ)」、つまり
# 牡羊座(おひつじざ)から魚座(うおざ)までの12個の星座について、
# 名前や記号(シンボル)をまとめて管理しているファイルです。
#
# 星占いの世界では、天(そら)を1周ぐるっと360度の円だと考えます。
# その360度を、30度ずつ12個に区切ったものが「12星座」です。
#
#   0度   ~  30度   → 牡羊座(おひつじざ)
#   30度  ~  60度   → 牡牛座(おうしざ)
#   60度  ~  90度   → 双子座(ふたござ)
#   ...(このように30度ずつ進んでいきます)...
#   330度 ~  360度  → 魚座(うおざ)
#
# 太陽や月や惑星が「黄道(こうどう。天体が通る道)」の
# どの角度(0度~360度)にいるかを計算すれば、
# 「今その天体は何座にいるか」が分かる、という仕組みです。
# ============================================================================

from __future__ import annotations

# 12星座のデータです。リスト(一覧)の0番目が牡羊座、1番目が牡牛座…
# という順番で、実際の星座の並び順と揃えてあります。
#
#   key         : プログラムの中だけで使う、英語の短い名前
#   name_en     : 画面に表示する英語の名前
#   symbol      : 星座を表す記号(絵文字のようなもの)
#   element_en  : 四大元素(火・地・風・水)。星占いで「似た性格のグループ分け」
#                 として使われる伝統的な分類です。
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

# 1つの星座がしめる角度の広さ。360度 ÷ 12星座 = 30度。
DEGREES_PER_SIGN = 30.0


def normalize_longitude(longitude: float) -> float:
    """
    角度を "0度以上 360度未満" の範囲におさまるように直します。

    たとえば "370度" は1周(360度)を超えているので "10度" と同じ意味ですし、
    "-10度" は1周分足りないので "350度" と同じ意味になります。
    これは、時計の針が12時を過ぎたら0時に戻るのと同じイメージです。

    "%" (パーセント記号) は「割り算のあまりを求める」という意味の記号です。
    360で割ったあまりを求めることで、上のような "1周した後" の角度を
    正しく 0~360 の範囲に収めることができます。
    """
    return longitude % 360.0


def sign_from_longitude(longitude: float) -> dict:
    """
    黄道上の角度(0度~360度)を受け取り、
    「何座の、何度何分にあたるか」を計算して返します。

    たとえば longitude = 45.5 (度) が渡されてきたら、

      45.5度 ÷ 30度 = 1 あまり 15.5度

    ということなので、「1番目(0番目から数えて)の星座」つまり牡牛座の
    「15.5度」の位置にある、と分かります。
    15.5度は「15度」と「0.5度」に分けられ、0.5度は60分(ぷん)の半分、
    つまり「30分」なので、"牡牛座 15度30分" という表示になります。
    (星占いの角度は、時計と同じように 1度 = 60分 で表す伝統があります)
    """
    longitude = normalize_longitude(longitude)

    sign_index = int(longitude // DEGREES_PER_SIGN)
    # 万が一の計算誤差で12を超えてしまった場合の保険(実際はほぼ起こりません)
    sign_index = min(sign_index, len(ZODIAC_SIGNS) - 1)

    degree_in_sign = longitude - (sign_index * DEGREES_PER_SIGN)
    degree_int = int(degree_in_sign)
    minute_float = (degree_in_sign - degree_int) * 60
    minute_int = int(round(minute_float))

    # 分(ふん)を四捨五入した結果 "60分" になってしまった場合、
    # 度を1つ繰り上げる処理(時計の "59分の次は0分で1時間繰り上がる" と同じ)
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

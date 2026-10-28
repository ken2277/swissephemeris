# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only
# ============================================================================
# app/aspects.py
#
# 【このファイルは何をしているの?】
# 「アスペクト」と呼ばれる、2つの天体の"角度の関係"を見つけ出す
# ファイルです。
#
# 星占いでは、「太陽と月が、空の上でどれくらいの角度(かくど)離れて
# いるか」によって、2つの天体の間に特別な意味(相性の良し悪しなど)が
# 生まれる、と考えます。この関係のことを「アスペクト」と呼びます。
#
# たとえば、
#   ・2つの天体がほぼ同じ場所(0度差)にあれば → 「合(ごう)」
#   ・ちょうど反対側(180度差)にあれば       → 「衝(しょう)」
#   ・正三角形の位置関係(120度差)にあれば   → 「トライン」
#   ・正方形の位置関係(90度差)にあれば      → 「スクエア」
#   ・六角形の位置関係(60度差)にあれば      → 「セクスタイル」
#
# ぴったり0度、180度…でなくても、数度くらいのズレ(これを
# 「オーブ」と呼びます)までは「だいたい同じ意味を持つ」とみなす
# 伝統があるので、このファイルでも「許容できるズレの範囲(orb)」を
# 決めて判定しています。
# ============================================================================

from __future__ import annotations

# --- アスペクト(角度の関係)の定義一覧 --------------------------------------
#
#   key        : プログラム内部で使う短い名前
#   angle      : ぴったりのアスペクトになる角度
#   max_orb    : ここまでのズレなら「そのアスペクトが成立している」とみなす、
#                許される誤差の範囲(度数)
#   name_en    : 英語の名前
#   symbol     : 記号
#   nature_en  : 伝統的に「調和的(良い意味)」か「緊張的(challenging)」かの分類
#
# オーブの数値は、多くの占星術の教科書で使われる、一般的な目安の値です。
ASPECT_DEFINITIONS = [
    {"key": "conjunction", "angle": 0,   "max_orb": 8, "name_en": "Conjunction", "symbol": "☌", "nature_en": "Neutral"},
    {"key": "opposition",  "angle": 180, "max_orb": 8, "name_en": "Opposition",  "symbol": "☍", "nature_en": "Tense"},
    {"key": "trine",       "angle": 120, "max_orb": 8, "name_en": "Trine",       "symbol": "△", "nature_en": "Harmonious"},
    {"key": "square",      "angle": 90,  "max_orb": 7, "name_en": "Square",      "symbol": "□", "nature_en": "Tense"},
    {"key": "sextile",     "angle": 60,  "max_orb": 6, "name_en": "Sextile",     "symbol": "⚹", "nature_en": "Harmonious"},
]


def angular_distance(longitude_a: float, longitude_b: float) -> float:
    """
    2つの角度(0度~360度)の間の、"円周上での最短の差"を計算します。

    ふつうの引き算だと、たとえば "10度" と "350度" の差は
    "340度" になってしまいますが、円をぐるっと1周する道のりで考えると
    実際には "20度" しか離れていません(10度→0度→350度、と回る方が近い)。

    このズレを直すために、まず単純な差を求めたあと、
    それが180度を超えていたら "360度からその値を引く" ことで、
    必ず「0度~180度」におさまる"本当の最短距離"に直しています。
    """
    diff = abs(longitude_a - longitude_b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def find_aspects(bodies: list[dict]) -> list[dict]:
    """
    天体のリストを受け取り、すべての天体の"2つの組み合わせ"について
    アスペクト(角度の関係)が成立しているかどうかを調べます。

    たとえば天体が10個あれば、組み合わせは
    (10 × 9) ÷ 2 = 45通り
    あるので、その45通りすべてをチェックします。

    "bodies" には、各天体の辞書(dict)が入っていることを期待しています。
    それぞれの辞書には、最低限
        {"key": "sun", "longitude": 123.45, ...}
    のような情報が入っている必要があります。
    """
    found = []

    # 二重ループ(ループの中にループ)を使って、
    # すべての「2つの天体の組み合わせ」を1回ずつ取り出します。
    # "i" と "j" の代わりに "j > i" の条件をつけることで、
    # 「AとB」と「BとA」のような同じ組み合わせの重複を防いでいます。
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            body_a = bodies[i]
            body_b = bodies[j]

            distance = angular_distance(body_a["longitude"], body_b["longitude"])

            # それぞれのアスペクト候補(合・衝・トラインなど)について、
            # 「ぴったりの角度から、どれだけズレているか(オーブ)」を調べ、
            # 許容範囲内であれば「このアスペクトが成立している」とみなします。
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

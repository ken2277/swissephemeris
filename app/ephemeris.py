# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only
# ============================================================================
# app/ephemeris.py
#
# 【このファイルは何をしているの?】
# pyswisseph(Swiss Ephemeris)というライブラリに対して、
# 「天体暦データファイルは、このフォルダに置いてありますよ」と
# 教えてあげるための、準備係のファイルです。
#
# たとえるなら、料理人(pyswisseph)に「食材はこの冷蔵庫に
# 入っているよ」と、冷蔵庫の場所を教えてあげるようなものです。
# 教えておかないと、料理人はどこに食材があるか分からず、
# 簡易的な代用品(Moshierという、やや精度の落ちる計算方法)で
# 代わりに計算してしまいます。
# ============================================================================

from __future__ import annotations

import swisseph as swe

# アプリの中で、この設定が「すでに1回行われたかどうか」を覚えておくための
# 目印(フラグ)です。Webサーバーは1つのアプリを使い回すので、
# 何度も同じ設定をやり直す必要はありません。
_is_configured = False


def configure_ephemeris(ephemeris_path: str) -> None:
    """
    Swiss Ephemeris のデータファイルが置いてあるフォルダの場所を、
    pyswisseph に教えます。

    この関数は、アプリが起動するとき(app/__init__.py の中)で
    1回だけ呼び出されます。
    """
    global _is_configured

    # "set_ephe_path" が、pyswisseph に「探すべきフォルダ」を伝える命令です。
    swe.set_ephe_path(ephemeris_path)
    _is_configured = True


def is_configured() -> bool:
    """設定がすでに行われたかどうかを返します(主に確認・デバッグ用)。"""
    return _is_configured

# Copyright (c) 2026 Ken Kusuki
# SPDX-License-Identifier: AGPL-3.0-only
# app/api_routes.py
#
# Excerpt of app/routes.py from the moonsign-astrology.com site, containing only
# the /api/natal-chart endpoint and its input validation helpers.
# The rest of the site (pages, contact form, map proxy) is intentionally omitted.

from __future__ import annotations

import datetime

from flask import Blueprint, jsonify, request

from .natal_chart import NatalChartError, calculate_natal_chart

bp = Blueprint("main", __name__)


@bp.post("/api/natal-chart")
def api_natal_chart():
    """
    ネイタルチャートの計算をお願いするための、APIの入り口です。

    ブラウザ側のJavaScript(static/js/main.js)が、
    お客さんが入力した「生年月日・時刻・場所」を、
    このURLに向けて "POST"(データを送って処理をお願いする方法)します。

    ここでの仕事は3つだけです。
      1. 送られてきたデータの形が正しいかを確認する(バリデーション)
      2. 正しければ、計算係(natal_chart.py)に計算をお願いする
      3. 計算結果(または、エラーメッセージ)を、JSON形式で送り返す
    """
    # "request.get_json()" で、お客さんのブラウザから送られてきた
    # JSONデータ(データの入った小包のようなもの)を取り出します。
    # "silent=True" は、「もしJSONの形が壊れていても、エラーで
    # プログラムを止めずに、代わりに None を返してください」という指定です。
    payload = request.get_json(silent=True)

    if payload is None or not isinstance(payload, dict):
        return jsonify({"error": "Invalid request format (please send JSON)."}), 400

    try:
        birth_date = _parse_date(payload.get("birth_date"))
        birth_time = _parse_time(payload.get("birth_time"))
        latitude = _parse_float(payload.get("latitude"), "latitude")
        longitude = _parse_float(payload.get("longitude"), "longitude")
    except ValueError as exc:
        # お客さんの入力ミスは、お客さんに直してもらう必要があるエラーなので
        # "400 Bad Request"(あなたのお願いの内容がおかしいです)という
        # 意味の番号をつけて返します。
        return jsonify({"error": str(exc)}), 400

    # 場所の名前(例: "東京都" )は、無くても計算自体はできるので必須にはせず、
    # 長すぎる入力だけ切り詰めて安全にしています。
    place_name = payload.get("place_name")
    if place_name is not None:
        place_name = str(place_name)[:200]

    house_system = payload.get("house_system", "P")
    if not isinstance(house_system, str) or len(house_system) != 1:
        return jsonify({"error": "house_system must be specified as a single letter (e.g., 'P')."}), 400

    try:
        result = calculate_natal_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            place_name=place_name,
            house_system=house_system,
        )
    except NatalChartError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)



def _parse_date(value) -> datetime.date:
    """
    "1990-05-15" のような文字列を、Pythonが日付として扱える
    datetime.date という形に変換します。

    形式が違っていたり、そもそも値が無かったりした場合は、
    お客さんに分かりやすい日本語のエラーメッセージをつけて、
    ValueError(値がおかしい、というエラー)を発生させます。
    """
    if not value:
        raise ValueError("Please provide a birth date (birth_date).")
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("Birth date must be in 'YYYY-MM-DD' format (e.g., 1990-05-15).") from exc


def _parse_time(value) -> datetime.time:
    """"08:30" のような文字列を、datetime.time という形に変換します。"""
    if not value:
        raise ValueError("Please provide a birth time (birth_time).")
    try:
        return datetime.time.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("Birth time must be in 'HH:MM' format (e.g., 08:30).") from exc


def _parse_float(value, field_name: str) -> float:
    """緯度・経度など、数値として送られてくるべき値を、安全に float(小数)に変換します。"""
    if value is None or value == "":
        raise ValueError(f"Please provide {field_name}.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number.") from exc

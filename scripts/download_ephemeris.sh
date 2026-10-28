#!/usr/bin/env bash
# ============================================================================
# download_ephemeris.sh
#
# 【これは何をするプログラム?】
# Swiss Ephemeris(天体の正確な位置データ)のファイルを、
# インターネット上の公式配布元からダウンロードしてきて、
# "ephe" フォルダの中に保存する、お手伝いプログラムです。
#
# シェルスクリプトという種類のプログラムで、Pythonではなく
# 「サーバーのコマンド(呪文)を順番に自動で打ち込んでくれる台本」です。
#
# 【使い方】
#   cd (プロジェクトのフォルダ)
#   bash scripts/download_ephemeris.sh
#
# ============================================================================

# "set -e": もし途中のコマンドが1つでも失敗したら、
#           そこで台本を止める、というおまじないです。
#           (失敗に気づかず、次の処理に進んでしまう事故を防ぎます)
set -e

# ダウンロード先のフォルダ(このスクリプトから見て一つ上の ephe フォルダ)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EPHE_DIR="${SCRIPT_DIR}/../ephe"

# ダウンロード元の公式URL(スイスの Astrodienst 社が無料公開しているデータ)
BASE_URL="https://www.astro.com/ftp/swisseph/ephe"

# ダウンロードするファイルの一覧です。
#   sepl_18.se1  → 太陽・水星~冥王星などの主要な惑星のデータ(西暦1800~2399年)
#   semo_18.se1  → 月の、より細かい動きのデータ(西暦1800~2399年)
#   seas_18.se1  → キロン(小惑星)など、補助的な天体のデータ(西暦1800~2399年)
#
# 「_18」は "1800年から2399年まで" の範囲を表す記号です。
# 世界中のほとんどの利用者(存命の方や、その数十年前のご先祖様まで)の
# 生年月日は、この範囲に収まります。
FILES=(
  "sepl_18.se1"
  "semo_18.se1"
  "seas_18.se1"
)

mkdir -p "${EPHE_DIR}"

echo "Swiss Ephemeris のデータファイルを ${EPHE_DIR} にダウンロードします..."

for FILE in "${FILES[@]}"; do
  DEST="${EPHE_DIR}/${FILE}"

  if [ -f "${DEST}" ]; then
    echo "  - ${FILE} はすでに存在するのでスキップします。"
    continue
  fi

  echo "  - ${FILE} をダウンロード中..."

  # curl があれば curl を、無ければ wget を使う、という保険をかけています。
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${BASE_URL}/${FILE}" -o "${DEST}"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "${BASE_URL}/${FILE}" -O "${DEST}"
  else
    echo "エラー: curl も wget も見つかりません。どちらかをインストールしてください。" >&2
    echo "  例: sudo apt install curl" >&2
    exit 1
  fi

  # ダウンロードしたファイルが空っぽ(0バイト)なら失敗とみなし、削除します。
  if [ ! -s "${DEST}" ]; then
    echo "エラー: ${FILE} のダウンロードに失敗しました(ファイルが空です)。" >&2
    rm -f "${DEST}"
    exit 1
  fi
done

echo "完了しました。以下のファイルが用意されています:"
ls -lh "${EPHE_DIR}"/*.se1

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from flask import Flask, jsonify, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "app.db"

app = Flask(__name__)


@dataclass
class AudioItem:
    id: int
    name: str
    description: str
    level: str
    audio_url: str
    expected_kana: str
    expected_kanji: str


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            level TEXT NOT NULL,
            audio_url TEXT NOT NULL,
            expected_kana TEXT NOT NULL,
            expected_kanji TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM audio_items")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_items = [
            (
                "挨拶 1",
                "日常的な挨拶の練習",
                "N5",
                "/static/audio/sample1.mp3",
                "おはようございます",
                "おはようございます",
            ),
            (
                "買い物 1",
                "買い物で使う表現",
                "N4",
                "/static/audio/sample2.mp3",
                "これください",
                "これ下さい",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO audio_items
            (name, description, level, audio_url, expected_kana, expected_kanji)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_items,
        )
        conn.commit()
    conn.close()


init_db()


def fetch_audio_items() -> list[AudioItem]:
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM audio_items ORDER BY id").fetchall()
    conn.close()
    return [AudioItem(**row) for row in rows]


def normalize_kana(text: str) -> str:
    normalized = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            normalized.append(chr(code - 0x60))
        else:
            normalized.append(ch)
    return "".join(normalized)


def normalize_input(text: str) -> str:
    cleaned = "".join(ch for ch in text.strip() if not ch.isspace())
    cleaned = cleaned.replace("・", "").replace("、", "").replace("。", "")
    return normalize_kana(cleaned)


def is_correct_answer(user_input: str, item: AudioItem) -> bool:
    normalized_input = normalize_input(user_input)
    expected_kana = normalize_input(item.expected_kana)
    expected_kanji = normalize_input(item.expected_kanji)
    return normalized_input in {expected_kana, expected_kanji}


def get_item_by_id(item_id: int) -> AudioItem | None:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM audio_items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return AudioItem(**row)


def upsert_item(data: dict[str, str], item_id: int | None = None) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = (
        data["name"],
        data["description"],
        data["level"],
        data["audio_url"],
        data["expected_kana"],
        data["expected_kanji"],
    )
    if item_id is None:
        cursor.execute(
            """
            INSERT INTO audio_items
            (name, description, level, audio_url, expected_kana, expected_kanji)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            fields,
        )
    else:
        cursor.execute(
            """
            UPDATE audio_items
            SET name = ?, description = ?, level = ?, audio_url = ?, expected_kana = ?, expected_kanji = ?
            WHERE id = ?
            """,
            fields + (item_id,),
        )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    items = fetch_audio_items()
    return render_template("index.html", items=items)


@app.route("/api/audio-items")
def api_audio_items():
    items = [asdict(item) for item in fetch_audio_items()]
    return jsonify(items)


@app.route("/check", methods=["POST"])
def check_answer():
    payload = request.get_json(force=True)
    item_id = int(payload.get("id", 0))
    user_input = payload.get("text", "")
    item = get_item_by_id(item_id)
    if item is None:
        return jsonify({"ok": False, "message": "音频不存在"}), 404
    correct = is_correct_answer(user_input, item)
    return jsonify(
        {
            "ok": True,
            "correct": correct,
            "expected_kana": item.expected_kana,
            "expected_kanji": item.expected_kanji,
        }
    )


@app.route("/admin")
def admin_list():
    items = fetch_audio_items()
    return render_template("admin_list.html", items=items)


@app.route("/admin/new", methods=["GET", "POST"])
def admin_new():
    if request.method == "POST":
        data = {key: request.form.get(key, "").strip() for key in FORM_FIELDS}
        upsert_item(data)
        return redirect(url_for("admin_list"))
    return render_template("admin_edit.html", item=None)


@app.route("/admin/<int:item_id>/edit", methods=["GET", "POST"])
def admin_edit(item_id: int):
    item = get_item_by_id(item_id)
    if item is None:
        return redirect(url_for("admin_list"))
    if request.method == "POST":
        data = {key: request.form.get(key, "").strip() for key in FORM_FIELDS}
        upsert_item(data, item_id=item_id)
        return redirect(url_for("admin_list"))
    return render_template("admin_edit.html", item=item)


@app.route("/admin/<int:item_id>/delete", methods=["POST"])
def admin_delete(item_id: int):
    conn = get_db_connection()
    conn.execute("DELETE FROM audio_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_list"))


FORM_FIELDS = [
    "name",
    "description",
    "level",
    "audio_url",
    "expected_kana",
    "expected_kanji",
]


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

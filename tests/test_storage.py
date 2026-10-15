# tests/test_storage.py
# Tests for saving and loading. They use a temporary folder, so your real
# history and settings are never touched.

import json

from calculator.storage import (
    MAX_HISTORY,
    load_history,
    load_settings,
    save_history,
    save_settings,
)


def test_history_round_trip(tmp_path):
    file = tmp_path / "history.json"
    entries = ["2+3 = 5", "6×7 = 42", "sin(30) = 0.5"]
    save_history(entries, file)
    assert load_history(file) == entries


def test_missing_files_give_empty_results(tmp_path):
    assert load_history(tmp_path / "nothing.json") == []
    assert load_settings(tmp_path / "nothing.json") == {}


def test_damaged_file_does_not_crash(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text("this is not json", encoding="utf-8")
    assert load_history(file) == []
    assert load_settings(file) == {}


def test_history_ignores_bad_entries(tmp_path):
    file = tmp_path / "history.json"
    file.write_text(
        json.dumps(["2+3 = 5", 42, "no equals sign", None, "1+1 = 2"]),
        encoding="utf-8",
    )
    assert load_history(file) == ["2+3 = 5", "1+1 = 2"]


def test_history_keeps_only_the_newest(tmp_path):
    file = tmp_path / "history.json"
    many = [f"{i}+1 = {i + 1}" for i in range(MAX_HISTORY + 20)]
    save_history(many, file)
    loaded = load_history(file)
    assert len(loaded) == MAX_HISTORY
    assert loaded[-1] == many[-1]


def test_settings_round_trip(tmp_path):
    file = tmp_path / "settings.json"
    save_settings({"theme": "dark"}, file)
    assert load_settings(file) == {"theme": "dark"}


def test_settings_with_wrong_type_are_ignored(tmp_path):
    file = tmp_path / "settings.json"
    file.write_text("[1, 2]", encoding="utf-8")
    assert load_settings(file) == {}


def test_saving_creates_missing_folders(tmp_path):
    file = tmp_path / "new" / "folder" / "history.json"
    save_history(["1+1 = 2"], file)
    assert file.exists()


def test_symbols_are_saved_readably(tmp_path):
    file = tmp_path / "history.json"
    save_history(["6×7 = 42"], file)
    assert "×" in file.read_text(encoding="utf-8")
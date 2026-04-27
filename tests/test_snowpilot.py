"""Tests for SnowPilot/CAAML parser helpers."""

from pathlib import Path

from snowpyt_mechparams import snowpilot


def test_parse_caaml_directory_defaults_to_xml_files(tmp_path, monkeypatch):
    """The default pattern should parse only XML files, deterministically."""
    (tmp_path / "b.xml").write_text("<xml />")
    (tmp_path / "a.xml").write_text("<xml />")
    (tmp_path / "notes.txt").write_text("skip me")

    seen = []

    def fake_parser(filepath):
        seen.append(Path(filepath).name)
        return Path(filepath).name

    monkeypatch.setattr(snowpilot, "caaml_parser", fake_parser)

    result = snowpilot.parse_caaml_directory(str(tmp_path))

    assert result == ["a.xml", "b.xml"]
    assert seen == ["a.xml", "b.xml"]


def test_parse_caaml_directory_honors_custom_pattern(tmp_path, monkeypatch):
    """Callers should be able to narrow parsing with the pattern argument."""
    (tmp_path / "profile.caaml.xml").write_text("<xml />")
    (tmp_path / "profile.xml").write_text("<xml />")

    monkeypatch.setattr(
        snowpilot,
        "caaml_parser",
        lambda filepath: Path(filepath).name,
    )

    result = snowpilot.parse_caaml_directory(
        str(tmp_path),
        pattern="*.caaml.xml",
    )

    assert result == ["profile.caaml.xml"]


def test_parse_caaml_directory_skips_failed_files(tmp_path, monkeypatch):
    """Files that fail parsing should be skipped without aborting the directory."""
    (tmp_path / "bad.xml").write_text("<xml />")
    (tmp_path / "good.xml").write_text("<xml />")

    def fake_parser(filepath):
        name = Path(filepath).name
        if name == "bad.xml":
            raise ValueError("broken")
        return name

    monkeypatch.setattr(snowpilot, "caaml_parser", fake_parser)

    result = snowpilot.parse_caaml_directory(str(tmp_path))

    assert result == ["good.xml"]

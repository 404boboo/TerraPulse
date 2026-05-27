from __future__ import annotations

from pathlib import Path

import pytest

from src import report_pipeline


SAMPLE_CSV_PATH = Path(__file__).parent.parent / "data" / "Sample_mission_log.csv"


def test_export_creates_markdown_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    output_path = report_pipeline.export_mission_report(
        SAMPLE_CSV_PATH,
        output_dir=output_dir,
    )

    assert output_path.exists()
    assert output_path.suffix == ".md"
    assert output_path.parent == output_dir


def test_export_returns_existing_path_and_report_content(tmp_path: Path) -> None:
    output_path = report_pipeline.export_mission_report(
        SAMPLE_CSV_PATH,
        output_dir=tmp_path / "reports",
    )

    report_text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "TerraPulse Mission Report" in report_text
    assert "Risk" in report_text
    assert "rear left calf" in report_text or "front left" in report_text


def test_export_uses_custom_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "custom_reports"

    output_path = report_pipeline.export_mission_report(
        SAMPLE_CSV_PATH,
        output_dir=output_dir,
        output_filename="mission.md",
    )

    assert output_path == output_dir / "mission.md"
    assert output_path.exists()


def test_export_uses_default_filename_from_csv_stem(tmp_path: Path) -> None:
    output_path = report_pipeline.export_mission_report(
        SAMPLE_CSV_PATH,
        output_dir=tmp_path,
    )

    assert output_path.name == "Sample_mission_log_report.md"


def test_export_missing_csv_path_raises_file_not_found_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        report_pipeline.export_mission_report(missing_path)
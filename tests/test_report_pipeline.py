from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src import report_pipeline


def _sample_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "sample_mission_log.csv"
    df = pd.DataFrame(
        {
            "timestamp": [
                "2026-05-25T10:00:00Z",
                "2026-05-25T10:00:01Z",
            ],
            "battery_percentage": [92.0, 91.5],
            "mission_status": ["ok", "warning"],
        }
    )
    df.to_csv(csv_path, index=False)
    return csv_path


def test_export_creates_markdown_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = _sample_csv(tmp_path)
    output_dir = tmp_path / "reports"

    monkeypatch.setattr(report_pipeline.mission_loader, "load_mission_data", lambda _: pd.read_csv(csv_path), raising=False)
    monkeypatch.setattr(report_pipeline.risk_scorer, "calculate_route_risk", lambda _: {"risk_score": 42, "risk_level": "moderate", "reasons": ["Battery margin is reduced."], "metrics": {"battery_percentage": 91.5}}, raising=False)
    monkeypatch.setattr(report_pipeline.event_analyzer, "analyze_events", lambda _: [{"event_type": "temperature_spike", "severity": "warning", "joint_label": "front left calf", "start_time": "2026-05-25T10:00:01Z", "end_time": "2026-05-25T10:00:02Z", "duration_seconds": 1.0, "peak_value": 71.2, "threshold": 70.0}], raising=False)
    monkeypatch.setattr(report_pipeline.event_analyzer, "summarize_events", lambda events: {"temperature_spike": {"count": len(events), "duration_seconds": 1.0}}, raising=False)

    output_path = report_pipeline.export_mission_report(csv_path, output_dir=output_dir)

    assert output_path.exists()
    assert output_path.suffix == ".md"
    assert output_path.parent == output_dir


def test_export_returns_existing_path_and_report_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = _sample_csv(tmp_path)

    monkeypatch.setattr(report_pipeline.mission_loader, "load_mission_data", lambda _: pd.read_csv(csv_path), raising=False)
    monkeypatch.setattr(report_pipeline.risk_scorer, "calculate_route_risk", lambda _: {"risk_score": 42, "risk_level": "moderate", "reasons": ["Battery margin is reduced."], "metrics": {"battery_percentage": 91.5}}, raising=False)
    monkeypatch.setattr(report_pipeline.event_analyzer, "analyze_events", lambda _: [{"event_type": "temperature_spike", "severity": "warning", "joint_label": "front left calf", "start_time": "2026-05-25T10:00:01Z", "end_time": "2026-05-25T10:00:02Z", "duration_seconds": 1.0, "peak_value": 71.2, "threshold": 70.0}], raising=False)
    monkeypatch.setattr(report_pipeline.event_analyzer, "summarize_events", lambda events: {"temperature_spike": {"count": len(events), "duration_seconds": 1.0}}, raising=False)

    output_path = report_pipeline.export_mission_report(csv_path, output_dir=tmp_path / "reports")
    report_text = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "TerraPulse Mission Report" in report_text
    assert "Risk score: 42" in report_text
    assert "Risk level: moderate" in report_text
    assert "front left calf" in report_text


def test_export_uses_custom_output_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = _sample_csv(tmp_path)
    output_dir = tmp_path / "custom_reports"

    monkeypatch.setattr(report_pipeline.mission_loader, "load_mission_data", lambda _: pd.read_csv(csv_path), raising=False)
    monkeypatch.setattr(report_pipeline.risk_scorer, "calculate_route_risk", lambda _: {"risk_score": 10, "risk_level": "low", "reasons": [], "metrics": {}}, raising=False)
    monkeypatch.setattr(report_pipeline.event_analyzer, "analyze_events", lambda _: [], raising=False)
    monkeypatch.setattr(report_pipeline.event_analyzer, "summarize_events", lambda events: {}, raising=False)

    output_path = report_pipeline.export_mission_report(csv_path, output_dir=output_dir, output_filename="mission.md")

    assert output_path == output_dir / "mission.md"
    assert output_path.exists()


def test_export_missing_csv_path_raises_file_not_found_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        report_pipeline.export_mission_report(missing_path)

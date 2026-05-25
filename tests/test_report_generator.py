from __future__ import annotations

import pandas as pd

from src.report_generator import generate_markdown_report


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [
                "2026-05-24T10:00:00Z",
                "2026-05-24T10:00:01Z",
                "2026-05-24T10:00:02Z",
            ],
            "mission_status": ["ok", "ok", "warning"],
            "battery_percentage": [92.5, 92.1, 91.9],
        }
    )


def _sample_risk_result() -> dict[str, object]:
    return {
        "risk_score": 78,
        "risk_level": "high",
        "reasons": [
            "Low battery margin during the second half of the mission.",
            "Front left calf temperature exceeded the preferred operating band.",
        ],
        "metrics": {
            "battery_percentage": 91.9,
            "joint_temperature": 71.2,
            "joint_current": 14.8,
            "total_current": 81.4,
        },
    }


def _sample_events() -> list[dict[str, object]]:
    return [
        {
            "event_type": "temperature_spike",
            "severity": "warning",
            "joint_label": "front left calf",
            "start_time": "2026-05-24T10:00:01Z",
            "end_time": "2026-05-24T10:00:02Z",
            "duration_seconds": 1.0,
            "peak_value": 71.2,
            "threshold": 70.0,
        }
    ]


def _sample_event_summary() -> dict[str, dict[str, object]]:
    return {
        "temperature_spike": {"count": 1, "duration_seconds": 1.0},
        "current_spike": {"count": 0, "duration_seconds": 0.0},
    }


def test_generate_markdown_report_returns_string() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), _sample_events(), _sample_event_summary())

    assert isinstance(report, str)


def test_generate_markdown_report_includes_title() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), _sample_events(), _sample_event_summary())

    assert "# TerraPulse Mission Report" in report


def test_generate_markdown_report_includes_risk_score_and_level() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), _sample_events(), _sample_event_summary())

    assert "Risk score: 78" in report
    assert "Risk level: high" in report


def test_generate_markdown_report_includes_risk_reasons() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), _sample_events(), _sample_event_summary())

    assert "Low battery margin during the second half of the mission." in report
    assert "Front left calf temperature exceeded the preferred operating band." in report


def test_generate_markdown_report_includes_joint_label_from_events() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), _sample_events(), _sample_event_summary())

    assert "front left calf" in report


def test_generate_markdown_report_includes_event_duration() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), _sample_events(), _sample_event_summary())

    assert "1" in report
    assert "Duration (s)" in report


def test_generate_markdown_report_handles_no_events_without_crashing() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), [], {})

    assert "No joint-level events were detected." in report
    assert "No summary data was supplied." in report


def test_generate_markdown_report_includes_engineering_recommendations() -> None:
    report = generate_markdown_report(_sample_df(), _sample_risk_result(), _sample_events(), _sample_event_summary())

    assert "Engineering Recommendations" in report
    assert "follow-up inspection" in report


def test_generate_markdown_report_handles_empty_risk_reasons() -> None:
    risk_result = _sample_risk_result()
    risk_result["reasons"] = []

    report = generate_markdown_report(_sample_df(), risk_result, _sample_events(), _sample_event_summary())

    assert "No explicit risk reasons were recorded." in report


def test_generate_markdown_report_handles_partial_event_summary_entries() -> None:
    report = generate_markdown_report(
        _sample_df(),
        _sample_risk_result(),
        _sample_events(),
        {"temperature_spike": {"count": 1}},
    )

    assert "temperature_spike" in report
    assert "Count" in report

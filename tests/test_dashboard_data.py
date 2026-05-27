from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import dashboard_data


def _sample_mission_df() -> pd.DataFrame:
    data = {
        "mission_time_s": [0.0, 1.0],
        "battery_percent": [95.0, 94.0],
        "total_current_a": [18.0, 26.0],
        "terrain_slope_deg": [3.0, 8.0],
        "signal_strength_percent": [98.0, 92.0],
    }

    for column in dashboard_data.get_joint_metric_columns("temp_c"):
        data[column] = [40.0, 72.0 if column == "fl_calf_temp_c" else 42.0]
    for column in dashboard_data.get_joint_metric_columns("current_a"):
        data[column] = [2.0, 3.0]
    for column in dashboard_data.get_joint_metric_columns("torque_nm"):
        data[column] = [8.0, 9.0]

    return pd.DataFrame(data)


def test_prepare_dashboard_data_returns_expected_keys(monkeypatch) -> None:
    mission_df = _sample_mission_df()
    events = [
        {
            "event_type": "temperature_spike",
            "severity": "warning",
            "joint_label": "front left calf",
            "duration_seconds": 1.0,
        }
    ]
    event_summary = {"temperature_spike": {"count": 1, "duration_seconds": 1.0}}
    risk_result = {
        "risk_score": 64,
        "risk_level": "moderate",
        "reasons": ["Joint temperature elevated."],
        "metrics": {"max_joint_temperature": 72.0},
    }

    monkeypatch.setattr(dashboard_data, "load_mission_log", lambda csv_path: mission_df)
    monkeypatch.setattr(dashboard_data, "calculate_risk_score", lambda df: risk_result)
    monkeypatch.setattr(dashboard_data, "analyze_joint_events", lambda df: events)
    monkeypatch.setattr(dashboard_data, "summarize_events", lambda items: event_summary)

    result = dashboard_data.prepare_dashboard_data(Path("mission.csv"))

    assert set(result) == {
        "mission_df",
        "risk_result",
        "events",
        "event_summary",
        "events_df",
        "event_summary_df",
        "metric_cards",
    }
    assert not result["mission_df"].empty
    assert {"risk_score", "risk_level", "reasons", "metrics"}.issubset(result["risk_result"])
    assert isinstance(result["events"], list)
    assert isinstance(result["event_summary"], dict)
    assert isinstance(result["events_df"], pd.DataFrame)
    assert isinstance(result["event_summary_df"], pd.DataFrame)
    assert result["metric_cards"]["risk_score"] == 64
    assert result["metric_cards"]["event_count"] == 1


def test_build_events_dataframe_returns_dataframe_for_empty_events() -> None:
    events_df = dashboard_data.build_events_dataframe([])

    assert isinstance(events_df, pd.DataFrame)
    assert events_df.empty


def test_get_joint_metric_columns_returns_12_columns_for_each_joint_metric() -> None:
    assert len(dashboard_data.get_joint_metric_columns("temp_c")) == 12
    assert len(dashboard_data.get_joint_metric_columns("current_a")) == 12
    assert len(dashboard_data.get_joint_metric_columns("torque_nm")) == 12

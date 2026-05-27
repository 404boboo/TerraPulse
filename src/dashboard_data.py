from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.event_analyzer import analyze_joint_events, summarize_events
from src.mission_loader import load_mission_log
from src.risk_scorer import calculate_risk_score

try:
    from src.mission_loader import JOINTS
except ImportError:  # pragma: no cover - kept for older module layouts
    JOINTS = [
        "fl_hip",
        "fl_thigh",
        "fl_calf",
        "fr_hip",
        "fr_thigh",
        "fr_calf",
        "rl_hip",
        "rl_thigh",
        "rl_calf",
        "rr_hip",
        "rr_thigh",
        "rr_calf",
    ]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, dict):
            return converted
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return [value.to_dict()]
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _get_first(mapping: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def _safe_min(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    value = pd.to_numeric(df[column], errors="coerce").min()
    return None if pd.isna(value) else float(value)


def _safe_min_from_candidates(df: pd.DataFrame, columns: tuple[str, ...]) -> float | None:
    for column in columns:
        value = _safe_min(df, column)
        if value is not None:
            return value
    return None


def _safe_max(df: pd.DataFrame, column: str) -> float | None:
    if column not in df.columns:
        return None
    value = pd.to_numeric(df[column], errors="coerce").max()
    return None if pd.isna(value) else float(value)


def _safe_max_from_candidates(df: pd.DataFrame, columns: tuple[str, ...]) -> float | None:
    for column in columns:
        value = _safe_max(df, column)
        if value is not None:
            return value
    return None


def get_joint_metric_columns(metric: str) -> list[str]:
    return [f"{joint}_{metric}" for joint in JOINTS]


def build_events_dataframe(events: Any) -> pd.DataFrame:
    event_rows = [_as_dict(event) for event in _as_list(events)]
    event_rows = [row for row in event_rows if row]
    return pd.DataFrame(event_rows)


def build_event_summary_dataframe(event_summary: Any) -> pd.DataFrame:
    summary = _as_dict(event_summary)
    rows: list[dict[str, Any]] = []

    for event_type, details in summary.items():
        if isinstance(details, dict):
            row = {"event_type": event_type, **details}
        else:
            row = {"event_type": event_type, "count": details}
        rows.append(row)

    return pd.DataFrame(rows)


def get_key_metric_cards(
    mission_df: pd.DataFrame,
    risk_result: Any,
    events: Any | None = None,
) -> dict[str, Any]:
    risk = _as_dict(risk_result)
    risk_score = _get_first(risk, ("risk_score", "score"))
    risk_level = _get_first(risk, ("risk_level", "level"))

    joint_temp_columns = [
        column for column in get_joint_metric_columns("temp_c") if column in mission_df.columns
    ]
    max_joint_temp = None
    if joint_temp_columns:
        max_value = mission_df[joint_temp_columns].apply(pd.to_numeric, errors="coerce").max().max()
        max_joint_temp = None if pd.isna(max_value) else float(max_value)

    event_count = len(_as_list(events)) if events is not None else 0

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "minimum_battery": _safe_min_from_candidates(
            mission_df,
            ("battery_percent", "battery_percentage"),
        ),
        "maximum_total_current": _safe_max_from_candidates(
            mission_df,
            ("total_current_a", "total_current"),
        ),
        "maximum_terrain_slope": _safe_max(mission_df, "terrain_slope_deg"),
        "minimum_signal_strength": _safe_min(mission_df, "signal_strength_percent"),
        "maximum_joint_temperature": max_joint_temp,
        "event_count": event_count,
    }


def prepare_dashboard_data(csv_path: Path | str) -> dict[str, Any]:
    mission_df = load_mission_log(csv_path)
    risk_result = calculate_risk_score(mission_df)
    events = analyze_joint_events(mission_df)
    event_summary = summarize_events(events)

    return {
        "mission_df": mission_df,
        "risk_result": risk_result,
        "events": _as_list(events),
        "event_summary": _as_dict(event_summary),
        "events_df": build_events_dataframe(events),
        "event_summary_df": build_event_summary_dataframe(event_summary),
        "metric_cards": get_key_metric_cards(mission_df, risk_result, events),
    }

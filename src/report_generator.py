from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

try:
    import pandas as pd
except Exception:  # pragma: no cover - pandas is expected in the project env
    pd = None  # type: ignore[assignment]


MISSION_TITLE = "TerraPulse Mission Report"


def _to_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            converted = value.to_dict()
            if isinstance(converted, Mapping):
                return dict(converted)
        except Exception:
            return {}
    return {}


def _get_first_present(mapping: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if pd is not None:
        if isinstance(value, pd.DataFrame):
            return value.to_dict(orient="records")
        if isinstance(value, pd.Series):
            return [value.to_dict()]
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if hasattr(value, "tolist"):
        try:
            converted = value.tolist()
            if isinstance(converted, list):
                return converted
        except Exception:
            return [value]
    return [value]


def _format_value(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _format_timestamp(value: Any) -> str:
    if value is None:
        return "N/A"
    if pd is not None:
        try:
            timestamp = pd.to_datetime(value)
            if pd.isna(timestamp):
                return _format_value(value)
            return timestamp.isoformat(sep=" ", timespec="seconds")
        except Exception:
            return _format_value(value)
    return _format_value(value)


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    header_row = " | ".join(headers)
    separator = " | ".join(["---"] * len(headers))
    lines = [f"| {header_row} |", f"| {separator} |"]
    for row in rows:
        cells = [_format_value(cell) for cell in row]
        lines.append(f"| {' | '.join(cells)} |")
    return "\n".join(lines)


def generate_mission_summary(df: Any) -> str:
    if df is None:
        sample_count = 0
        columns: list[str] = []
        start_time = None
        end_time = None
        mission_status = None
    else:
        sample_count = len(df)
        columns = list(getattr(df, "columns", []))
        time_columns = ["timestamp", "time", "datetime", "recorded_at", "sample_time"]
        status_columns = ["mission_status", "status"]

        start_time = None
        end_time = None
        for column in time_columns:
            if column in columns:
                series = df[column]
                try:
                    times = pd.to_datetime(series) if pd is not None else series
                    start_time = times.min()
                    end_time = times.max()
                except Exception:
                    start_time = series.iloc[0] if len(series) else None
                    end_time = series.iloc[-1] if len(series) else None
                break

        mission_status = None
        for column in status_columns:
            if column in columns and len(df[column]):
                unique_values = [value for value in df[column].dropna().unique().tolist() if value is not None]
                if unique_values:
                    mission_status = ", ".join(_format_value(value) for value in unique_values[:3])
                break

    lines = ["## Mission Summary", ""]
    lines.append(f"- Samples analyzed: {_format_value(sample_count)}")
    lines.append(f"- Start time: {_format_timestamp(start_time)}")
    lines.append(f"- End time: {_format_timestamp(end_time)}")
    if mission_status:
        lines.append(f"- Mission status: {mission_status}")
    if columns:
        lines.append(f"- Telemetry fields: {_format_value(len(columns))}")
    return "\n".join(lines)


def generate_risk_section(risk_result: Any) -> str:
    risk = _to_mapping(risk_result)
    score = _get_first_present(risk, ["risk_score", "score"])
    level = _get_first_present(risk, ["risk_level", "level"])
    reasons = _to_list(risk.get("reasons") or risk.get("risk_reasons"))

    lines = ["## Route Risk", ""]
    lines.append(f"- Risk score: {_format_value(score)}")
    lines.append(f"- Risk level: {_format_value(level)}")
    lines.append("")
    lines.append("### Risk Reasons")
    if reasons:
        for reason in reasons:
            lines.append(f"- {_format_value(reason)}")
    else:
        lines.append("- No explicit risk reasons were recorded.")
    return "\n".join(lines)


def generate_metrics_section(risk_result: Any) -> str:
    risk = _to_mapping(risk_result)
    metrics = risk.get("metrics")
    metric_items: list[tuple[str, Any]] = []

    if isinstance(metrics, Mapping):
        metric_items.extend(metrics.items())
    else:
        preferred_keys = [
            "battery_percentage",
            "joint_temperature",
            "joint_current",
            "joint_torque",
            "total_current",
            "terrain_slope",
            "signal_strength",
        ]
        for key in preferred_keys:
            if key in risk:
                metric_items.append((key, risk[key]))

    lines = ["## Key Metrics", ""]
    if metric_items:
        rows = [(name.replace("_", " ").title(), value) for name, value in metric_items]
        lines.append(_markdown_table(["Metric", "Value"], rows))
    else:
        lines.append("- No key metrics were supplied.")
    return "\n".join(lines)


def generate_events_section(events: Any) -> str:
    event_list = _to_list(events)

    lines = ["## Detailed Joint Events", ""]
    if not event_list:
        lines.append("- No joint-level events were detected.")
        return "\n".join(lines)

    rows = []
    for event in event_list:
        event_map = _to_mapping(event)
        rows.append(
            [
                _get_first_present(event_map, ["event_type", "type"]),
                _get_first_present(event_map, ["severity"]),
                _get_first_present(event_map, ["joint_label", "joint", "label"]),
                _format_timestamp(_get_first_present(event_map, ["start_time", "start"])),
                _format_timestamp(_get_first_present(event_map, ["end_time", "end"])),
                _get_first_present(event_map, ["duration_seconds", "duration"]),
                _get_first_present(event_map, ["peak_value", "peak"]),
                _get_first_present(event_map, ["threshold"]),
            ]
        )

    lines.append(
        _markdown_table(
            [
                "Event Type",
                "Severity",
                "Joint Label",
                "Start Time",
                "End Time",
                "Duration (s)",
                "Peak Value",
                "Threshold",
            ],
            rows,
        )
    )
    return "\n".join(lines)


def generate_event_summary_section(event_summary: Any) -> str:
    summary = _to_mapping(event_summary)
    lines = ["## Event Summary", ""]
    if not summary:
        lines.append("- No summary data was supplied.")
        return "\n".join(lines)

    rows = []
    for event_type, details in summary.items():
        if isinstance(details, Mapping):
            count = details.get("count", details.get("event_count"))
            duration = details.get("duration_seconds", details.get("total_duration_seconds"))
            rows.append([event_type, count, duration])
        else:
            rows.append([event_type, details, None])

    lines.append(_markdown_table(["Event Type", "Count", "Duration (s)"], rows))
    return "\n".join(lines)


def generate_engineering_recommendations(
    risk_result: Any,
    events: Any,
    event_summary: Any,
) -> str:
    risk = _to_mapping(risk_result)
    reasons = _to_list(risk.get("reasons") or risk.get("risk_reasons"))
    risk_level = str(_get_first_present(risk, ["risk_level", "level"]) or "").lower()
    event_list = _to_list(events)
    summary = _to_mapping(event_summary)

    recommendations: list[str] = []

    if risk_level in {"critical", "high"}:
        recommendations.append("Review the mission before re-running the route in the field.")
    if any("battery" in str(reason).lower() for reason in reasons):
        recommendations.append("Check battery health, charge state, and power draw trends before the next sortie.")
    if any("temperature" in str(reason).lower() or "overheat" in str(reason).lower() for reason in reasons):
        recommendations.append("Inspect joint cooling, lubrication, and duty cycle limits on the affected limb.")
    if any("current" in str(reason).lower() or "torque" in str(reason).lower() for reason in reasons):
        recommendations.append("Inspect actuator load paths and verify that the affected joint is moving freely.")
    if any("signal" in str(reason).lower() for reason in reasons):
        recommendations.append("Review communications quality and antenna placement in the affected field area.")
    if not event_list and not recommendations:
        recommendations.append("No abnormal joint events were detected; retain the mission as a baseline reference.")
    else:
        affected_joints = []
        for event in event_list:
            event_map = _to_mapping(event)
            joint_label = _get_first_present(event_map, ["joint_label", "joint", "label"])
            if joint_label:
                affected_joints.append(str(joint_label))
        if affected_joints:
            unique_joints = list(dict.fromkeys(affected_joints))
            recommendations.append(
                f"Prioritize follow-up inspection of: {', '.join(unique_joints)}."
            )

    if summary and not any("baseline" in item.lower() for item in recommendations):
        high_count = []
        for event_type, details in summary.items():
            count = details.get("count") if isinstance(details, Mapping) else details
            if isinstance(count, (int, float)) and count > 0:
                high_count.append(str(event_type))
        if high_count:
            recommendations.append(
                f"Track recurrence of the following event classes across future missions: {', '.join(high_count)}."
            )

    unique_recommendations = list(dict.fromkeys(recommendations))

    lines = ["## Engineering Recommendations", ""]
    for recommendation in unique_recommendations:
        lines.append(f"- {recommendation}")
    if not unique_recommendations:
        lines.append("- No additional engineering actions were identified.")
    return "\n".join(lines)


def generate_markdown_report(
    df: Any,
    risk_result: Any,
    events: Any,
    event_summary: Any,
) -> str:
    sections = [
        f"# {MISSION_TITLE}",
        "",
        generate_mission_summary(df),
        "",
        generate_risk_section(risk_result),
        "",
        generate_metrics_section(risk_result),
        "",
        generate_events_section(events),
        "",
        generate_event_summary_section(event_summary),
        "",
        generate_engineering_recommendations(risk_result, events, event_summary),
        "",
    ]
    return "\n".join(sections).strip() + "\n"

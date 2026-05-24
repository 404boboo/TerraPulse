import pandas as pd
from src.mission_loader import JOINTS, get_joint_cols


def format_joint_name(joint: str) -> str:

    leg_map = {
        "fl": "front left",
        "fr": "front right",
        "rl": "rear left",
        "rr": "rear right",
    }

    leg_code, joint_code = joint.split("_", 1)

    return f"{leg_map[leg_code]} {joint_code}"

def build_joint_events(df: pd.DataFrame, metric: str, threshold: float, event_type: str, severity: str, comparison: str = "above",
) -> list[dict]:
    events = []
    metric_cols = get_joint_cols(metric)

    for col in metric_cols:
        joint = col.replace(f"_{metric}", "")

        if comparison == "above":
            condition = df[col] > threshold
        else:
            condition = df[col] < threshold

        active_event_start = None
        active_event_rows = []

        for index, is_active in condition.items():
            row = df.loc[index]

            if is_active and active_event_start is None:
                active_event_start = row
                active_event_rows = [row]
            elif is_active:
                active_event_rows.append(row)
            elif active_event_start is not None:
                events.append(_create_event(joint=joint, metric=metric, threshold=threshold, event_type=event_type, severity=severity, rows=active_event_rows, comparison=comparison))
                active_event_start = None
                active_event_rows = []

        if active_event_start is not None:
            events.append(_create_event(joint=joint, metric=metric, threshold=threshold, event_type=event_type, severity=severity, rows=active_event_rows, comparison=comparison))  
    
    return events


def _create_event(joint: str, metric: str, threshold: float, event_type: str, severity: str, rows: list[pd.Series], comparison: str) -> dict:
    start_row = rows[0]
    end_row = rows[-1]

    values = [float(row[f"{joint}_{metric}"]) for row in rows]

    if comparison == "above":
        peak_value = max(values)
    else:
        peak_value = min(values)

    duration_s = int(end_row["mission_time_s"] - start_row["mission_time_s"])

    return {
        "event_type": event_type,
        "severity": severity,
        "joint": joint,
        "joint_label": format_joint_name(joint),
        "metric": metric,
        "threshold": threshold,
        "comparison": comparison,
        "start_time": start_row["timestamp"],
        "end_time": end_row["timestamp"],
        "start_mission_time_s": int(start_row["mission_time_s"]),
        "end_mission_time_s": int(end_row["mission_time_s"]),
        "duration_s": duration_s,
        "sample_count": len(rows),
        "peak_value": peak_value,
    }

def analyze_joint_events(df: pd.DataFrame) -> list[dict]:
    events = []

    events.extend(build_joint_events(
        df=df,
        metric="temp_c",
        threshold=80,
        event_type="High Joint Temperature",
        severity="WARNING",
    ))

    events.extend(build_joint_events(
        df=df,
        metric="temp_c",
        threshold=90,
        event_type="Critical Joint Overheating",
        severity="CRITICAL",
    ))

    events.extend(build_joint_events(
        df=df,
        metric="current_a",
        threshold=5,
        event_type="High Joint Current",
        severity="WARNING",
    ))

    events.extend(build_joint_events(
        df=df,
        metric="torque_nm",
        threshold=35,
        event_type="High Joint Torque",
        severity="WARNING",
    ))

    return sorted(events, key=lambda event: event["start_mission_time_s"])


def summarize_events(events: list[dict]) -> dict:
    summary = {}

    for event in events:
        key = (event["event_type"], event["joint"])

        if key not in summary:
            summary[key] = {
                "event_type": event["event_type"],
                "joint": event["joint"],
                "joint_label": event["joint_label"],
                "severity": event["severity"],
                "count": 0,
                "total_duration_s": 0,
                "peak_value": event["peak_value"],
            }

        summary[key]["count"] += 1
        summary[key]["total_duration_s"] += event["duration_s"]
        summary[key]["peak_value"] = max(summary[key]["peak_value"], event["peak_value"])

    return {
        f"{event_type}:{joint}": value
        for (event_type, joint), value in summary.items()
    }
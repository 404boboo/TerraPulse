import pandas as pd

from src.event_analyzer import analyze_joint_events, format_joint_name, summarize_events
from src.mission_loader import JOINTS


def build_test_df(**overrides):
    base = {
        "timestamp": ["00:00", "00:30", "01:00", "01:30"],
        "mission_time_s": [0, 30, 60, 90],
    }

    for joint in JOINTS:
        base[f"{joint}_temp_c"] = [40, 45, 50, 55]
        base[f"{joint}_current_a"] = [0.5, 0.8, 1.0, 1.2]
        base[f"{joint}_torque_nm"] = [5.0, 8.0, 10.0, 12.0]

    base.update(overrides)

    return pd.DataFrame(base)


def test_format_joint_name():
    assert format_joint_name("fl_hip") == "front left hip"
    assert format_joint_name("rr_calf") == "rear right calf"


def test_analyze_joint_events_identifies_specific_joint():
    df = build_test_df(
        rl_calf_temp_c=[70, 82, 91, 88],
    )

    events = analyze_joint_events(df)

    assert any(event["joint"] == "rl_calf" for event in events)
    assert any(event["joint_label"] == "rear left calf" for event in events)


def test_analyze_joint_events_tracks_start_and_end_time():
    df = build_test_df(
        rl_calf_temp_c=[70, 82, 91, 88],
    )

    events = analyze_joint_events(df)

    high_temp_event = next(
        event for event in events
        if event["event_type"] == "High Joint Temperature"
        and event["joint"] == "rl_calf"
    )

    assert high_temp_event["start_time"] == "00:30"
    assert high_temp_event["end_time"] == "01:30"
    assert high_temp_event["duration_s"] == 60
    assert high_temp_event["sample_count"] == 3
    assert high_temp_event["peak_value"] == 91


def test_analyze_joint_events_detects_critical_overheating():
    df = build_test_df(
        rl_calf_temp_c=[70, 82, 91, 88],
    )

    events = analyze_joint_events(df)

    critical_event = next(
        event for event in events
        if event["event_type"] == "Critical Joint Overheating"
        and event["joint"] == "rl_calf"
    )

    assert critical_event["start_time"] == "01:00"
    assert critical_event["end_time"] == "01:00"
    assert critical_event["duration_s"] == 0
    assert critical_event["peak_value"] == 91


def test_summarize_events_counts_repeated_events():
    df = build_test_df(
        rl_calf_current_a=[6.0, 1.0, 6.5, 1.0],
    )

    events = analyze_joint_events(df)
    summary = summarize_events(events)

    key = "High Joint Current:rl_calf"

    assert key in summary
    assert summary[key]["count"] == 2
    assert summary[key]["joint_label"] == "rear left calf"
    assert summary[key]["peak_value"] == 6.5
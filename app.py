from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard_data import get_joint_metric_columns, prepare_dashboard_data
from src.report_pipeline import export_mission_report


DEFAULT_CSV_PATH = Path("data/Sample_mission_log.csv")


def _format_metric(value: object, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if isinstance(value, float):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _first_available(df: pd.DataFrame, columns: list[str]) -> str | None:
    for column in columns:
        if column in df.columns:
            return column
    return None


def _mission_duration(df: pd.DataFrame) -> float | None:
    if "mission_time_s" not in df.columns:
        return None
    times = pd.to_numeric(df["mission_time_s"], errors="coerce")
    duration = times.max() - times.min()
    return None if pd.isna(duration) else float(duration)


def _risk_reasons(risk_result: object) -> list[str]:
    risk = _as_dict(risk_result)
    reasons = risk.get("reasons") or risk.get("risk_reasons") or []
    if isinstance(reasons, list):
        return [str(reason) for reason in reasons]
    return [str(reasons)]


def _mission_status_summary(dashboard: dict[str, object]) -> str:
    cards = _as_dict(dashboard["metric_cards"])
    risk_level = cards.get("risk_level") or "unknown"
    event_count = cards.get("event_count") or 0
    duration = _mission_duration(dashboard["mission_df"])
    duration_text = f"{duration:.1f} s" if duration is not None else "unknown duration"

    if event_count:
        return (
            f"Mission replay covers {duration_text} with {event_count} detected joint-level "
            f"event(s). Current route risk is {risk_level}."
        )
    return f"Mission replay covers {duration_text} with no detected joint-level events. Current route risk is {risk_level}."


def _plot_line(df: pd.DataFrame, y: str | list[str], title: str, y_label: str) -> None:
    if "mission_time_s" not in df.columns:
        st.info(f"{title} requires mission_time_s telemetry.")
        return

    required = [y] if isinstance(y, str) else y
    available = [column for column in required if column in df.columns]
    if not available:
        st.info(f"{title} telemetry is not available in this mission export.")
        return

    fig = px.line(
        df,
        x="mission_time_s",
        y=available,
        title=title,
        labels={"mission_time_s": "Mission time (s)", "value": y_label},
    )
    fig.update_layout(legend_title_text="Signal", margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _plot_route(df: pd.DataFrame) -> None:
    if "x_m" not in df.columns or "y_m" not in df.columns:
        st.info("Route plot requires x_m and y_m telemetry.")
        return

    hover_data = [column for column in ("mission_time_s", "waypoint", "status") if column in df.columns]
    text = "waypoint" if "waypoint" in df.columns else None
    fig = px.line(
        df,
        x="x_m",
        y="y_m",
        text=text,
        hover_data=hover_data,
        markers=True,
        title="2D Mission Route",
        labels={"x_m": "X position (m)", "y_m": "Y position (m)"},
    )
    fig.update_traces(textposition="top center")
    if not df.empty:
        fig.add_trace(
            go.Scatter(
                x=[df["x_m"].iloc[0]],
                y=[df["y_m"].iloc[0]],
                mode="markers",
                marker=dict(color="#1f7a3f", size=12, symbol="circle"),
                name="Start",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[df["x_m"].iloc[-1]],
                y=[df["y_m"].iloc[-1]],
                mode="markers",
                marker=dict(color="#b42318", size=12, symbol="x"),
                name="End",
            )
        )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _show_metric_cards(cards: dict[str, object]) -> None:
    labels = [
        ("Risk Score", "risk_score", ""),
        ("Risk Level", "risk_level", ""),
        ("Min Battery", "minimum_battery", "%"),
        ("Max Total Current", "maximum_total_current", " A"),
        ("Max Terrain Slope", "maximum_terrain_slope", " deg"),
        ("Min Signal", "minimum_signal_strength", "%"),
        ("Max Joint Temp", "maximum_joint_temperature", " C"),
        ("Event Count", "event_count", ""),
    ]

    columns = st.columns(4)
    for index, (label, key, suffix) in enumerate(labels):
        columns[index % 4].metric(label, _format_metric(cards.get(key), suffix))


def _show_overview(dashboard: dict[str, object]) -> None:
    mission_df = dashboard["mission_df"]
    cards = _as_dict(dashboard["metric_cards"])

    st.subheader("Mission Health")
    summary_columns = st.columns(4)
    summary_columns[0].metric("Risk Score", _format_metric(cards.get("risk_score")))
    summary_columns[1].metric("Risk Level", _format_metric(cards.get("risk_level")))
    summary_columns[2].metric("Mission Duration", _format_metric(_mission_duration(mission_df), " s"))
    summary_columns[3].metric("Event Count", _format_metric(cards.get("event_count")))

    condition_columns = st.columns(4)
    condition_columns[0].metric("Min Battery", _format_metric(cards.get("minimum_battery"), "%"))
    condition_columns[1].metric("Max Joint Temp", _format_metric(cards.get("maximum_joint_temperature"), " C"))
    condition_columns[2].metric("Max Terrain Slope", _format_metric(cards.get("maximum_terrain_slope"), " deg"))
    condition_columns[3].metric("Min Signal", _format_metric(cards.get("minimum_signal_strength"), "%"))

    st.caption(_mission_status_summary(dashboard))

    st.subheader("Risk Reasons")
    reasons = _risk_reasons(dashboard["risk_result"])
    if reasons:
        for reason in reasons:
            st.write(f"- {reason}")
    else:
        st.info("No explicit risk reasons were reported for this mission.")


def _show_mission_timeline(df: pd.DataFrame) -> None:
    timeline_columns = [
        column
        for column in ("mission_time_s", "waypoint", "robot_mode", "status", "event")
        if column in df.columns
    ]
    if not timeline_columns:
        st.info("No mission timeline columns are available in this export.")
        return

    timeline_df = df[timeline_columns]
    if "event" in timeline_df.columns:
        event_rows = timeline_df[timeline_df["event"].fillna("").astype(str).str.len() > 0]
        if not event_rows.empty:
            timeline_df = event_rows
    st.dataframe(timeline_df.head(25), use_container_width=True)


def _show_power_and_terrain(df: pd.DataFrame) -> None:
    st.subheader("Power")
    left, right = st.columns(2)
    with left:
        battery_column = _first_available(df, ["battery_percent", "battery_percentage"])
        if battery_column:
            _plot_line(df, battery_column, "Battery Over Mission Time", "Battery (%)")
        else:
            st.info("Battery telemetry is not available in this mission export.")
    with right:
        total_current_column = _first_available(df, ["total_current_a", "total_current"])
        if total_current_column:
            _plot_line(df, total_current_column, "Total Current Over Mission Time", "Current (A)")
        else:
            st.info("Total current telemetry is not available in this mission export.")

    st.subheader("Terrain and Link Quality")
    left, right = st.columns(2)
    with left:
        _plot_line(df, "terrain_slope_deg", "Terrain Slope Over Mission Time", "Slope (deg)")
    with right:
        _plot_line(df, "signal_strength_percent", "Signal Strength Over Mission Time", "Signal (%)")

    st.subheader("IMU Orientation")
    _plot_line(
        df,
        ["imu_roll_deg", "imu_pitch_deg", "imu_yaw_deg"],
        "IMU Roll, Pitch, and Yaw",
        "Angle (deg)",
    )


def _show_joint_telemetry(df: pd.DataFrame) -> None:
    with st.expander("Joint Temperature", expanded=True):
        _plot_line(df, get_joint_metric_columns("temp_c"), "Joint Temperature", "Temperature (C)")
    with st.expander("Joint Current", expanded=True):
        _plot_line(df, get_joint_metric_columns("current_a"), "Joint Current", "Current (A)")
    with st.expander("Joint Torque", expanded=True):
        _plot_line(df, get_joint_metric_columns("torque_nm"), "Joint Torque", "Torque (Nm)")


def _show_event_visuals(events_df: pd.DataFrame, event_summary_df: pd.DataFrame) -> None:
    st.subheader("Joint-Level Events")
    if events_df.empty:
        st.info("No joint-level events were detected.")
    else:
        if "severity" in events_df.columns:
            review_events = events_df[
                events_df["severity"].astype(str).str.lower().isin(["critical", "warning"])
            ]
            if not review_events.empty:
                st.warning(f"{len(review_events)} warning or critical event(s) require engineering review.")
        st.dataframe(events_df, use_container_width=True)

        if "severity" in events_df.columns:
            severity_counts = events_df["severity"].value_counts().reset_index()
            severity_counts.columns = ["severity", "count"]
            st.plotly_chart(
                px.bar(severity_counts, x="severity", y="count", title="Severity Counts"),
                use_container_width=True,
            )

        if "joint_label" in events_df.columns:
            joint_counts = events_df["joint_label"].value_counts().reset_index()
            joint_counts.columns = ["joint_label", "count"]
            st.plotly_chart(
                px.bar(joint_counts, x="joint_label", y="count", title="Event Count by Joint"),
                use_container_width=True,
            )

    st.subheader("Event Summary")
    if event_summary_df.empty:
        st.info("No event summary entries were produced.")
    else:
        st.dataframe(event_summary_df, use_container_width=True)


def _resolve_csv_input() -> Path:
    st.sidebar.header("Mission Source")
    uploaded_file = st.sidebar.file_uploader("Mission CSV", type=["csv"])
    if uploaded_file is None:
        st.sidebar.caption(f"Using sample file: {DEFAULT_CSV_PATH}")
        return DEFAULT_CSV_PATH

    with NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        return Path(temp_file.name)


def _show_sidebar_metadata(csv_path: Path, dashboard: dict[str, object]) -> None:
    mission_df = dashboard["mission_df"]
    cards = _as_dict(dashboard["metric_cards"])

    st.sidebar.header("Mission Metadata")
    st.sidebar.write(f"Source: `{csv_path.name}`")
    st.sidebar.write(f"Samples: `{len(mission_df)}`")
    st.sidebar.write(f"Duration: `{_format_metric(_mission_duration(mission_df), ' s')}`")
    st.sidebar.write(f"Risk: `{_format_metric(cards.get('risk_level'))}`")
    st.sidebar.write(f"Events: `{_format_metric(cards.get('event_count'))}`")


def _export_report_controls(csv_path: Path, key_prefix: str) -> None:
    if st.button("Export Markdown Report", key=f"{key_prefix}_export_report"):
        output_path = export_mission_report(csv_path)
        report_text = output_path.read_text(encoding="utf-8")
        st.session_state["latest_report_path"] = str(output_path)
        st.session_state["latest_report_text"] = report_text
        st.success(f"Report exported to {output_path}")

    report_path = st.session_state.get("latest_report_path")
    report_text = st.session_state.get("latest_report_text")
    if report_path:
        st.write(f"Latest report: `{report_path}`")
    if report_text:
        st.download_button(
            "Download Markdown Report",
            data=report_text,
            file_name=Path(str(report_path)).name,
            mime="text/markdown",
            key=f"{key_prefix}_download_report",
        )


def main() -> None:
    st.set_page_config(page_title="TerraPulse", layout="wide")
    st.title("TerraPulse")
    st.caption("Quadruped Mission Replay, Route Risk Scoring, and Field Incident Analysis")

    csv_path = _resolve_csv_input()
    if not csv_path.exists():
        st.error(f"Mission CSV not found: {csv_path}")
        return

    dashboard = prepare_dashboard_data(csv_path)
    mission_df = dashboard["mission_df"]
    _show_sidebar_metadata(csv_path, dashboard)

    _show_metric_cards(dashboard["metric_cards"])

    st.sidebar.header("Report Export")
    with st.sidebar:
        _export_report_controls(csv_path, "sidebar")

    overview_tab, replay_tab, power_tab, joint_tab, events_tab, report_tab = st.tabs(
        [
            "Overview",
            "Mission Replay",
            "Power & Terrain",
            "Joint Telemetry",
            "Events & Diagnostics",
            "Report Export",
        ]
    )

    with overview_tab:
        _show_overview(dashboard)

    with replay_tab:
        st.subheader("Route Replay")
        _plot_route(mission_df)
        st.subheader("Mission Timeline")
        _show_mission_timeline(mission_df)

    with power_tab:
        _show_power_and_terrain(mission_df)

    with joint_tab:
        _show_joint_telemetry(mission_df)

    with events_tab:
        _show_event_visuals(dashboard["events_df"], dashboard["event_summary_df"])

    with report_tab:
        st.subheader("Markdown Mission Report")
        st.caption("Exports use the existing TerraPulse report pipeline.")
        _export_report_controls(csv_path, "main")


if __name__ == "__main__":
    main()

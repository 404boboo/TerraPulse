from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import plotly.express as px
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


def _first_available(df: pd.DataFrame, columns: list[str]) -> str | None:
    for column in columns:
        if column in df.columns:
            return column
    return None


def _plot_line(df: pd.DataFrame, y: str | list[str], title: str, y_label: str) -> None:
    if "mission_time_s" not in df.columns:
        st.info(f"{title} requires mission_time_s telemetry.")
        return

    required = [y] if isinstance(y, str) else y
    available = [column for column in required if column in df.columns]
    if not available:
        st.info(f"{title} telemetry is not available in this mission export.")
        return

    fig = px.line(df, x="mission_time_s", y=available, title=title, labels={"value": y_label})
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


def _show_event_visuals(events_df: pd.DataFrame, event_summary_df: pd.DataFrame) -> None:
    st.subheader("Joint-Level Events")
    if events_df.empty:
        st.info("No joint-level events were detected.")
    else:
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
    uploaded_file = st.sidebar.file_uploader("Mission CSV", type=["csv"])
    if uploaded_file is None:
        return DEFAULT_CSV_PATH

    with NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        return Path(temp_file.name)


def main() -> None:
    st.set_page_config(page_title="TerraPulse", layout="wide")
    st.title("TerraPulse")
    st.caption("Robot Mission Replay, Route Risk Scoring, and Field Incident Analysis")

    csv_path = _resolve_csv_input()
    if not csv_path.exists():
        st.error(f"Mission CSV not found: {csv_path}")
        return

    dashboard = prepare_dashboard_data(csv_path)
    mission_df = dashboard["mission_df"]

    _show_metric_cards(dashboard["metric_cards"])

    st.divider()
    _plot_route(mission_df)

    left, right = st.columns(2)
    with left:
        battery_column = _first_available(mission_df, ["battery_percent", "battery_percentage"])
        if battery_column:
            _plot_line(mission_df, battery_column, "Battery Over Mission Time", "Battery (%)")
        else:
            st.info("Battery telemetry is not available in this mission export.")
        _plot_line(mission_df, "terrain_slope_deg", "Terrain Slope Over Mission Time", "Slope (deg)")
    with right:
        total_current_column = _first_available(mission_df, ["total_current_a", "total_current"])
        if total_current_column:
            _plot_line(mission_df, total_current_column, "Total Current Over Mission Time", "Current (A)")
        else:
            st.info("Total current telemetry is not available in this mission export.")
        _plot_line(mission_df, "signal_strength_percent", "Signal Strength Over Mission Time", "Signal (%)")

    _plot_line(
        mission_df,
        ["imu_roll_deg", "imu_pitch_deg", "imu_yaw_deg"],
        "IMU Roll, Pitch, and Yaw",
        "Angle (deg)",
    )
    _plot_line(
        mission_df,
        get_joint_metric_columns("temp_c"),
        "Joint Temperature",
        "Temperature (C)",
    )
    _plot_line(
        mission_df,
        get_joint_metric_columns("current_a"),
        "Joint Current",
        "Current (A)",
    )
    _plot_line(
        mission_df,
        get_joint_metric_columns("torque_nm"),
        "Joint Torque",
        "Torque (Nm)",
    )

    st.divider()
    _show_event_visuals(dashboard["events_df"], dashboard["event_summary_df"])

    st.divider()
    if st.button("Export Markdown Report"):
        output_path = export_mission_report(csv_path)
        report_text = output_path.read_text(encoding="utf-8")
        st.success(f"Report exported to {output_path}")
        st.download_button(
            "Download Markdown Report",
            data=report_text,
            file_name=output_path.name,
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()

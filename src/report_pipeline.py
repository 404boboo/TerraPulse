from __future__ import annotations

from pathlib import Path

from src.event_analyzer import analyze_joint_events, summarize_events
from src.mission_loader import load_mission_log
from src.report_generator import generate_markdown_report
from src.risk_scorer import calculate_risk_score


def ensure_reports_dir(output_dir: Path | str) -> Path:
    reports_dir = Path(output_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def build_report_from_csv(csv_path: Path | str) -> str:
    csv_file = Path(csv_path)

    mission_df = load_mission_log(csv_file)
    risk_result = calculate_risk_score(mission_df)
    events = analyze_joint_events(mission_df)
    event_summary = summarize_events(events)

    return generate_markdown_report(
        mission_df,
        risk_result,
        events,
        event_summary,
    )


def save_report(report_text: str, output_path: Path | str) -> Path:
    report_file = Path(output_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_text, encoding="utf-8")
    return report_file


def export_mission_report(
    csv_path: Path | str,
    output_dir: Path | str = "reports",
    output_filename: str | None = None,
) -> Path:
    csv_file = Path(csv_path)

    if not csv_file.exists():
        raise FileNotFoundError(csv_file)

    reports_dir = ensure_reports_dir(output_dir)
    filename = output_filename or f"{csv_file.stem}_report.md"
    output_path = reports_dir / filename

    report_text = build_report_from_csv(csv_file)

    return save_report(report_text, output_path)
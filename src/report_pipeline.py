from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from src import event_analyzer, mission_loader, risk_scorer
from src import report_generator


_MISSION_LOADER_CANDIDATES = (
    "load_mission_data",
    "load_mission_csv",
    "load_mission",
    "load_csv",
)
_RISK_SCORER_CANDIDATES = (
    "calculate_route_risk",
    "score_route_risk",
    "calculate_risk",
    "score_risk",
)
_EVENT_ANALYZER_CANDIDATES = (
    "analyze_events",
    "detect_joint_events",
    "detect_events",
    "find_events",
)
_EVENT_SUMMARY_CANDIDATES = (
    "summarize_events",
    "summarize_event_counts",
    "summarize_event_summary",
    "build_event_summary",
)
_REPORT_GENERATOR_CANDIDATES = (
    "generate_markdown_report",
    "build_markdown_report",
    "create_markdown_report",
)


def _resolve_callable(module: Any, candidates: tuple[str, ...]) -> Callable[..., Any]:
    for name in candidates:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate
    raise AttributeError(
        f"Could not find a callable on {module.__name__} matching any of: {', '.join(candidates)}"
    )


def ensure_reports_dir(output_dir: Path | str) -> Path:
    reports_dir = Path(output_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def build_report_from_csv(csv_path: Path | str) -> str:
    csv_file = Path(csv_path)
    load_mission = _resolve_callable(mission_loader, _MISSION_LOADER_CANDIDATES)
    score_risk = _resolve_callable(risk_scorer, _RISK_SCORER_CANDIDATES)
    analyze_events = _resolve_callable(event_analyzer, _EVENT_ANALYZER_CANDIDATES)
    summarize_events = _resolve_callable(event_analyzer, _EVENT_SUMMARY_CANDIDATES)
    generate_report = _resolve_callable(report_generator, _REPORT_GENERATOR_CANDIDATES)

    mission_df = load_mission(csv_file)
    risk_result = score_risk(mission_df)
    events = analyze_events(mission_df)
    event_summary = summarize_events(events)
    return generate_report(mission_df, risk_result, events, event_summary)


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

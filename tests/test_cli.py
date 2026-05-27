from pathlib import Path

from src.cli import main


SAMPLE_CSV_PATH = Path(__file__).parent.parent / "data" / "Sample_mission_log.csv"


def test_cli_exports_report_successfully(tmp_path):
    exit_code = main([
        str(SAMPLE_CSV_PATH),
        "--output-dir",
        str(tmp_path),
    ])

    expected_report = tmp_path / "Sample_mission_log_report.md"

    assert exit_code == 0
    assert expected_report.exists()


def test_cli_supports_custom_output_filename(tmp_path):
    exit_code = main([
        str(SAMPLE_CSV_PATH),
        "--output-dir",
        str(tmp_path),
        "--output-name",
        "custom_report.md",
    ])

    expected_report = tmp_path / "custom_report.md"

    assert exit_code == 0
    assert expected_report.exists()


def test_cli_generated_report_contains_expected_content(tmp_path):
    exit_code = main([
        str(SAMPLE_CSV_PATH),
        "--output-dir",
        str(tmp_path),
    ])

    expected_report = tmp_path / "Sample_mission_log_report.md"
    report_text = expected_report.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "TerraPulse Mission Report" in report_text
    assert "Risk" in report_text


def test_cli_prints_success_message(tmp_path, capsys):
    exit_code = main([
        str(SAMPLE_CSV_PATH),
        "--output-dir",
        str(tmp_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Report successfully generated" in captured.out
    assert "Report Path:" in captured.out


def test_cli_returns_error_for_missing_csv(tmp_path, capsys):
    missing_csv = tmp_path / "missing.csv"

    exit_code = main([
        str(missing_csv),
        "--output-dir",
        str(tmp_path),
    ])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.out
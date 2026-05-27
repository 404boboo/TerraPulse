import argparse
from pathlib import Path
from src.report_pipeline import export_mission_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="terrapulse",
        description="Export TerraPulse mission analysis reports from CSV telemetry.",
    )

    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to the exported mission CSV file.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Directory where the generated Markdown report should be saved.",
    )

    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Optional custom Markdown report filename.",
    )


    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report_path = export_mission_report(
            csv_path=args.csv_path,
            output_dir=args.output_dir,
            output_filename=args.output_name,
        )
    except FileNotFoundError as error:
        print(f"Error: {error}")
        return 1
    except Exception as error:
        print(f"An unexpected error occurred: {error}")
        return 1
    
    print(f"Report successfully generated")
    print(f"Mission CSV: {args.csv_path}")
    print(f"Report Path: {report_path}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())



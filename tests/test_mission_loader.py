from pathlib import Path

import pandas as pd
import pytest

from src.mission_loader import JOINTS, get_joint_columns, load_mission_log


SAMPLE_CSV_PATH = Path(__file__).parent.parent / "data" / "Sample_mission_log.csv"


def test_load_mission_log_returns_dataframe():
    cleaned_df = load_mission_log(SAMPLE_CSV_PATH)

    assert isinstance(cleaned_df, pd.DataFrame)
    assert not cleaned_df.empty


def test_load_mission_log_sorts_mission_time():
    cleaned_df = load_mission_log(SAMPLE_CSV_PATH)

    assert cleaned_df["mission_time_s"].is_monotonic_increasing


def test_load_mission_log_12_joints():
    assert len(JOINTS) == 12


def test_load_mission_log_joint_metric_cols():
    cleaned_df = load_mission_log(SAMPLE_CSV_PATH)

    for metric in ["temp_c", "torque_nm", "current_a"]:
        for column in get_joint_columns(metric):
            assert column in cleaned_df.columns


def test_load_mission_log_raises_file_not_found():
    missing_path = Path(__file__).parent.parent / "data" / "missing_file.csv"

    with pytest.raises(FileNotFoundError):
        load_mission_log(missing_path)
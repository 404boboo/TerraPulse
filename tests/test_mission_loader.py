from pathlib import Path
import pandas as pd
import pytest
from src.mission_loader import load_mission_log

@pytest.fixture
def sample_mission_data():
    csv_path = Path(__file__).parent.parent / "data" / "Sample_mission_log.csv"
    return load_mission_log(csv_path)


def test_load_mission_log_returns_dataframe(sample_mission_data):
    assert isinstance(sample_mission_data, pd.DataFrame)
    assert not sample_mission_data.empty


def test_load_mission_log_sorts_by_mission_time(sample_mission_data):
    assert sample_mission_data["mission_time_s"].is_monotonic_increasing


def test_load_mission_log_raises_file_not_found():
    missing_path = Path(__file__).parent.parent / "data" / "missing_file.csv"
    
    with pytest.raises(FileNotFoundError):
        load_mission_log(missing_path)
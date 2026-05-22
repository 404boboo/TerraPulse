from pathlib import Path
import pandas as pd



REQUIRED_COLUMNS = {
    "timestamp",
    "mission_time_s",
    "x_m",
    "y_m",
    "z_m",
    "waypoint",
    "robot_mode",
    "battery_percent",
    "pack_voltage_v",
    "total_current_a",
    "avg_motor_temp_c",
    "max_motor_temp_c",
    "front_left_contact",
    "front_right_contact",
    "rear_left_contact",
    "rear_right_contact",
    "slope_deg",
    "roll_deg",
    "pitch_deg",
    "signal_strength_percent",
    "status",
    "event",
}

NUMERIC_COLUMNS = [
    "mission_time_s",
    "x_m",
    "y_m",
    "z_m",
    "battery_percent",
    "pack_voltage_v",
    "total_current_a",
    "avg_motor_temp_c",
    "max_motor_temp_c",
    "front_left_contact",
    "front_right_contact",
    "rear_left_contact",
    "rear_right_contact",
    "slope_deg",
    "roll_deg",
    "pitch_deg",
    "signal_strength_percent",
]

def validate_mission_data(df: pd.DataFrame) -> None:
    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

def clean_mission_log(df: pd.DataFrame) -> pd.DataFrame:
    validate_mission_data(df)

    cleaned_df = df.copy()

    for col in NUMERIC_COLUMNS:
        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="raise")
    # Sort by mission time and reset indx
    cleaned_df = cleaned_df.sort_values("mission_time_s").reset_index(drop=True)
    return cleaned_df

def load_mission_log(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Mission log file not found: {file_path}")
    
    df = pd.read_csv(path)
    return clean_mission_log(df)


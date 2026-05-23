from pathlib import Path

import pandas as pd


JOINTS = [
    "fl_hip",
    "fl_thigh",
    "fl_calf",
    "fr_hip",
    "fr_thigh",
    "fr_calf",
    "rl_hip",
    "rl_thigh",
    "rl_calf",
    "rr_hip",
    "rr_thigh",
    "rr_calf",
]

BASE_REQUIRED_COLUMNS = {
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
    "imu_roll_deg",
    "imu_pitch_deg",
    "imu_yaw_deg",
    "fl_contact",
    "fr_contact",
    "rl_contact",
    "rr_contact",
    "terrain_slope_deg",
    "signal_strength_percent",
    "status",
    "event",
}

JOINT_REQUIRED_COLUMNS = {
    f"{joint}_{metric}"
    for joint in JOINTS
    for metric in ["temp_c", "torque_nm", "current_a"]
}

REQUIRED_COLUMNS = BASE_REQUIRED_COLUMNS | JOINT_REQUIRED_COLUMNS

NUMERIC_COLUMNS = [
    "mission_time_s",
    "x_m",
    "y_m",
    "z_m",
    "battery_percent",
    "pack_voltage_v",
    "total_current_a",
    "imu_roll_deg",
    "imu_pitch_deg",
    "imu_yaw_deg",
    "fl_contact",
    "fr_contact",
    "rl_contact",
    "rr_contact",
    "terrain_slope_deg",
    "signal_strength_percent",
    *JOINT_REQUIRED_COLUMNS,
]


def validate_mission_data(df: pd.DataFrame) -> None:
    missing_cols = REQUIRED_COLUMNS - set(df.columns)

    if missing_cols:
        missing = ", ".join(sorted(missing_cols))
        raise ValueError(f"Mission log is missing required columns: {missing}")


def clean_mission_log(df: pd.DataFrame) -> pd.DataFrame:
    validate_mission_data(df)

    cleaned_df = df.copy()

    for column in NUMERIC_COLUMNS:
        cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors="raise")

    cleaned_df = cleaned_df.sort_values("mission_time_s").reset_index(drop=True)

    return cleaned_df


def load_mission_log(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Mission log does not exist: {path}")

    df = pd.read_csv(path)
    return clean_mission_log(df)


def get_joint_cols(metric: str) -> list[str]:
    return [f"{joint}_{metric}" for joint in JOINTS]
import pandas as pd
from src.mission_loader import get_joint_cols


def get_risk_level(score: int) -> str:
    if score <= 30:
        return "Low"
    elif score <= 60:
        return "Medium"
    elif score <= 80:
        return "High"
    return "Critical"


def get_max_joint_value(df: pd.DataFrame, metric: str) -> float:
    cols = get_joint_cols(metric)
    return float(df[cols].max().max())


# This function detects if the robot is physically stalled.
# Compares X and Y coordinates then check if robot is actively suppoted to be moving
# If it find a match it increments same_position_counter, if it hits the threshold(defualts to 3 rows in a row), it returns True
def detect_stalled_robot(df: pd.DataFrame, repeated_points_threshold: int = 3) -> bool:
    same_position_counter = 1

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        current = df.iloc[i]

        same_x = current["x_m"] == prev["x_m"]
        same_y = current["y_m"] == prev["y_m"]
        robot_moving = current["robot_mode"] in {"WALKING", "INSPECTING", "RETURNING"}

        if same_x and same_y and robot_moving:
            same_position_counter += 1

            if same_position_counter >= repeated_points_threshold:
                return True
        else:
            same_position_counter = 1

    return False

def get_risk_reasons(df: pd.DataFrame) -> list[str]:
    reasons = []

    max_joint_temp = get_max_joint_value(df, "temp_c")
    max_joint_torque = get_max_joint_value(df, "torque_nm")
    max_joint_current = get_max_joint_value(df, "current_a")

    if df["battery_percent"].min() < 30:
        reasons.append("Battery dropped below 30%")
    if df["battery_percent"].min() < 20:
        reasons.append("Battery dropped below 20%")
    if max_joint_temp > 80:
        reasons.append(f"At least one joint exceeded 80°C (max: {max_joint_temp:.1f}°C)")
    if max_joint_temp > 90:
        reasons.append(f"At least one joint exceeded 90°C (max: {max_joint_temp:.1f}°C)")

    if max_joint_current > 5:
        reasons.append(f"At least one joint exceeded 10 A current (max: {max_joint_current:.1f} A)")
    if max_joint_torque > 35:
        reasons.append(f"At least one joint exceeded 35 Nm torque (max: {max_joint_torque:.1f} Nm)")
    
    if df["total_current_a"].max() > 25:
        reasons.append(f"Total current exceeded 25 A (max: {df['total_current_a'].max():.1f} A)")
    if df["terrain_slope_deg"].max() > 15:
        reasons.append("Terrain slope exceeded 15°")

    if df["signal_strength_percent"].min() < 70:
        reasons.append("Signal strength dropped below 70%")

    if df["signal_strength_percent"].min() < 50:
        reasons.append("Signal strength dropped below 50%")

    if detect_stalled_robot(df):
        reasons.append("Possible stuck robot detected")

    if (df["status"] == "CRITICAL").any():
        reasons.append("Critical mission status occurred")

    return reasons

def calculate_risk_score(df: pd.DataFrame) -> dict:
    score = 0

    max_joint_temp = get_max_joint_value(df, "temp_c")
    max_joint_torque = get_max_joint_value(df, "torque_nm")
    max_joint_current = get_max_joint_value(df, "current_a")


    if df["battery_percent"].min() < 30:
        score += 25
    
    if df["battery_percent"].min() < 20:
        score += 15

    if max_joint_temp > 80:
        score += 15
    
    if max_joint_temp > 90:
        score += 20

    if max_joint_current > 5:
        score += 10

    if max_joint_torque > 35:
        score += 10

    if df["total_current_a"].max() > 25:
        score += 15
    
    if df["terrain_slope_deg"].max() > 15:
        score += 15

    if df["signal_strength_percent"].min() < 70:
        score += 10
    
    if df["signal_strength_percent"].min() < 50:
        score += 15

    if detect_stalled_robot(df):
        score += 30

    if (df["status"] == "CRITICAL").any():
        score += 20

    score = min(score, 100)

    return {
        "score": score,
        "level": get_risk_level(score),
        "reasons": get_risk_reasons(df),
        "metrics": {
            "max_joint_temp_c": max_joint_temp,
            "max_joint_current_a": max_joint_current,
            "max_joint_torque_nm": max_joint_torque,
            "min_battery_percent": float(df["battery_percent"].min()),
            "max_total_current_a": float(df["total_current_a"].max()),
            "max_terrain_slope_deg": float(df["terrain_slope_deg"].max()),
            "min_signal_strength_percent": float(df["signal_strength_percent"].min()),
        },
    }

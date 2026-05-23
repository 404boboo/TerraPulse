import pandas as pd

from src.mission_loader import JOINTS
from src.risk_scorer import calculate_risk_score, detect_stalled_robot, get_risk_level


def build_test_df(**overrides):
    base = {
        "battery_percent": [100, 90, 80],
        "total_current_a": [5, 8, 10],
        "terrain_slope_deg": [0, 5, 8],
        "signal_strength_percent": [100, 95, 90],
        "x_m": [0, 1, 2],
        "y_m": [0, 1, 2],
        "robot_mode": ["IDLE", "WALKING", "WALKING"],
        "status": ["OK", "OK", "OK"],
        }
    
    for joint in JOINTS:
        base[f"{joint}_temp_c"] = [40, 50, 60]
        base[f"{joint}_current_a"] = [0.6, 0.8, 1.0]
        base[f"{joint}_torque_nm"] = [2.0, 5.0, 10.0]

    base.update(overrides)
    return pd.DataFrame(base)

def test_get_risk_level():
    assert get_risk_level(0) == "Low"
    assert get_risk_level(30) == "Low"
    assert get_risk_level(31) == "Medium"
    assert get_risk_level(60) == "Medium"
    assert get_risk_level(61) == "High"
    assert get_risk_level(80) == "High"
    assert get_risk_level(81) == "Critical"

def test_calculate_risk_score_low():
    df = build_test_df()
    result = calculate_risk_score(df)

    assert result["score"] == 0
    assert result["level"] == "Low"
    assert result["reasons"] == []
    assert result["metrics"]["max_joint_temp_c"] == 60

def test_calculate_risk_score_high():
    df = build_test_df(
        battery_percent=[100, 18, 12],
        total_current_a=[10, 28, 31],
        terrain_slope_deg=[0, 18, 22],
        signal_strength_percent=[100, 65, 45],
        x_m=[1, 1, 1],
        y_m=[1, 1, 1],
        robot_mode=["WALKING", "WALKING", "WALKING"],
        status=["OK", "WARNING", "CRITICAL"],
        rl_calf_temp_c=[70, 92, 95],
        rl_calf_current_a=[2.0, 5.5, 6.0],
        rl_calf_torque_nm=[20.0, 36.0, 38.0],
    )
    result = calculate_risk_score(df)

    assert result["score"] == 100
    assert result["level"] == "Critical"
    assert result["metrics"]["max_joint_temp_c"] == 95
    assert result["metrics"]["max_joint_current_a"] == 6.0
    assert result["metrics"]["max_joint_torque_nm"] == 38.0
    assert "Possible stuck robot detected" in result["reasons"]
    assert "At least one joint exceeded 90°C (max: 95.0°C)" in result["reasons"]


def test_detect_stuck_robot_returns_true_for_repeated_active_position():
    df = pd.DataFrame({
        "x_m": [2, 2, 2],
        "y_m": [3, 3, 3],
        "robot_mode": ["WALKING", "WALKING", "WALKING"],
    })

    assert detect_stalled_robot(df) is True


def test_detect_stuck_robot_returns_false_when_robot_moves():
    df = pd.DataFrame({
        "x_m": [0, 1, 2],
        "y_m": [0, 1, 2],
        "robot_mode": ["WALKING", "WALKING", "WALKING"],
    })

    assert detect_stalled_robot(df) is False

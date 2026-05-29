from __future__ import annotations

import pytest

from src.robot_profiles import (
    RobotProfile,
    get_robot_profile,
    list_robot_profile_keys,
    robot_profile_exists,
)


def test_quadruped_profile_exists() -> None:
    assert robot_profile_exists("quadruped")


def test_mobile_robot_profile_exists() -> None:
    assert robot_profile_exists("mobile_robot")


def test_manipulator_profile_exists() -> None:
    assert robot_profile_exists("manipulator")


def test_generic_robot_profile_exists() -> None:
    assert robot_profile_exists("generic_robot")


def test_list_robot_profile_keys_returns_all_expected_keys() -> None:
    assert set(list_robot_profile_keys()) == {
        "quadruped",
        "mobile_robot",
        "manipulator",
        "generic_robot",
    }


def test_get_robot_profile_returns_robot_profile() -> None:
    profile = get_robot_profile("quadruped")

    assert isinstance(profile, RobotProfile)
    assert profile.key == "quadruped"


def test_unknown_profile_raises_value_error_with_valid_keys() -> None:
    with pytest.raises(ValueError, match="Valid profiles"):
        get_robot_profile("humanoid")


def test_quadruped_profile_includes_expected_diagnostic_categories() -> None:
    profile = get_robot_profile("quadruped")

    assert "thermal" in profile.diagnostic_categories
    assert "current" in profile.diagnostic_categories
    assert "torque" in profile.diagnostic_categories
    assert "mission_risk" in profile.diagnostic_categories


def test_quadruped_profile_includes_expected_component_groups() -> None:
    profile = get_robot_profile("quadruped")

    assert "front_left_leg" in profile.component_groups
    assert "front_right_leg" in profile.component_groups
    assert "rear_left_leg" in profile.component_groups
    assert "rear_right_leg" in profile.component_groups
    assert "power_system" in profile.component_groups
    assert profile.component_groups["front_left_leg"] == ("fl_hip", "fl_thigh", "fl_calf")


def test_manipulator_profile_includes_motion_diagnostics() -> None:
    profile = get_robot_profile("manipulator")

    assert (
        "position_error" in profile.diagnostic_categories
        or "motion_tracking" in profile.diagnostic_categories
    )


def test_generic_profile_can_be_used_as_fallback() -> None:
    profile = get_robot_profile("generic_robot")

    assert profile.robot_type == "generic_robot"
    assert "mission_risk" in profile.diagnostic_categories
    assert "mission_state" in profile.component_groups
